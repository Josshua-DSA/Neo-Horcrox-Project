"""
routers/risk.py
---------------
POST /api/v1/risk/predict          → single prediction (+ log ke PostgreSQL)
POST /api/v1/risk/predict/batch    → batch prediction
GET  /api/v1/risk/logs             → lihat history prediksi dari DB
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from backend.schemas.risk import RiskInput, RiskResponse, BatchRiskInput, BatchRiskResponse
from backend.services.prediction import predict_single, predict_batch
from backend.services.order_service import log_prediction, get_prediction_logs
from backend.core.database import get_db

router = APIRouter()


@router.post(
    "/predict",
    response_model=RiskResponse,
    summary="Predict late delivery risk (hasil di-log ke PostgreSQL)",
)
async def predict_risk(
    order: RiskInput,
    db: AsyncSession = Depends(get_db),
):
    try:
        result = predict_single(order)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Log ke PostgreSQL
    log_data = {
        "order_id": order.dict(by_alias=True).get("Order Id"),
        "prediction": result.prediction,
        "probability_late": result.probability_late,
        "probability_on_time": result.probability_on_time,
        "label": result.label,
        "model_version": result.model_version,
        "input_snapshot": order.dict(by_alias=True),
    }
    await log_prediction(db, log_data)

    return result


@router.post(
    "/predict/batch",
    response_model=BatchRiskResponse,
    summary="Batch prediction (tanpa log individual)",
)
async def predict_risk_batch(payload: BatchRiskInput):
    if not payload.orders:
        raise HTTPException(status_code=400, detail="orders list kosong")
    if len(payload.orders) > 1000:
        raise HTTPException(status_code=400, detail="Max batch size 1000")
    try:
        return predict_batch(payload.orders)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/logs",
    summary="Lihat history log prediksi dari PostgreSQL",
)
async def prediction_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    prediction: Optional[int] = Query(None, ge=0, le=1, description="0=on-time, 1=late"),
    db: AsyncSession = Depends(get_db),
):
    logs = await get_prediction_logs(db, skip=skip, limit=limit, prediction=prediction)
    return {"total": len(logs), "data": logs}