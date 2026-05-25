"""Supplier selection read-only routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.schemas.supplier_selection_schema import (
    SupplierCandidateDetail,
    SupplierHealth,
)
from backend.services.supplier_selection_service import supplier_selection_service

router = APIRouter()


@router.get("/health", response_model=SupplierHealth, summary="Supplier selection data health")
def health():
    return supplier_selection_service.health()


@router.get("/categories", summary="List product categories")
def categories():
    data = supplier_selection_service.categories()
    return {"total": len(data), "data": data}


@router.get("/categories/{category_id}/products", summary="List ranked products by category")
def products(
    category_id: str,
    limit: int = Query(25, ge=1, le=100),
    include_rejected: bool = Query(True),
):
    data = supplier_selection_service.products(
        category_id=category_id,
        limit=limit,
        include_rejected=include_rejected,
    )
    return {"total": len(data), "data": data}


@router.get(
    "/products/{candidate_id}",
    response_model=SupplierCandidateDetail,
    summary="Product candidate detail with forecast and risk inputs",
)
def product_detail(candidate_id: str):
    detail = supplier_selection_service.product_detail(candidate_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} tidak ditemukan")
    return detail


@router.get("/summary", summary="Supplier selection summary")
def summary():
    return supplier_selection_service.summary()


@router.get("/weights", summary="Supplier selection AHP weights")
def weights():
    data = supplier_selection_service.weights()
    return {"total": len(data), "data": data}
