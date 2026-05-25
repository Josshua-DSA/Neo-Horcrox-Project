"""Dashboard aggregation service with PostgreSQL-first and CSV fallback paths."""

from __future__ import annotations

import logging
from typing import Any
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct

from ..config import settings
from .dashboard_dataset import dashboard_dataset_repository
from ..schemas.db_models import Order, OrderItem

logger = logging.getLogger(__name__)


class DashboardService:
    """Computes dashboard data on the backend using PostgreSQL first, falling back to CSV."""

    def __init__(self) -> None:
        self._dataset: pd.DataFrame | None = None

    async def summary(self, db: AsyncSession | None) -> dict[str, Any]:
        if db is not None:
            try:
                # Query metrics from PostgreSQL
                q = select(
                    func.count(Order.id).label("total_orders"),
                    func.sum(func.coalesce(Order.sales_per_customer, 0)).label("total_sales"),
                    func.sum(func.coalesce(Order.order_profit_per_order, 0)).label("total_profit"),
                    func.avg(func.coalesce(Order.late_delivery_risk, 0)).label("late_rate"),
                    func.avg(func.coalesce(Order.days_for_shipping_real, 0) - func.coalesce(Order.days_for_shipment_scheduled, 0)).label("avg_shipping_delay"),
                    func.sum(func.coalesce(Order.late_delivery_risk, 0)).label("high_risk_shipments"),
                    func.count(distinct(Order.category_name)).label("total_categories"),
                    func.count(distinct(Order.market)).label("total_markets")
                )
                res = await db.execute(q)
                row = res.fetchone()
                
                if row and row.total_orders > 0:
                    # Get avg discount rate from OrderItem
                    q_discount = select(func.avg(func.coalesce(OrderItem.order_item_discount_rate, 0)))
                    res_discount = await db.execute(q_discount)
                    avg_discount = res_discount.scalar() or 0.0

                    return {
                        "source": "postgresql",
                        "total_orders": int(row.total_orders),
                        "total_rows": int(row.total_orders),
                        "total_sales": round(float(row.total_sales), 2),
                        "total_profit": round(float(row.total_profit), 2),
                        "late_rate": round(float(row.late_rate), 4),
                        "avg_shipping_delay": round(float(row.avg_shipping_delay), 2),
                        "high_risk_shipments": int(row.high_risk_shipments),
                        "avg_discount_rate": round(float(avg_discount), 4),
                        "total_categories": int(row.total_categories),
                        "total_markets": int(row.total_markets),
                    }
            except Exception as e:
                logger.warning(f"PostgreSQL dashboard summary query failed: {e}")

        # Fallback to CSV
        frame = self._load_dataset()
        if frame.empty:
            return self._empty_summary()
        return {
            "source": "csv",
            "total_orders": int(frame["Order Id"].nunique()),
            "total_rows": int(frame["Order Id"].nunique()),
            "total_sales": round(float(frame["Sales"].sum()), 2),
            "total_profit": round(float(frame["Order Profit Per Order"].sum()), 2),
            "late_rate": round(float(frame["Late_delivery_risk"].mean()), 4),
            "avg_shipping_delay": round(float((frame["Days for shipping (real)"] - frame["Days for shipment (scheduled)"]).mean()), 2),
            "high_risk_shipments": int(frame["Late_delivery_risk"].sum()),
            "avg_discount_rate": round(float(frame["Order Item Discount Rate"].mean()), 4),
            "total_categories": int(frame["Category Name"].nunique()),
            "total_markets": int(frame["Market"].nunique()),
        }

    async def filters(self, db: AsyncSession | None) -> dict[str, list[str]]:
        if db is not None:
            try:
                # Query unique values directly from Postgres
                async def get_distinct(column):
                    q = select(distinct(column)).where(column != None).order_by(column)
                    res = await db.execute(q)
                    return [str(v) for v in res.scalars().all() if v]

                return {
                    "markets": await get_distinct(Order.market),
                    "order_regions": await get_distinct(Order.order_region),
                    "order_countries": await get_distinct(Order.order_country),
                    "shipping_modes": await get_distinct(Order.shipping_mode),
                    "categories": await get_distinct(Order.category_name),
                    "departments": await get_distinct(Order.department_name),
                    "segments": await get_distinct(Order.customer_segment),
                    "statuses": await get_distinct(Order.order_status),
                }
            except Exception as e:
                logger.warning(f"PostgreSQL dashboard filters query failed: {e}")

        # Fallback to CSV
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
        }

    async def risk_by_market(self, db: AsyncSession | None) -> list[dict[str, Any]]:
        if db is not None:
            try:
                q = (
                    select(
                        Order.market,
                        func.count(Order.id).label("total_orders"),
                        func.sum(func.coalesce(Order.late_delivery_risk, 0)).label("late_orders"),
                        func.avg(func.coalesce(Order.late_delivery_risk, 0)).label("late_rate")
                    )
                    .group_by(Order.market)
                    .order_by(func.avg(func.coalesce(Order.late_delivery_risk, 0)).desc())
                )
                res = await db.execute(q)
                rows = res.all()
                if rows:
                    return [
                        {
                            "market": str(row.market or "Unknown"),
                            "total_orders": int(row.total_orders),
                            "late_orders": int(row.late_orders),
                            "late_rate": round(float(row.late_rate), 4),
                        }
                        for row in rows
                    ]
            except Exception as e:
                logger.warning(f"PostgreSQL dashboard risk_by_market query failed: {e}")

        # Fallback to CSV
        frame = self._load_dataset()
        if frame.empty:
            return []
        grouped = frame.groupby("Market", dropna=False).agg(
            total_orders=("Order Id", "nunique"),
            total_rows=("Order Id", "size"),
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

    async def sales_by_category(self, db: AsyncSession | None, limit: int = 20) -> list[dict[str, Any]]:
        if db is not None:
            try:
                q = (
                    select(
                        Order.category_name,
                        func.sum(func.coalesce(Order.sales_per_customer, 0)).label("total_sales"),
                        func.count(Order.id).label("order_count")
                    )
                    .group_by(Order.category_name)
                    .order_by(func.sum(func.coalesce(Order.sales_per_customer, 0)).desc())
                    .limit(limit)
                )
                res = await db.execute(q)
                rows = res.all()
                if rows:
                    return [
                        {
                            "category_name": str(row.category_name or "Unknown"),
                            "total_sales": round(float(row.total_sales), 2),
                            "order_count": int(row.order_count),
                        }
                        for row in rows
                    ]
            except Exception as e:
                logger.warning(f"PostgreSQL dashboard sales_by_category query failed: {e}")

        # Fallback to CSV
        frame = self._load_dataset()
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

    async def shipping_performance(self, db: AsyncSession | None) -> list[dict[str, Any]]:
        if db is not None:
            try:
                q = (
                    select(
                        Order.shipping_mode,
                        func.count(Order.id).label("order_count"),
                        func.avg(func.coalesce(Order.late_delivery_risk, 0)).label("late_rate"),
                        func.avg(Order.days_for_shipping_real).label("avg_shipping_days"),
                        func.avg(Order.days_for_shipment_scheduled).label("avg_scheduled_days")
                    )
                    .group_by(Order.shipping_mode)
                    .order_by(func.count(Order.id).desc())
                )
                res = await db.execute(q)
                rows = res.all()
                if rows:
                    return [
                        {
                            "shipping_mode": str(row.shipping_mode or "Unknown"),
                            "order_count": int(row.order_count),
                            "late_rate": round(float(row.late_rate), 4),
                            "avg_shipping_days": round(float(row.avg_shipping_days or 0), 2),
                            "avg_scheduled_days": round(float(row.avg_scheduled_days or 0), 2),
                        }
                        for row in rows
                    ]
            except Exception as e:
                logger.warning(f"PostgreSQL dashboard shipping_performance query failed: {e}")

        # Fallback to CSV
        frame = self._load_dataset()
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
        ]
        if not path.exists():
            self._dataset = pd.DataFrame(columns=columns)
            return self._dataset
        self._dataset = dashboard_dataset_repository.load(columns)
        return self._dataset

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


dashboard_service = DashboardService()
