"""Business service for production late-delivery risk prediction."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from ..config import settings
from ..core.model_registry import model_registry
from ..schemas.risk_predict_schema import (
    RiskModelInfo,
    RiskPredictionItem,
    RiskPredictionResponse,
    normalize_records,
)


class RiskPredictionService:
    """Runs inference against the production champion model."""

    shipping_mode_expected_days = {
        "Same Day": 0,
        "First Class": 1,
        "Second Class": 2,
        "Standard Class": 4,
    }

    def __init__(self) -> None:
        self._scaler_stats: dict[str, dict[str, float]] | None = None

<<<<<<< HEAD
def predict_late_shipment(payload: dict) -> dict:
    model = load_champion_model()
    metadata = load_champion_metadata()
    records = normalize_records(payload)
    feature_names = metadata.get("features", [])
    features = build_late_shipment_features(records, feature_names)

    if model is None:
        return {
            "count": len(records),
            "target": metadata.get("target", "Late_delivery_risk"),
            "predictions": [],
            "warning": "Champion model file was not found or could not be loaded.",
        }

    frame = pd.DataFrame(features)
    probabilities = _predict_probability(model, frame)
    threshold = float(metadata.get("threshold", 0.5))

    predictions = []
    for index, probability in enumerate(probabilities):
        risk = int(probability >= threshold)
        predictions.append(
            {
                "index": index,
                "late_delivery_risk": risk,
                "risk_label": "late" if risk else "on_time",
                "late_probability": float(probability),
                "threshold": threshold,
                "features": features[index],
            }
        )

    return {
        "count": len(predictions),
        "target": metadata.get("target", "Late_delivery_risk"),
        "feature_order": feature_names,
        "predictions": predictions,
    }
=======
    def get_model_info(self) -> RiskModelInfo:
        metadata = model_registry.champion_metadata or {}
        features = self._effective_feature_names(model_registry.champion_model, metadata)
        return RiskModelInfo(
            model_loaded=model_registry.champion_model is not None,
            metadata_loaded=bool(metadata),
            target=metadata.get("target", "Late_delivery_risk"),
            threshold=float(metadata.get("threshold", 0.5)),
            features=features,
            metadata={**metadata, "effective_features": features},
        )

    def predict(self, payload: dict[str, Any]) -> RiskPredictionResponse:
        model = model_registry.champion_model
        if model is None:
            raise RuntimeError("Production champion risk model is not loaded.")

        metadata = model_registry.champion_metadata or {}
        feature_names = self._effective_feature_names(model, metadata)
        if not feature_names:
            raise RuntimeError("Production champion metadata has no feature list.")

        records = normalize_records(payload)
        rows = [self._build_feature_row(record, feature_names) for record in records]
        missing = self._missing_required_values(rows, feature_names)
        if missing:
            raise ValueError(f"Missing required risk feature(s): {', '.join(missing)}")

        frame = pd.DataFrame(rows, columns=feature_names)
        frame = self._scale_engineered_features(frame, feature_names)
        probabilities = self._predict_probabilities(model, frame)
        threshold = float(metadata.get("threshold", 0.5))

        predictions: list[RiskPredictionItem] = []
        for index, probability in enumerate(probabilities):
            late_probability = float(probability["late"])
            on_time_probability = float(probability["on_time"])
            risk = int(late_probability >= threshold)
            risk_probability = late_probability if risk == 1 else max(0.0, 1.0 - on_time_probability)
            predictions.append(
                RiskPredictionItem(
                    index=index,
                    late_delivery_risk=risk,
                    risk_label="yes" if risk else "no",
                    delivery_label="late" if risk else "on_time",
                    late_probability=late_probability,
                    on_time_probability=on_time_probability,
                    risk_probability=risk_probability,
                    risk_percentage=round(risk_probability * 100.0, 2),
                    threshold=threshold,
                )
            )

        return RiskPredictionResponse(
            count=len(predictions),
            target=metadata.get("target", "Late_delivery_risk"),
            model_name=metadata.get("model_name") or metadata.get("alias"),
            model_version=metadata.get("version"),
            predictions=predictions,
        )

    def _build_feature_row(self, record: dict[str, Any], feature_names: list[str]) -> dict[str, Any]:
        row = dict(record)
        self._normalize_aliases(row)
        self._add_order_date_features(row)
        self._add_shipping_mode_features(row)
        self._add_engineered_risk_features(row)

        return {
            feature: self._coerce_feature_value(feature, row.get(feature))
            for feature in feature_names
        }

    def _normalize_aliases(self, row: dict[str, Any]) -> None:
        aliases = {
            "Latitude": ["latitude", "lat"],
            "Longitude": ["longitude", "lng", "lon"],
            "Shipping Mode": ["shipping_mode", "shippingMode"],
            "scheduled_days": [
                "Days for shipment (scheduled)",
                "days_for_shipment_scheduled",
                "scheduled_shipping_days",
            ],
        }
        for canonical, candidates in aliases.items():
            if row.get(canonical) not in (None, ""):
                continue
            for candidate in candidates:
                if row.get(candidate) not in (None, ""):
                    row[canonical] = row[candidate]
                    break

    def _add_order_date_features(self, row: dict[str, Any]) -> None:
        raw_date = (
            row.get("order_date")
            or row.get("order date (DateOrders)")
            or row.get("orderDate")
            or row.get("order_datetime")
        )
        if raw_date in (None, ""):
            return

        order_date = pd.to_datetime(raw_date, errors="coerce")
        if pd.isna(order_date):
            return

        row.setdefault("order_day", int(order_date.day))
        row.setdefault("order_dayofweek", int(order_date.dayofweek))
        row.setdefault("order_hour", int(order_date.hour))
        row.setdefault("order_is_weekend", int(order_date.dayofweek >= 5))

    def _add_shipping_mode_features(self, row: dict[str, Any]) -> None:
        mode_raw = str(row.get("Shipping Mode", "")).strip()
        mode = mode_raw.lower()
        if not mode:
            return

        row.setdefault("is_fast_shipping", int(mode in {"same day", "first class"}))
        row.setdefault("is_standard_shipping", int(mode == "standard class"))
        row.setdefault("is_first_class_mode", int(mode == "first class"))
        row.setdefault("is_second_class_mode", int(mode == "second class"))
        if row.get("expected_scheduled_days_by_mode") in (None, ""):
            row["expected_scheduled_days_by_mode"] = self.shipping_mode_expected_days.get(mode_raw)
        if row.get("scheduled_by_mode") in (None, ""):
            row["scheduled_by_mode"] = row.get("expected_scheduled_days_by_mode")

    def _add_engineered_risk_features(self, row: dict[str, Any]) -> None:
        latitude = self._to_float(row.get("Latitude"), 0.0)
        longitude = self._to_float(row.get("Longitude"), 0.0)
        row.setdefault("geo_distance_proxy", math.sqrt(latitude**2 + longitude**2))

        hour = self._to_float(row.get("order_hour"), 0.0)
        if row.get("order_period") in (None, ""):
            if hour <= 5:
                row["order_period"] = 0
            elif hour <= 11:
                row["order_period"] = 1
            elif hour <= 17:
                row["order_period"] = 2
            else:
                row["order_period"] = 3

        mode = str(row.get("Shipping Mode", "")).strip()
        expected_days = self.shipping_mode_expected_days.get(mode)
        if row.get("expected_scheduled_days_by_mode") in (None, ""):
            row["expected_scheduled_days_by_mode"] = expected_days
        if row.get("scheduled_days") in (None, ""):
            row["scheduled_days"] = expected_days
        if row.get("scheduled_by_mode") in (None, ""):
            row["scheduled_by_mode"] = row.get("expected_scheduled_days_by_mode")

        scheduled_days = self._to_float(row.get("scheduled_days"), 0.0)
        row.setdefault("is_medium_shipping", int(2 <= scheduled_days <= 3))

    def _coerce_feature_value(self, feature: str, value: Any) -> Any:
        if value in ("", None):
            return None
        if feature == "Shipping Mode":
            return str(value)
        numeric = pd.to_numeric(value, errors="coerce")
        if pd.isna(numeric):
            return value
        if feature.startswith("is_") or feature in {"order_day", "order_dayofweek", "order_hour", "order_is_weekend"}:
            return int(numeric)
        return float(numeric)

    def _to_float(self, value: Any, default: float) -> float:
        try:
            if value in ("", None) or pd.isna(value):
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    def _missing_required_values(self, rows: list[dict[str, Any]], feature_names: list[str]) -> list[str]:
        missing: set[str] = set()
        for row in rows:
            for feature in feature_names:
                if row.get(feature) is None:
                    missing.add(feature)
        return sorted(missing)

    def _predict_probabilities(self, model: Any, frame: pd.DataFrame) -> list[dict[str, float]]:
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(frame)
            classes = [int(item) for item in getattr(model, "classes_", [0, 1])]
            late_index = classes.index(1) if 1 in classes else min(1, len(classes) - 1)
            on_time_index = classes.index(0) if 0 in classes else 0

            result: list[dict[str, float]] = []
            for row in probabilities:
                late_probability = float(row[late_index])
                on_time_probability = float(row[on_time_index])
                if len(row) == 1:
                    on_time_probability = 1.0 - late_probability
                result.append(
                    {
                        "late": self._clamp_probability(late_probability),
                        "on_time": self._clamp_probability(on_time_probability),
                    }
                )
            return result

        predictions = model.predict(frame)
        return [
            {
                "late": self._clamp_probability(float(value)),
                "on_time": self._clamp_probability(1.0 - float(value)),
            }
            for value in predictions
        ]

    def _clamp_probability(self, value: float) -> float:
        return min(1.0, max(0.0, value))

    def _effective_feature_names(self, model: Any, metadata: dict[str, Any]) -> list[str]:
        if model is not None and hasattr(model, "get_booster"):
            try:
                feature_names = model.get_booster().feature_names
                if feature_names:
                    return list(feature_names)
            except Exception:
                pass
        if model is not None and hasattr(model, "feature_names_in_"):
            return [str(item) for item in model.feature_names_in_]
        return list(metadata.get("features", []))

    def _scale_engineered_features(self, frame: pd.DataFrame, feature_names: list[str]) -> pd.DataFrame:
        if "geo_distance_proxy" not in feature_names:
            return frame
        stats = self._load_scaler_stats(feature_names)
        if not stats:
            return frame

        scaled = frame.copy()
        for feature in feature_names:
            feature_stats = stats.get(feature)
            if not feature_stats:
                continue
            std = feature_stats["std"]
            if std == 0:
                continue
            scaled[feature] = (pd.to_numeric(scaled[feature], errors="coerce") - feature_stats["mean"]) / std
        return scaled

    def _load_scaler_stats(self, feature_names: list[str]) -> dict[str, dict[str, float]]:
        if self._scaler_stats is not None:
            return self._scaler_stats

        path = settings.dataset_root / "engineered" / "data_Classification.csv"
        if not path.exists():
            self._scaler_stats = {}
            return self._scaler_stats

        try:
            frame = pd.read_csv(path, usecols=feature_names)
        except Exception:
            self._scaler_stats = {}
            return self._scaler_stats

        self._scaler_stats = {}
        for feature in feature_names:
            values = pd.to_numeric(frame[feature], errors="coerce")
            self._scaler_stats[feature] = {
                "mean": float(values.mean()),
                "std": float(values.std(ddof=0)),
            }
        return self._scaler_stats
>>>>>>> prefix-app


risk_prediction_service = RiskPredictionService()


def get_model_info() -> dict[str, Any]:
    return risk_prediction_service.get_model_info().model_dump()


def predict_late_shipment(payload: dict[str, Any]) -> dict[str, Any]:
    return risk_prediction_service.predict(payload).model_dump()
