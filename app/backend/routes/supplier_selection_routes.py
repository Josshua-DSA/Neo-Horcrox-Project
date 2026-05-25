from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from backend.schemas.forecast_supplier import SupplierInput, SupplierResponse
from backend.services.supplier_service import recommend_supplier
from backend.core.model_registry import model_registry

router = APIRouter()

@router.post("/recommend", response_model=SupplierResponse, summary="Rekomendasi supplier terbaik")
def get_supplier_recommendation(payload: SupplierInput):
    if model_registry.supplier_model is None:
        raise HTTPException(status_code=503, detail="Supplier model belum di-load.")
    try:
        return recommend_supplier(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaderboard")
def supplier_leaderboard(
    market: Optional[str] = Query(None),
    shipping_mode: Optional[str] = Query(None),
    top_n: int = Query(20, ge=1, le=100),
):
    lookup = model_registry.supplier_lookup
    if lookup is None:
        raise HTTPException(status_code=503, detail="Supplier model belum di-load.")
    results = lookup
    if market:
        results = [r for r in results if r.get("Market") == market]
    if shipping_mode:
        results = [r for r in results if r.get("Shipping Mode") == shipping_mode]
    results = sorted(results, key=lambda r: r.get("supplier_score", 0), reverse=True)[:top_n]
    return {"total": len(results), "data": results}

@router.get("/metadata")
def supplier_metadata():
    meta = model_registry.supplier_metadata
    if meta is None:
        raise HTTPException(status_code=503, detail="Supplier model belum di-load.")
    return meta