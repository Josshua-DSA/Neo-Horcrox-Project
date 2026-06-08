"""Inference entry points for late-shipment risk."""

from __future__ import annotations

from typing import Any

import pandas as pd

from ..features.build_features import build_late_shipment_features
from ..utils.constants import LATE_SHIPMENT_FEATURES, TARGET_LATE_SHIPMENT


def predict(model: Any, frame: pd.DataFrame):
    return model.predict(frame)


def predict_probability(model: Any, frame: pd.DataFrame):
    if hasattr(model, "predict_proba"):
        return model.predict_proba(frame)[:, 1]
    return [float(value) for value in model.predict(frame)]


def predict_records(
    model: Any,
    records: list[dict[str, Any]],
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata = metadata or {}
    features = metadata.get("features") or LATE_SHIPMENT_FEATURES
    threshold = float(metadata.get("threshold", 0.5))
    frame = pd.DataFrame(build_late_shipment_features(records, features))
    probabilities = predict_probability(model, frame)

    predictions = []
    for index, probability in enumerate(probabilities):
        risk = int(float(probability) >= threshold)
        predictions.append(
            {
                "index": index,
                "late_delivery_risk": risk,
                "risk_label": "late" if risk else "on_time",
                "late_probability": float(probability),
                "threshold": threshold,
            }
        )

    return {
        "count": len(predictions),
        "target": metadata.get("target", TARGET_LATE_SHIPMENT),
        "features": features,
        "predictions": predictions,
    }
