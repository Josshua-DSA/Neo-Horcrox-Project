<<<<<<< HEAD
"""Schema helpers for supplier-selection requests."""


def parse_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_limit(value, default: int = 10, maximum: int = 100) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = default
    return max(1, min(limit, maximum))
=======
"""Schemas for read-only supplier selection ranking APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SupplierCategory(BaseModel):
    category_id: str
    category_name: str
    total_candidates: int
    primary_candidate_id: str | None = None
    primary_candidate_name: str | None = None


class SupplierCandidate(BaseModel):
    candidate_id: str
    candidate_name: str
    category_id: str
    category_name: str
    final_rank_in_category: int | None = None
    recommendation: str | None = None
    risk_level: str | None = None
    risk_score: float | None = None
    topsis_score: float | None = None
    total_orders: int | None = None
    total_sales: float | None = None
    total_profit: float | None = None
    late_rate: float | None = None
    prequalified: bool | None = None
    compliance_passed: bool | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)


class SupplierCandidateDetail(BaseModel):
    candidate: dict[str, Any]
    related_candidates: list[SupplierCandidate] = Field(default_factory=list)


class SupplierHealth(BaseModel):
    status: str
    data_loaded: bool
    total_categories: int
    total_candidates: int
    source_files: dict[str, str]


class SupplierWeight(BaseModel):
    criteria: str
    weight: float
>>>>>>> prefix-app
