"""Dashboard API routes."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..services.dashboard_service import dashboard_service

router = APIRouter()


def dashboard_filters(
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    market: str | None = Query(None),
    order_region: str | None = Query(None),
    order_country: str | None = Query(None),
    shipping_mode: str | None = Query(None),
    category: str | None = Query(None),
    department: str | None = Query(None),
    segment: str | None = Query(None),
    status: str | None = Query(None),
    risk_level: str | None = Query(None),
) -> dict[str, Any]:
    return {
        "start_date": start_date,
        "end_date": end_date,
        "market": market,
        "order_region": order_region,
        "order_country": order_country,
        "shipping_mode": shipping_mode,
        "category": category,
        "department": department,
        "segment": segment,
        "status": status,
        "risk_level": risk_level,
    }


@router.get("/summary", summary="Dashboard summary metrics")
async def summary(
    db: AsyncSession = Depends(get_db),
    filters: dict[str, Any] = Depends(dashboard_filters),
) -> dict:
    return await dashboard_service.summary(db, filters)


@router.get("/filters", summary="Dashboard filter options from raw dataset")
async def filters(db: AsyncSession = Depends(get_db)) -> dict:
    return await dashboard_service.filters(db)


@router.get("/risk-by-market", summary="Late delivery risk by market")
async def risk_by_market(
    db: AsyncSession = Depends(get_db),
    filters: dict[str, Any] = Depends(dashboard_filters),
) -> dict:
    data = await dashboard_service.risk_by_market(db, filters)
    return {"total": len(data), "data": data}


@router.get("/sales-by-category", summary="Sales by category")
async def sales_by_category(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    filters: dict[str, Any] = Depends(dashboard_filters),
) -> dict:
    data = await dashboard_service.sales_by_category(db, limit=limit, filters=filters)
    return {"total": len(data), "data": data}


@router.get("/shipping-performance", summary="Shipping performance by mode")
async def shipping_performance(
    db: AsyncSession = Depends(get_db),
    filters: dict[str, Any] = Depends(dashboard_filters),
) -> dict:
    data = await dashboard_service.shipping_performance(db, filters)
    return {"total": len(data), "data": data}
