"""Dashboard aggregation service using PostgreSQL with CSV fallback."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pandas as pd
from sqlalchemy import distinct, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..schemas.db_models import Order, OrderItem
from .dashboard_dataset import dashboard_dataset_repository


class DashboardService:
    """Computes dashboard data on the backend so the frontend stays simple."""

    def __init__(self) -> None:
        self._dataset: pd.DataFrame | None = None

    async def summary(self, db: AsyncSession | None, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        if db is not None and await self._postgres_has_orders(db):
            return await self._postgres_summary(db, filters)

        frame = self._filtered_dataset(filters)
        if frame.empty:
            return self._empty_summary()
        return {
            "source": "csv",
            "total_orders": int(frame["Order Id"].nunique()),
            "total_rows": int(len(frame)),
            "total_sales": round(float(frame["Sales"].sum()), 2),
            "total_profit": round(float(frame["Order Profit Per Order"].sum()), 2),
            "late_rate": round(float(frame["Late_delivery_risk"].mean()), 4),
            "avg_shipping_delay": round(
                float((frame["Days for shipping (real)"] - frame["Days for shipment (scheduled)"]).mean()),
                2,
            ),
            "high_risk_shipments": int(frame["Late_delivery_risk"].sum()),
            "avg_discount_rate": round(float(frame["Order Item Discount Rate"].mean()), 4),
            "total_categories": int(frame["Category Name"].nunique()),
            "total_markets": int(frame["Market"].nunique()),
        }

    async def filters(self, db: AsyncSession | None) -> dict[str, Any]:
        if db is not None and await self._postgres_has_orders(db):
            return {
                "markets": await self._postgres_distinct(db, Order.market),
                "order_regions": await self._postgres_distinct(db, Order.order_region),
                "order_countries": await self._postgres_distinct(db, Order.order_country),
                "shipping_modes": await self._postgres_distinct(db, Order.shipping_mode),
                "categories": await self._postgres_distinct(db, Order.category_name),
                "departments": await self._postgres_distinct(db, Order.department_name),
                "segments": await self._postgres_distinct(db, Order.customer_segment),
                "statuses": await self._postgres_distinct(db, Order.order_status),
                "risk_levels": ["On Time", "Late"],
                "date_range": await self._postgres_date_range(db),
            }

        frame = self._load_dataset()
        if frame.empty:
            return {
                "markets": [],
                "order_regions": [],
                "order_countries": [],
                "shipping_modes": [],
                "categories": [],
                "departments": [],
                "segments": [],
                "statuses": [],
                "risk_levels": [],
                "date_range": {},
            }
        return {
            "markets": self._unique_values(frame, "Market"),
            "order_regions": self._unique_values(frame, "Order Region"),
            "order_countries": self._unique_values(frame, "Order Country"),
            "shipping_modes": self._unique_values(frame, "Shipping Mode"),
            "categories": self._unique_values(frame, "Category Name"),
            "departments": self._unique_values(frame, "Department Name"),
            "segments": self._unique_values(frame, "Customer Segment"),
            "statuses": self._unique_values(frame, "Order Status"),
            "risk_levels": ["On Time", "Late"],
            "date_range": self._csv_date_range(frame),
        }

    async def risk_by_market(self, db: AsyncSession | None, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if db is not None and await self._postgres_has_orders(db):
            return await self._postgres_risk_by_market(db, filters)

        frame = self._filtered_dataset(filters)
        if frame.empty:
            return []
        grouped = frame.groupby("Market", dropna=False).agg(
            total_orders=("Order Id", "nunique"),
            late_orders=("Late_delivery_risk", "sum"),
            late_rate=("Late_delivery_risk", "mean"),
        )
        return [
            {
                "market": str(index),
                "total_orders": int(row["total_orders"]),
                "late_orders": int(row["late_orders"]),
                "late_rate": round(float(row["late_rate"]), 4),
            }
            for index, row in grouped.sort_values("late_rate", ascending=False).iterrows()
        ]

    async def sales_by_category(
        self,
        db: AsyncSession | None,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if db is not None and await self._postgres_has_orders(db):
            return await self._postgres_sales_by_category(db, limit, filters)

        frame = self._filtered_dataset(filters)
        if frame.empty:
            return []
        grouped = frame.groupby("Category Name", dropna=False).agg(
            total_sales=("Sales", "sum"),
            order_count=("Order Id", "nunique"),
        )
        grouped = grouped.sort_values("total_sales", ascending=False).head(limit)
        return [
            {
                "category_name": str(index),
                "total_sales": round(float(row["total_sales"]), 2),
                "order_count": int(row["order_count"]),
            }
            for index, row in grouped.iterrows()
        ]

    async def shipping_performance(
        self,
        db: AsyncSession | None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if db is not None and await self._postgres_has_orders(db):
            return await self._postgres_shipping_performance(db, filters)

        frame = self._filtered_dataset(filters)
        if frame.empty:
            return []
        grouped = frame.groupby("Shipping Mode", dropna=False).agg(
            order_count=("Order Id", "nunique"),
            late_rate=("Late_delivery_risk", "mean"),
            avg_shipping_days=("Days for shipping (real)", "mean"),
            avg_scheduled_days=("Days for shipment (scheduled)", "mean"),
        )
        return [
            {
                "shipping_mode": str(index),
                "order_count": int(row["order_count"]),
                "late_rate": round(float(row["late_rate"]), 4),
                "avg_shipping_days": round(float(row["avg_shipping_days"]), 2),
                "avg_scheduled_days": round(float(row["avg_scheduled_days"]), 2),
            }
            for index, row in grouped.sort_values("order_count", ascending=False).iterrows()
        ]

    async def _postgres_summary(self, db: AsyncSession, filters: dict[str, Any] | None) -> dict[str, Any]:
        try:
            statement = self._apply_postgres_filters(
                select(
                    func.count(Order.id).label("total_rows"),
                    func.count(distinct(Order.order_id)).label("total_orders"),
                    func.coalesce(func.sum(Order.sales_per_customer), 0).label("total_sales"),
                    func.coalesce(func.sum(Order.order_profit_per_order), 0).label("total_profit"),
                    func.coalesce(func.avg(Order.late_delivery_risk), 0).label("late_rate"),
                    func.coalesce(
                        func.avg(Order.days_for_shipping_real - Order.days_for_shipment_scheduled),
                        0,
                    ).label("avg_shipping_delay"),
                    func.coalesce(func.sum(Order.late_delivery_risk), 0).label("high_risk_shipments"),
                    func.count(distinct(Order.category_name)).label("total_categories"),
                    func.count(distinct(Order.market)).label("total_markets"),
                ),
                filters,
            )
            result = await db.execute(statement)
            row = result.one()
            discount_statement = self._apply_postgres_filters(
                select(func.coalesce(func.avg(OrderItem.order_item_discount_rate), 0))
                .select_from(OrderItem)
                .join(Order, Order.order_id == OrderItem.order_id),
                filters,
            )
            avg_discount_rate = await db.scalar(discount_statement)
        except SQLAlchemyError:
            return self._empty_summary()

        return {
            "source": "postgresql",
            "total_orders": int(row.total_orders or 0),
            "total_rows": int(row.total_rows or 0),
            "total_sales": round(float(row.total_sales or 0), 2),
            "total_profit": round(float(row.total_profit or 0), 2),
            "late_rate": round(float(row.late_rate or 0), 4),
            "avg_shipping_delay": round(float(row.avg_shipping_delay or 0), 2),
            "high_risk_shipments": int(row.high_risk_shipments or 0),
            "avg_discount_rate": round(float(avg_discount_rate or 0), 4),
            "total_categories": int(row.total_categories or 0),
            "total_markets": int(row.total_markets or 0),
        }

    async def _postgres_has_orders(self, db: AsyncSession) -> bool:
        try:
            count = await db.scalar(select(func.count(Order.id)))
        except SQLAlchemyError:
            return False
        return bool(count)

    async def _postgres_distinct(self, db: AsyncSession, column: Any, limit: int = 250) -> list[str]:
        try:
            result = await db.execute(
                select(distinct(column))
                .where(column.is_not(None))
                .order_by(column)
                .limit(limit)
            )
        except SQLAlchemyError:
            return []
        return [str(value) for value in result.scalars().all() if value not in (None, "")]

    async def _postgres_date_range(self, db: AsyncSession) -> dict[str, str | None]:
        try:
            result = await db.execute(select(func.min(Order.order_date), func.max(Order.order_date)))
        except SQLAlchemyError:
            return {"start": None, "end": None}
        start, end = result.one()
        return {
            "start": start.date().isoformat() if start else None,
            "end": end.date().isoformat() if end else None,
        }

    async def _postgres_risk_by_market(
        self,
        db: AsyncSession,
        filters: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        try:
            statement = self._apply_postgres_filters(
                select(
                    Order.market,
                    func.count(distinct(Order.order_id)).label("total_orders"),
                    func.coalesce(func.sum(Order.late_delivery_risk), 0).label("late_orders"),
                    func.coalesce(func.avg(Order.late_delivery_risk), 0).label("late_rate"),
                )
                .group_by(Order.market)
                .order_by(func.coalesce(func.avg(Order.late_delivery_risk), 0).desc()),
                filters,
            )
            result = await db.execute(statement)
        except SQLAlchemyError:
            return []
        return [
            {
                "market": row.market or "Unknown",
                "total_orders": int(row.total_orders or 0),
                "late_orders": int(row.late_orders or 0),
                "late_rate": round(float(row.late_rate or 0), 4),
            }
            for row in result.all()
        ]

    async def _postgres_sales_by_category(
        self,
        db: AsyncSession,
        limit: int,
        filters: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        try:
            statement = self._apply_postgres_filters(
                select(
                    Order.category_name,
                    func.coalesce(func.sum(Order.sales_per_customer), 0).label("total_sales"),
                    func.count(distinct(Order.order_id)).label("order_count"),
                )
                .group_by(Order.category_name)
                .order_by(func.coalesce(func.sum(Order.sales_per_customer), 0).desc())
                .limit(limit),
                filters,
            )
            result = await db.execute(statement)
        except SQLAlchemyError:
            return []
        return [
            {
                "category_name": row.category_name or "Unknown",
                "total_sales": round(float(row.total_sales or 0), 2),
                "order_count": int(row.order_count or 0),
            }
            for row in result.all()
        ]

    async def _postgres_shipping_performance(
        self,
        db: AsyncSession,
        filters: dict[str, Any] | None,
    ) -> list[dict[str, Any]]:
        try:
            statement = self._apply_postgres_filters(
                select(
                    Order.shipping_mode,
                    func.count(distinct(Order.order_id)).label("order_count"),
                    func.coalesce(func.avg(Order.late_delivery_risk), 0).label("late_rate"),
                    func.coalesce(func.avg(Order.days_for_shipping_real), 0).label("avg_shipping_days"),
                    func.coalesce(func.avg(Order.days_for_shipment_scheduled), 0).label("avg_scheduled_days"),
                )
                .group_by(Order.shipping_mode)
                .order_by(func.count(distinct(Order.order_id)).desc()),
                filters,
            )
            result = await db.execute(statement)
        except SQLAlchemyError:
            return []
        return [
            {
                "shipping_mode": row.shipping_mode or "Unknown",
                "order_count": int(row.order_count or 0),
                "late_rate": round(float(row.late_rate or 0), 4),
                "avg_shipping_days": round(float(row.avg_shipping_days or 0), 2),
                "avg_scheduled_days": round(float(row.avg_scheduled_days or 0), 2),
            }
            for row in result.all()
        ]

    def _apply_postgres_filters(self, statement: Any, filters: dict[str, Any] | None) -> Any:
        filters = filters or {}
        mapping = {
            "market": Order.market,
            "order_region": Order.order_region,
            "order_country": Order.order_country,
            "shipping_mode": Order.shipping_mode,
            "category": Order.category_name,
            "department": Order.department_name,
            "segment": Order.customer_segment,
            "status": Order.order_status,
        }
        for key, column in mapping.items():
            value = filters.get(key)
            if value:
                statement = statement.where(column == value)

        risk_level = str(filters.get("risk_level") or "").lower()
        if risk_level in {"late", "high", "1"}:
            statement = statement.where(Order.late_delivery_risk == 1)
        elif risk_level in {"on time", "low", "0"}:
            statement = statement.where(Order.late_delivery_risk == 0)

        start_date = self._coerce_datetime_filter(filters.get("start_date"))
        end_date = self._coerce_datetime_filter(filters.get("end_date"))
        if start_date:
            statement = statement.where(Order.order_date >= start_date)
        if end_date:
            statement = statement.where(Order.order_date < end_date + timedelta(days=1))

        return statement

    def _coerce_datetime_filter(self, value: Any) -> Any:
        if not value:
            return None
        parsed = pd.to_datetime(value, errors="coerce")
        if pd.isna(parsed):
            return None
        return parsed.to_pydatetime()

    def _load_dataset(self) -> pd.DataFrame:
        if self._dataset is not None:
            return self._dataset
        path = settings.raw_supply_chain_dataset_path
        columns = [
            "Order Id",
            "Sales",
            "Order Profit Per Order",
            "Order Item Discount Rate",
            "Late_delivery_risk",
            "Market",
            "Order Region",
            "Order Country",
            "Category Name",
            "Department Name",
            "Customer Segment",
            "Order Status",
            "Shipping Mode",
            "Days for shipping (real)",
            "Days for shipment (scheduled)",
            "order date (DateOrders)",
        ]
        if not path.exists():
            self._dataset = pd.DataFrame(columns=columns)
            return self._dataset
        self._dataset = dashboard_dataset_repository.load(columns)
        return self._dataset

    def _filtered_dataset(self, filters: dict[str, Any] | None) -> pd.DataFrame:
        frame = self._load_dataset().copy()
        if frame.empty or not filters:
            return frame

        mapping = {
            "market": "Market",
            "order_region": "Order Region",
            "order_country": "Order Country",
            "shipping_mode": "Shipping Mode",
            "category": "Category Name",
            "department": "Department Name",
            "segment": "Customer Segment",
            "status": "Order Status",
        }
        for key, column in mapping.items():
            value = filters.get(key)
            if value and column in frame.columns:
                frame = frame[frame[column].astype(str) == str(value)]

        risk_level = str(filters.get("risk_level") or "").lower()
        if risk_level in {"late", "high", "1"}:
            frame = frame[frame["Late_delivery_risk"] == 1]
        elif risk_level in {"on time", "low", "0"}:
            frame = frame[frame["Late_delivery_risk"] == 0]

        dates = pd.to_datetime(frame.get("order date (DateOrders)"), errors="coerce")
        if filters.get("start_date"):
            start = pd.to_datetime(filters["start_date"], errors="coerce")
            if pd.notna(start):
                frame = frame[dates >= start]
                dates = dates[dates >= start]
        if filters.get("end_date"):
            end = pd.to_datetime(filters["end_date"], errors="coerce")
            if pd.notna(end):
                frame = frame[dates < end + pd.Timedelta(days=1)]

        return frame

    def _empty_summary(self) -> dict[str, Any]:
        return {
            "source": "none",
            "total_orders": 0,
            "total_rows": 0,
            "total_sales": 0.0,
            "total_profit": 0.0,
            "late_rate": 0.0,
            "avg_shipping_delay": 0.0,
            "high_risk_shipments": 0,
            "avg_discount_rate": 0.0,
            "total_categories": 0,
            "total_markets": 0,
        }

    def _unique_values(self, frame: pd.DataFrame, column: str, limit: int = 250) -> list[str]:
        if column not in frame.columns:
            return []
        values = frame[column].dropna().astype(str).sort_values().unique()
        return [value for value in values[:limit] if value]

    def _csv_date_range(self, frame: pd.DataFrame) -> dict[str, str | None]:
        dates = pd.to_datetime(frame.get("order date (DateOrders)"), errors="coerce").dropna()
        if dates.empty:
            return {"start": None, "end": None}
        return {
            "start": dates.min().date().isoformat(),
            "end": dates.max().date().isoformat(),
        }


dashboard_service = DashboardService()
