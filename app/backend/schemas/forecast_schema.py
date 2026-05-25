"""Pydantic schemas for demand forecasting."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ForecastInput(BaseModel):
    category_name: str
    market: str
    periods: int = Field(30, ge=1, le=365)
    order_month: int | None = Field(None, ge=1, le=12)
    order_year: int | None = Field(None, ge=2000, le=2100)


class ForecastPoint(BaseModel):
    date: str
    predicted_sales: float
    lower_bound: float | None = None
    upper_bound: float | None = None


class ForecastResponse(BaseModel):
    category_name: str
    market: str
    periods: int
    forecast: list[ForecastPoint]
    model_version: str = "0.1.0"
