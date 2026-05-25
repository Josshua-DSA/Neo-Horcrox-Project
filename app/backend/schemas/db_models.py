"""Pydantic models for MongoDB documents used by the backend."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OrderDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    order_id: int
    order_date: datetime | None = None
    shipping_date: datetime | None = None

    customer_id: int | None = None
    customer_segment: str | None = None
    customer_city: str | None = None
    customer_state: str | None = None
    customer_country: str | None = None

    shipping_mode: str | None = None
    days_for_shipping_real: int | None = None
    days_for_shipment_scheduled: int | None = None
    delivery_status: str | None = None
    late_delivery_risk: int | None = None

    market: str | None = None
    order_region: str | None = None
    order_country: str | None = None
    order_city: str | None = None
    order_state: str | None = None

    sales_per_customer: float | None = None
    benefit_per_order: float | None = None
    order_profit_per_order: float | None = None
    order_status: str | None = None
    type: str | None = None

    product_card_id: int | None = None
    product_name: str | None = None
    product_price: float | None = None
    product_status: int | None = None
    category_id: int | None = None
    category_name: str | None = None
    department_id: int | None = None
    department_name: str | None = None

    latitude: float | None = None
    longitude: float | None = None


class OrderItemDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    order_item_id: int
    order_id: int
    product_card_id: int | None = None
    order_item_cardprod_id: int | None = None
    order_item_quantity: int | None = None
    order_item_product_price: float | None = None
    order_item_discount: float | None = None
    order_item_discount_rate: float | None = None
    order_item_profit_ratio: float | None = None
    sales: float | None = None
    order_item_total: float | None = None


class PredictionLogDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    order_id: int | None = None
    prediction: int
    probability_late: float
    probability_on_time: float
    label: str
    model_version: str
    input_snapshot: dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ForecastLogDocument(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    category_name: str
    market: str
    periods: int
    forecast_result: list[dict[str, Any]]
    model_version: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
