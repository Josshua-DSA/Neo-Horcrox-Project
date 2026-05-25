"""
services/order_service.py
--------------------------
CRUD operations untuk tabel `orders`, `order_items`, dan `predictions`.
Menggunakan SQLAlchemy async session untuk PostgreSQL.
"""

import logging
from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, insert

from backend.schemas.db_models import Order, OrderItem, PredictionLog

logger = logging.getLogger(__name__)


# ─── Orders ──────────────────────────────────────────────────────────────────

async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[dict]:
    result = await db.execute(
        select(Order).where(Order.order_id == order_id)
    )
    order = result.scalars().first()
    return order.to_dict() if order else None


async def get_orders(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    market: Optional[str] = None,
    late_delivery_risk: Optional[int] = None,
    shipping_mode: Optional[str] = None,
) -> List[dict]:
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


async def insert_order(db: AsyncSession, order_data: dict) -> int:
    order = Order(**order_data)
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order.id


async def insert_orders_bulk(db: AsyncSession, orders_data: List[dict]) -> int:
    order_objects = [Order(**data) for data in orders_data]
    db.add_all(order_objects)
    await db.commit()
    return len(order_objects)


async def count_orders(
    db: AsyncSession,
    market: Optional[str] = None,
    late_delivery_risk: Optional[int] = None,
) -> int:
    query = select(func.count(Order.id))
    if market:
        query = query.where(Order.market == market)
    if late_delivery_risk is not None:
        query = query.where(Order.late_delivery_risk == late_delivery_risk)
    result = await db.execute(query)
    return result.scalar() or 0


# ─── Order Items ──────────────────────────────────────────────────────────────

async def get_items_by_order(db: AsyncSession, order_id: int) -> List[dict]:
    result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order_id)
    )
    return [row.to_dict() for row in result.scalars().all()]


async def insert_order_items_bulk(db: AsyncSession, items_data: List[dict]) -> int:
    item_objects = [OrderItem(**data) for data in items_data]
    db.add_all(item_objects)
    await db.commit()
    return len(item_objects)


# ─── Prediction Log ───────────────────────────────────────────────────────────

async def log_prediction(db: AsyncSession, prediction_data: dict) -> int:
    prediction = PredictionLog(**prediction_data)
    db.add(prediction)
    await db.commit()
    await db.refresh(prediction)
    return prediction.id


async def get_prediction_logs(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 50,
    prediction: Optional[int] = None,
) -> List[dict]:
    query = select(PredictionLog)
    if prediction is not None:
        query = query.where(PredictionLog.prediction == prediction)
    query = query.order_by(PredictionLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return [row.to_dict() for row in result.scalars().all()]


# ─── Analytics queries ────────────────────────────────────────────────────────

async def get_risk_summary(db: AsyncSession) -> dict:
    """Aggregate: jumlah late vs on-time per market."""
    query = (
        select(
            Order.market,
            Order.late_delivery_risk,
            func.count(Order.id).label("count"),
        )
        .group_by(Order.market, Order.late_delivery_risk)
        .order_by(Order.market)
    )
    result = await db.execute(query)
    rows = result.all()
    summary = [
        {
            "_id": {"market": row.market, "late_delivery_risk": row.late_delivery_risk},
            "count": row.count,
        }
        for row in rows
    ]
    return {"summary": summary}


async def get_sales_by_category(db: AsyncSession) -> dict:
    """Aggregate: total sales per category."""
    query = (
        select(
            Order.category_name,
            func.sum(Order.sales_per_customer).label("total_sales"),
            func.sum(Order.order_profit_per_order).label("total_profit"),
            func.count(Order.id).label("order_count"),
        )
        .group_by(Order.category_name)
        .order_by(func.sum(Order.sales_per_customer).desc())
        .limit(20)
    )
    result = await db.execute(query)
    rows = result.all()
    categories = [
        {
            "_id": row.category_name,
            "total_sales": float(row.total_sales) if row.total_sales else 0.0,
            "total_profit": float(row.total_profit) if row.total_profit else 0.0,
            "order_count": row.order_count,
        }
        for row in rows
    ]
    return {"categories": categories}