"""Order CRUD routes backed by MongoDB."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.database import get_db
from ..schemas.db_models import OrderDocument
from ..services.order_service import order_service

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("", summary="List orders with filters and pagination")
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    market: str | None = None,
    late_delivery_risk: int | None = Query(None, ge=0, le=1),
    shipping_mode: str | None = None,
    db: AsyncIOMotorDatabase | None = Depends(get_db),
) -> dict:
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB is not connected.")
    orders = await order_service.get_orders(
        db,
        skip=skip,
        limit=limit,
        market=market,
        late_delivery_risk=late_delivery_risk,
        shipping_mode=shipping_mode,
    )
    total = await order_service.count_orders(
        db,
        market=market,
        late_delivery_risk=late_delivery_risk,
        shipping_mode=shipping_mode,
    )
    return {"total": total, "skip": skip, "limit": limit, "data": orders}


@router.get("/{order_id}", summary="Get one order with items")
async def get_order(order_id: int, db: AsyncIOMotorDatabase | None = Depends(get_db)) -> dict:
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB is not connected.")
    order = await order_service.get_order_by_id(db, order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} was not found.")
    items = await order_service.get_items_by_order(db, order_id)
    return {"order": order, "items": items}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Insert one order")
async def create_order(order: OrderDocument, db: AsyncIOMotorDatabase | None = Depends(get_db)) -> dict:
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB is not connected.")
    inserted_id = await order_service.insert_order(db, order)
    return {"inserted_id": inserted_id, "order_id": order.order_id}


@router.post("/bulk", status_code=status.HTTP_201_CREATED, summary="Insert orders in bulk")
async def create_orders_bulk(
    orders: list[OrderDocument],
    db: AsyncIOMotorDatabase | None = Depends(get_db),
) -> dict:
    if db is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="MongoDB is not connected.")
    if not orders:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="orders list is empty.")
    if len(orders) > 5000:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Max bulk insert is 5000 documents.")
    count = await order_service.insert_orders_bulk(db, orders)
    return {"inserted": count}
