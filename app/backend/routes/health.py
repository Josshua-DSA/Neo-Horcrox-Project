from fastapi import APIRouter
from backend.core.model_registry import model_registry

router = APIRouter()

@router.get("/health", summary="Health check")
def health():
    return {
        "status": "ok",
        "models": {
            "risk_model":     model_registry.risk_model is not None,
            "forecast_model": model_registry.forecast_model is not None,
            "supplier_model": model_registry.supplier_model is not None,
        },
    }