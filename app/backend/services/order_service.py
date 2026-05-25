"""PostgreSQL-backed order and analytics operations."""

from __future__ import annotations

import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert

from ..schemas.db_models import Order, OrderItem, PredictionLog

logger = logging.getLogger(__name__)


class OrderService:
    async def get_order_by_id(self, db: AsyncSession, order_id: int) -> dict[str, Any] | None:
        result = await db.execute(
            select(Order).where(Order.order_id == order_id)
        )
        order = result.scalars().first()
        return order.to_dict() if order else None

    async def get_orders(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        market: str | None = None,
        late_delivery_risk: int | None = None,
        shipping_mode: str | None = None,
    ) -> list[dict[str, Any]]:
        query = select(Order)
        if market:
            query = query.where(Order.market == market)
        if late_delivery_risk is not None:
            query = query.where(Order.late_delivery_risk == late_delivery_risk)
        if shipping_mode:
            query = query.where(Order.shipping_mode == shipping_mode)

        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return [row.to_dict() for row in result.scalars().all()]

    async def count_orders(
        self,
        db: AsyncSession,
        market: str | None = None,
        late_delivery_risk: int | None = None,
        shipping_mode: str | None = None,
    ) -> int:
        query = select(func.count(Order.id))
        if market:
            query = query.where(Order.market == market)
        if late_delivery_risk is not None:
            query = query.where(Order.late_delivery_risk == late_delivery_risk)
        if shipping_mode:
            query = query.where(Order.shipping_mode == shipping_mode)
        result = await db.execute(query)
        return result.scalar() or 0

    async def insert_order(self, db: AsyncSession, order_data: Any) -> int:
        # Convert to dict if needed
        data = order_data if isinstance(order_data, dict) else order_data.dict(by_alias=True)
        # Ensure we filter out id or other non-existent fields if passed
        order = Order(**data)
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order.id

    async def insert_orders_bulk(self, db: AsyncSession, orders_data: list[Any]) -> int:
        docs = [data if isinstance(data, dict) else data.dict(by_alias=True) for data in orders_data]
        order_objects = [Order(**data) for data in docs]
        db.add_all(order_objects)
        await db.commit()
        return len(order_objects)

    async def get_items_by_order(self, db: AsyncSession, order_id: int) -> list[dict[str, Any]]:
        result = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        return [row.to_dict() for row in result.scalars().all()]

    async def insert_order_items_bulk(self, db: AsyncSession, items_data: list[Any]) -> int:
        docs = [data if isinstance(data, dict) else data.dict(by_alias=True) for data in items_data]
        item_objects = [OrderItem(**data) for data in docs]
        db.add_all(item_objects)
        await db.commit()
        return len(item_objects)

    async def log_prediction(self, db: AsyncSession, prediction_data: Any) -> int:
        data = prediction_data if isinstance(prediction_data, dict) else prediction_data.dict(by_alias=True)
        prediction = PredictionLog(**data)
        db.add(prediction)
        await db.commit()
        await db.refresh(prediction)
        return prediction.id

    async def get_prediction_logs(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        prediction: int | None = None,
    ) -> list[dict[str, Any]]:
        query = select(PredictionLog)
        if prediction is not None:
            query = query.where(PredictionLog.prediction == prediction)
        query = query.order_by(PredictionLog.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return [row.to_dict() for row in result.scalars().all()]


order_service = OrderService()


async def log_prediction(db: AsyncSession, prediction_data: Any) -> int:
    return await order_service.log_prediction(db, prediction_data)


async def get_prediction_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    prediction: int | None = None,
) -> list[dict[str, Any]]:
    return await order_service.get_prediction_logs(db, skip=skip, limit=limit, prediction=prediction)
