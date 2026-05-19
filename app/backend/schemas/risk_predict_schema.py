"""Schemas and normalization helpers for late-delivery risk prediction."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RiskPredictionItem(BaseModel):
    index: int
    late_delivery_risk: int = Field(..., description="0 = on time, 1 = late risk")
    risk_label: str = Field(..., description="yes/no label for late delivery risk")
    delivery_label: str
    late_probability: float = Field(..., ge=0.0, le=1.0)
    on_time_probability: float = Field(..., ge=0.0, le=1.0)
    risk_probability: float = Field(..., ge=0.0, le=1.0)
    risk_percentage: float = Field(..., ge=0.0, le=100.0)
    threshold: float


class RiskPredictionResponse(BaseModel):
    count: int
    target: str = "Late_delivery_risk"
    model_name: str | None = None
    model_version: str | int | None = None
    predictions: list[RiskPredictionItem]


class RiskModelInfo(BaseModel):
    model_loaded: bool
    metadata_loaded: bool
    target: str = "Late_delivery_risk"
    threshold: float = 0.5
    features: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BatchRiskInput(BaseModel):
    model_config = ConfigDict(extra="allow")

    records: list[dict[str, Any]]


def normalize_records(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Accept single-record and batch payload variants used by the frontend."""
    if "records" in payload and isinstance(payload["records"], list):
        return [dict(item) for item in payload["records"]]
    if "orders" in payload and isinstance(payload["orders"], list):
        return [dict(item) for item in payload["orders"]]
    if "data" in payload and isinstance(payload["data"], list):
        return [dict(item) for item in payload["data"]]
    if "data" in payload and isinstance(payload["data"], dict):
        return [dict(payload["data"])]
    return [dict(payload)]
