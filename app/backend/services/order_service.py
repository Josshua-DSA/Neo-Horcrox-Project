"""MongoDB-backed order and analytics operations."""

from __future__ import annotations

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..schemas.db_models import OrderDocument, OrderItemDocument, PredictionLogDocument


class OrderService:
    async def get_order_by_id(self, db: AsyncIOMotorDatabase, order_id: int) -> dict[str, Any] | None:
        return await db.orders.find_one({"order_id": order_id}, {"_id": 0})

    async def get_orders(
        self,
        db: AsyncIOMotorDatabase,
        skip: int = 0,
        limit: int = 50,
        market: str | None = None,
        late_delivery_risk: int | None = None,
        shipping_mode: str | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if market:
            query["market"] = market
        if late_delivery_risk is not None:
            query["late_delivery_risk"] = late_delivery_risk
        if shipping_mode:
            query["shipping_mode"] = shipping_mode
        cursor = db.orders.find(query, {"_id": 0}).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def count_orders(
        self,
        db: AsyncIOMotorDatabase,
        market: str | None = None,
        late_delivery_risk: int | None = None,
        shipping_mode: str | None = None,
    ) -> int:
        query: dict[str, Any] = {}
        if market:
            query["market"] = market
        if late_delivery_risk is not None:
            query["late_delivery_risk"] = late_delivery_risk
        if shipping_mode:
            query["shipping_mode"] = shipping_mode
        return await db.orders.count_documents(query)

    async def insert_order(self, db: AsyncIOMotorDatabase, order: OrderDocument) -> str:
        result = await db.orders.insert_one(order.model_dump())
        return str(result.inserted_id)

    async def insert_orders_bulk(self, db: AsyncIOMotorDatabase, orders: list[OrderDocument]) -> int:
        docs = [order.model_dump() for order in orders]
        result = await db.orders.insert_many(docs, ordered=False)
        return len(result.inserted_ids)

    async def get_items_by_order(self, db: AsyncIOMotorDatabase, order_id: int) -> list[dict[str, Any]]:
        cursor = db.order_items.find({"order_id": order_id}, {"_id": 0})
        return await cursor.to_list(length=100)

    async def insert_order_items_bulk(self, db: AsyncIOMotorDatabase, items: list[OrderItemDocument]) -> int:
        docs = [item.model_dump() for item in items]
        result = await db.order_items.insert_many(docs, ordered=False)
        return len(result.inserted_ids)

    async def log_prediction(self, db: AsyncIOMotorDatabase, prediction_doc: PredictionLogDocument) -> str:
        result = await db.predictions.insert_one(prediction_doc.model_dump())
        return str(result.inserted_id)

    async def get_prediction_logs(
        self,
        db: AsyncIOMotorDatabase,
        skip: int = 0,
        limit: int = 50,
        prediction: int | None = None,
    ) -> list[dict[str, Any]]:
        query: dict[str, Any] = {}
        if prediction is not None:
            query["prediction"] = prediction
        cursor = db.predictions.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)


order_service = OrderService()


async def log_prediction(db: AsyncIOMotorDatabase, prediction_doc: PredictionLogDocument) -> str:
    return await order_service.log_prediction(db, prediction_doc)


async def get_prediction_logs(
    db: AsyncIOMotorDatabase,
    skip: int = 0,
    limit: int = 50,
    prediction: int | None = None,
) -> list[dict[str, Any]]:
    return await order_service.get_prediction_logs(db, skip=skip, limit=limit, prediction=prediction)
