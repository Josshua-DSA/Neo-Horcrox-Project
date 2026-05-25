from fastapi import APIRouter, HTTPException, status
from backend.schemas.forecast_supplier import ForecastInput, ForecastResponse
from backend.services.forecast_service import predict_forecast
from backend.core.model_registry import model_registry

router = APIRouter()

@router.post("/predict", response_model=ForecastResponse, summary="Prediksi demand sales harian")
def forecast_demand(payload: ForecastInput):
    if model_registry.forecast_model is None:
        raise HTTPException(status_code=503, detail="Forecast model belum di-load.")
    try:
        return predict_forecast(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/categories")
def list_categories():
    meta = model_registry.forecast_metadata
    if meta is None:
        raise HTTPException(status_code=503, detail="Forecast model belum di-load.")
    return {"categories": meta.get("categories", [])}

@router.get("/markets")
def list_markets():
    meta = model_registry.forecast_metadata
    if meta is None:
        raise HTTPException(status_code=503, detail="Forecast model belum di-load.")
    return {"markets": meta.get("markets", [])}

@router.get("/metadata")
def forecast_metadata():
    meta = model_registry.forecast_metadata
    if meta is None:
        raise HTTPException(status_code=503, detail="Forecast model belum di-load.")
    return meta