"""Dashboard API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.database import get_db
from ..services.dashboard_service import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", summary="Dashboard summary metrics")
async def summary(db: AsyncIOMotorDatabase | None = Depends(get_db)) -> dict:
    return await dashboard_service.summary(db)


@router.get("/filters", summary="Dashboard filter options from raw dataset")
async def filters(db: AsyncIOMotorDatabase | None = Depends(get_db)) -> dict:
    return await dashboard_service.filters(db)


@router.get("/risk-by-market", summary="Late delivery risk by market")
async def risk_by_market(db: AsyncIOMotorDatabase | None = Depends(get_db)) -> dict:
    data = await dashboard_service.risk_by_market(db)
    return {"total": len(data), "data": data}


@router.get("/sales-by-category", summary="Sales by category")
async def sales_by_category(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncIOMotorDatabase | None = Depends(get_db),
) -> dict:
    data = await dashboard_service.sales_by_category(db, limit=limit)
    return {"total": len(data), "data": data}


@router.get("/shipping-performance", summary="Shipping performance by mode")
async def shipping_performance(db: AsyncIOMotorDatabase | None = Depends(get_db)) -> dict:
    data = await dashboard_service.shipping_performance(db)
    return {"total": len(data), "data": data}
