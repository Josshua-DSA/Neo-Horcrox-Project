"""FastAPI routes for the business risk feature."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..schemas.risk_predict_schema import RiskModelInfo, RiskPredictionResponse, normalize_records
from ..services.order_service import order_service
from ..services.risk_predict_service import risk_prediction_service

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.get("/model", response_model=RiskModelInfo, summary="Production risk model metadata")
def model_info() -> RiskModelInfo:
    return risk_prediction_service.get_model_info()


@router.post("/predict", response_model=RiskPredictionResponse, summary="Predict late delivery risk")
async def predict_risk(
    payload: dict[str, Any],
    db: AsyncSession = Depends(get_db),
) -> RiskPredictionResponse:
    try:
        result = risk_prediction_service.predict(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    if db is not None:
        await _log_predictions(db, payload, result)
    return result


@router.get("/logs", summary="Prediction logs from PostgreSQL")
async def prediction_logs(
    skip: int = 0,
    limit: int = 50,
    prediction: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    logs = await order_service.get_prediction_logs(db, skip=skip, limit=limit, prediction=prediction)
    return {"total": len(logs), "data": logs}


async def _log_predictions(
    db: AsyncSession,
    payload: dict[str, Any],
    result: RiskPredictionResponse,
) -> None:
    records = normalize_records(payload)
    for item in result.predictions:
        snapshot = records[item.index] if item.index < len(records) else {}
        doc = {
            "order_id": _extract_order_id(snapshot),
            "prediction": item.late_delivery_risk,
            "probability_late": item.late_probability,
            "probability_on_time": item.on_time_probability,
            "label": item.risk_label,
            "model_version": str(result.model_version or "unknown"),
            "input_snapshot": snapshot,
        }
        await order_service.log_prediction(db, doc)


def _extract_order_id(snapshot: dict[str, Any]) -> int | None:
    for key in ("Order Id", "order_id", "orderId"):
        value = snapshot.get(key)
        if value in (None, ""):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None
