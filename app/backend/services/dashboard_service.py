"""Dashboard aggregation service with MongoDB-first and CSV fallback paths."""

from __future__ import annotations

from typing import Any

import pandas as pd
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..config import settings
from .dashboard_dataset import dashboard_dataset_repository


class DashboardService:
    """Computes dashboard data on the backend so the frontend stays simple."""

    def __init__(self) -> None:
        self._dataset: pd.DataFrame | None = None

    async def summary(self, db: AsyncIOMotorDatabase | None) -> dict[str, Any]:
        if db is not None:
            result = await self._mongo_summary(db)
            if result["total_orders"] > 0:
                return result
        frame = self._load_dataset()
        if frame.empty:
            return self._empty_summary()
        return {
            "source": "csv",
            "total_orders": int(frame["Order Id"].nunique()),
            "total_rows": int(len(frame)),
            "total_sales": round(float(frame["Sales"].sum()), 2),
            "total_profit": round(float(frame["Order Profit Per Order"].sum()), 2),
            "late_rate": round(float(frame["Late_delivery_risk"].mean()), 4),
            "avg_shipping_delay": round(float((frame["Days for shipping (real)"] - frame["Days for shipment (scheduled)"]).mean()), 2),
            "high_risk_shipments": int(frame["Late_delivery_risk"].sum()),
            "avg_discount_rate": round(float(frame["Order Item Discount Rate"].mean()), 4),
            "total_categories": int(frame["Category Name"].nunique()),
            "total_markets": int(frame["Market"].nunique()),
        }

    async def filters(self, db: AsyncIOMotorDatabase | None) -> dict[str, list[str]]:
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

    async def risk_by_market(self, db: AsyncIOMotorDatabase | None) -> list[dict[str, Any]]:
        if db is not None:
            result = await self._mongo_risk_by_market(db)
            if result:
                return result
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

    async def sales_by_category(self, db: AsyncIOMotorDatabase | None, limit: int = 20) -> list[dict[str, Any]]:
        if db is not None:
            result = await self._mongo_sales_by_category(db, limit)
            if result:
                return result
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

    async def shipping_performance(self, db: AsyncIOMotorDatabase | None) -> list[dict[str, Any]]:
        if db is not None:
            result = await self._mongo_shipping_performance(db)
            if result:
                return result
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

    async def _mongo_summary(self, db: AsyncIOMotorDatabase) -> dict[str, Any]:
        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_orders": {"$sum": 1},
                    "total_sales": {"$sum": {"$ifNull": ["$sales_per_customer", 0]}},
                    "total_profit": {"$sum": {"$ifNull": ["$order_profit_per_order", 0]}},
                    "late_rate": {"$avg": {"$ifNull": ["$late_delivery_risk", 0]}},
                    "avg_shipping_delay": {
                        "$avg": {
                            "$subtract": [
                                {"$ifNull": ["$days_for_shipping_real", 0]},
                                {"$ifNull": ["$days_for_shipment_scheduled", 0]},
                            ]
                        }
                    },
                    "high_risk_shipments": {"$sum": {"$ifNull": ["$late_delivery_risk", 0]}},
                    "avg_discount_rate": {"$avg": {"$ifNull": ["$order_item_discount_rate", 0]}},
                    "categories": {"$addToSet": "$category_name"},
                    "markets": {"$addToSet": "$market"},
                }
            }
        ]
        rows = await db.orders.aggregate(pipeline).to_list(length=1)
        if not rows:
            return self._empty_summary()
        row = rows[0]
        return {
            "source": "mongodb",
            "total_orders": int(row.get("total_orders", 0)),
            "total_rows": int(row.get("total_orders", 0)),
            "total_sales": round(float(row.get("total_sales", 0)), 2),
            "total_profit": round(float(row.get("total_profit", 0)), 2),
            "late_rate": round(float(row.get("late_rate", 0)), 4),
            "avg_shipping_delay": round(float(row.get("avg_shipping_delay", 0)), 2),
            "high_risk_shipments": int(row.get("high_risk_shipments", 0)),
            "avg_discount_rate": round(float(row.get("avg_discount_rate", 0)), 4),
            "total_categories": len(row.get("categories", [])),
            "total_markets": len(row.get("markets", [])),
        }

    async def _mongo_risk_by_market(self, db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": "$market",
                    "total_orders": {"$sum": 1},
                    "late_orders": {"$sum": {"$ifNull": ["$late_delivery_risk", 0]}},
                    "late_rate": {"$avg": {"$ifNull": ["$late_delivery_risk", 0]}},
                }
            },
            {"$sort": {"late_rate": -1}},
        ]
        rows = await db.orders.aggregate(pipeline).to_list(length=None)
        return [
            {
                "market": row.get("_id") or "Unknown",
                "total_orders": int(row.get("total_orders", 0)),
                "late_orders": int(row.get("late_orders", 0)),
                "late_rate": round(float(row.get("late_rate", 0)), 4),
            }
            for row in rows
        ]

    async def _mongo_sales_by_category(self, db: AsyncIOMotorDatabase, limit: int) -> list[dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": "$category_name",
                    "total_sales": {"$sum": {"$ifNull": ["$sales_per_customer", 0]}},
                    "order_count": {"$sum": 1},
                }
            },
            {"$sort": {"total_sales": -1}},
            {"$limit": limit},
        ]
        rows = await db.orders.aggregate(pipeline).to_list(length=limit)
        return [
            {
                "category_name": row.get("_id") or "Unknown",
                "total_sales": round(float(row.get("total_sales", 0)), 2),
                "order_count": int(row.get("order_count", 0)),
            }
            for row in rows
        ]

    async def _mongo_shipping_performance(self, db: AsyncIOMotorDatabase) -> list[dict[str, Any]]:
        pipeline = [
            {
                "$group": {
                    "_id": "$shipping_mode",
                    "order_count": {"$sum": 1},
                    "late_rate": {"$avg": {"$ifNull": ["$late_delivery_risk", 0]}},
                    "avg_shipping_days": {"$avg": "$days_for_shipping_real"},
                    "avg_scheduled_days": {"$avg": "$days_for_shipment_scheduled"},
                }
            },
            {"$sort": {"order_count": -1}},
        ]
        rows = await db.orders.aggregate(pipeline).to_list(length=None)
        return [
            {
                "shipping_mode": row.get("_id") or "Unknown",
                "order_count": int(row.get("order_count", 0)),
                "late_rate": round(float(row.get("late_rate", 0)), 4),
                "avg_shipping_days": round(float(row.get("avg_shipping_days", 0) or 0), 2),
                "avg_scheduled_days": round(float(row.get("avg_scheduled_days", 0) or 0), 2),
            }
            for row in rows
        ]


dashboard_service = DashboardService()
