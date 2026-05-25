"""Risk prediction API routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db
from backend.schemas.risk_predict_schema import (
    RiskModelInfo,
    RiskPredictionResponse,
    normalize_records,
)
from backend.services.order_service import get_prediction_logs, log_prediction
from backend.services.risk_predict_service import get_model_info, predict_records

router = APIRouter()


@router.get("/model", response_model=RiskModelInfo, summary="Risk model metadata")
def model_info():
    return get_model_info()


@router.post(
    "/predict",
    response_model=RiskPredictionResponse,
    summary="Predict late delivery risk and log the result to PostgreSQL",
)
async def predict_risk(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        records = normalize_records(payload)
        result = predict_records(records)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    for record, prediction in zip(records, result.predictions):
        await log_prediction(
            db,
            {
                "order_id": _coerce_int(record.get("Order Id") or record.get("order_id")),
                "prediction": prediction.late_delivery_risk,
                "probability_late": prediction.late_probability,
                "probability_on_time": prediction.on_time_probability,
                "label": prediction.delivery_label,
                "model_version": str(result.model_version or "unknown"),
                "input_snapshot": record,
            },
        )

    return result


@router.post(
    "/predict/batch",
    response_model=RiskPredictionResponse,
    summary="Batch predict late delivery risk",
)
async def predict_risk_batch(
    payload: dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
):
    return await predict_risk(payload, db)


@router.get("/logs", summary="Prediction logs from PostgreSQL")
async def prediction_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    prediction: int | None = Query(None, ge=0, le=1, description="0=on-time, 1=late"),
    db: AsyncSession = Depends(get_db),
):
    logs = await get_prediction_logs(db, skip=skip, limit=limit, prediction=prediction)
    return {"total": len(logs), "data": logs}


def _coerce_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None
