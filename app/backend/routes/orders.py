"""
routers/orders.py
------------------
CRUD endpoints untuk data order supply chain.

GET  /api/v1/orders                    → list orders (filter + pagination)
GET  /api/v1/orders/{order_id}         → detail satu order + items-nya
GET  /api/v1/orders/analytics/risk     → summary late delivery per market
GET  /api/v1/orders/analytics/sales    → sales per category
POST /api/v1/orders                    → insert satu order
POST /api/v1/orders/bulk               → insert banyak order sekaligus
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from backend.core.database import get_db
from backend.services import order_service

router = APIRouter()


@router.get("", summary="List orders dengan filter & pagination")
async def list_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    market: Optional[str] = Query(None, description="Africa | Europe | LATAM | Pacific Asia | USCA"),
    late_delivery_risk: Optional[int] = Query(None, ge=0, le=1),
    shipping_mode: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    orders = await order_service.get_orders(
        db, skip=skip, limit=limit,
        market=market,
        late_delivery_risk=late_delivery_risk,
        shipping_mode=shipping_mode,
    )
    total = await order_service.count_orders(db, market=market, late_delivery_risk=late_delivery_risk)
    return {"total": total, "skip": skip, "limit": limit, "data": orders}


@router.get("/analytics/risk", summary="Summary late delivery risk per market")
async def risk_summary(db: AsyncSession = Depends(get_db)):
    return await order_service.get_risk_summary(db)


@router.get("/analytics/sales", summary="Total sales & profit per category")
async def sales_by_category(db: AsyncSession = Depends(get_db)):
    return await order_service.get_sales_by_category(db)


@router.get("/{order_id}", summary="Detail satu order beserta items-nya")
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} tidak ditemukan")
    items = await order_service.get_items_by_order(db, order_id)
    return {"order": order, "items": items}


@router.post("", status_code=status.HTTP_201_CREATED, summary="Insert satu order")
async def create_order(order: dict, db: AsyncSession = Depends(get_db)):
    inserted_id = await order_service.insert_order(db, order)
    return {"inserted_id": inserted_id, "order_id": order.get("order_id")}


@router.post("/bulk", status_code=status.HTTP_201_CREATED, summary="Insert banyak order sekaligus")
async def create_orders_bulk(
    orders: List[dict],
    db: AsyncSession = Depends(get_db),
):
    if not orders:
        raise HTTPException(status_code=400, detail="orders list kosong")
    if len(orders) > 5000:
        raise HTTPException(status_code=400, detail="Max bulk insert adalah 5000 dokumen")
    count = await order_service.insert_orders_bulk(db, orders)
    return {"inserted": count}