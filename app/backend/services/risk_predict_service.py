"""Late shipment risk prediction service."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from backend.core.model_registry import model_registry
from backend.schemas.risk_predict_schema import (
    RiskModelInfo,
    RiskPredictionItem,
    RiskPredictionResponse,
)
from model.src.features.build_features import build_late_shipment_features


MODEL_NOT_READY_MSG = (
    "Risk model artifact is not loaded. "
    "Make sure model/artifacts/models/champion_model is available."
)


def get_model_info() -> RiskModelInfo:
    metadata = model_registry.champion_metadata or {}
    return RiskModelInfo(
        model_loaded=model_registry.champion_model is not None,
        metadata_loaded=bool(metadata),
        target=metadata.get("target", "Late_delivery_risk"),
        threshold=float(metadata.get("threshold", 0.5)),
        features=list(metadata.get("features", [])),
        metadata=metadata,
    )


def predict_records(records: list[dict[str, Any]]) -> RiskPredictionResponse:
    model = model_registry.champion_model
    metadata = model_registry.champion_metadata or {}
    if model is None:
        raise RuntimeError(MODEL_NOT_READY_MSG)

    features = list(metadata.get("features", []))
    if not features:
        raise RuntimeError("Risk model metadata does not define feature order.")

    feature_rows = build_late_shipment_features(records, features)
    frame = pd.DataFrame(feature_rows, columns=features)
    threshold = float(metadata.get("threshold", 0.5))

    probabilities = _late_probabilities(model, frame)
    predictions: list[RiskPredictionItem] = []

    for index, probability_late in enumerate(probabilities):
        late_probability = float(probability_late)
        on_time_probability = float(1.0 - late_probability)
        late_delivery_risk = int(late_probability >= threshold)
        risk_label = "yes" if late_delivery_risk else "no"

        predictions.append(
            RiskPredictionItem(
                index=index,
                late_delivery_risk=late_delivery_risk,
                risk_label=risk_label,
                delivery_label="Late Delivery Risk" if late_delivery_risk else "On Time",
                late_probability=round(late_probability, 6),
                on_time_probability=round(on_time_probability, 6),
                risk_probability=round(late_probability, 6),
                risk_percentage=round(late_probability * 100, 2),
                threshold=threshold,
            )
        )

    return RiskPredictionResponse(
        count=len(predictions),
        target=metadata.get("target", "Late_delivery_risk"),
        model_name=metadata.get("model_name"),
        model_version=metadata.get("version"),
        predictions=predictions,
    )


def _late_probabilities(model: Any, frame: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        probabilities = np.asarray(model.predict_proba(frame))
        if probabilities.ndim == 2 and probabilities.shape[1] > 1:
            return probabilities[:, 1]
        return probabilities.reshape(-1)

    predictions = np.asarray(model.predict(frame)).reshape(-1)
    return predictions.astype(float)
