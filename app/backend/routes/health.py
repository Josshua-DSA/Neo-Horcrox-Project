from fastapi import APIRouter

from backend.core.model_registry import model_registry

router = APIRouter()


@router.get("/health", summary="Health check")
def health():
    return {
        "status": "ok",
        "database": "postgresql",
        "models": {
            "risk_model": model_registry.champion_model is not None,
            "forecast_model": model_registry.forecast_model is not None,
            "supplier_selection": "csv_json",
        },
        "artifacts": model_registry.status()["artifacts"],
    }
