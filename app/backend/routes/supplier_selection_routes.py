"""Read-only supplier selection ranking routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from ..services.supplier_selection_service import supplier_selection_service

router = APIRouter(prefix="/supplier-selection", tags=["Supplier Selection"])


@router.get("/health", summary="Supplier selection artifact health")
def health() -> dict:
    return supplier_selection_service.health()


@router.get("/categories", summary="Supplier selection categories")
def categories() -> dict:
    items = [item.model_dump() for item in supplier_selection_service.categories()]
    return {"total": len(items), "data": items}


@router.get("/columns", summary="Supplier selection CSV columns")
def columns() -> dict:
    return supplier_selection_service.columns()


@router.get("/categories/{category_id}/products", summary="Ranked products/suppliers by category")
def products_by_category(
    category_id: str,
    limit: int = Query(20, ge=1, le=100),
    include_rejected: bool = Query(False),
) -> dict:
    try:
        items = supplier_selection_service.products_by_category(
            category_id=category_id,
            limit=limit,
            include_rejected=include_rejected,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    data = [item.model_dump() for item in items]
    return {"total": len(data), "data": data}


@router.get("/categories/{category_id}/preview", summary="Raw supplier selection preview by category")
def preview_by_category(
    category_id: str,
    limit: int = Query(5, ge=1, le=50),
) -> dict:
    try:
        return supplier_selection_service.preview_by_category(category_id, limit=limit)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/products/{candidate_id}", summary="Supplier/product candidate detail")
def product_profile(candidate_id: str) -> dict:
    try:
        return supplier_selection_service.product_profile(candidate_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/summary", summary="Supplier selection summary")
def summary() -> dict:
    return supplier_selection_service.summary()


@router.get("/weights", summary="Supplier selection AHP weights")
def weights() -> dict:
    data = supplier_selection_service.weights()
    return {"total": len(data), "data": data}
