"""Demand forecasting service backed by forecast model artifacts."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from ..core.model_registry import model_registry
from ..schemas.forecast_schema import ForecastInput, ForecastPoint, ForecastResponse


class ForecastService:
    """Produces daily demand forecasts for a category and market."""

    fallback_stats = {"mean_sales": 100.0, "std_sales": 20.0, "mean_qty": 2.0}

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "model_loaded": model_registry.forecast_model is not None,
            "cat_encoder_loaded": model_registry.forecast_cat_encoder is not None,
            "market_encoder_loaded": model_registry.forecast_mkt_encoder is not None,
            "metadata_loaded": bool(model_registry.forecast_metadata),
            "group_stats_loaded": bool(model_registry.forecast_group_stats),
        }

    def categories(self) -> list[str]:
        return list((model_registry.forecast_metadata or {}).get("categories", []))

    def markets(self) -> list[str]:
        return list((model_registry.forecast_metadata or {}).get("markets", []))

    def metadata(self) -> dict[str, Any]:
        return dict(model_registry.forecast_metadata or {})

    def predict(self, payload: ForecastInput) -> ForecastResponse:
        model = model_registry.forecast_model
        cat_encoder = model_registry.forecast_cat_encoder
        market_encoder = model_registry.forecast_mkt_encoder
        metadata = model_registry.forecast_metadata or {}

        if model is None or cat_encoder is None or market_encoder is None:
            raise RuntimeError("Forecast artifacts are not fully loaded.")

        known_categories = metadata.get("categories", [])
        known_markets = metadata.get("markets", [])
        if payload.category_name not in known_categories:
            raise ValueError(f"Unknown category '{payload.category_name}'.")
        if payload.market not in known_markets:
            raise ValueError(f"Unknown market '{payload.market}'.")

        features = metadata.get("features", [])
        category_encoded = int(cat_encoder.transform([payload.category_name])[0])
        market_encoded = int(market_encoder.transform([payload.market])[0])
        stats = self._get_group_stats(payload.category_name, payload.market)

        mean_sales = float(stats.get("mean_sales", self.fallback_stats["mean_sales"]))
        std_sales = float(stats.get("std_sales", self.fallback_stats["std_sales"]))
        mean_qty = float(stats.get("mean_qty", self.fallback_stats["mean_qty"]))

        start_date = self._start_date(payload)
        history = [mean_sales] * 30
        forecast_points: list[ForecastPoint] = []

        for offset in range(payload.periods):
            current_date = start_date + timedelta(days=offset)
            feature_row = self._build_feature_row(
                current_date=current_date,
                category_encoded=category_encoded,
                market_encoded=market_encoded,
                history=history,
                mean_sales=mean_sales,
                std_sales=std_sales,
                mean_qty=mean_qty,
            )
            frame = pd.DataFrame([feature_row])
            if features:
                frame = frame[features]

            prediction = max(0.0, float(model.predict(frame)[0]))
            std7 = float(np.std(history[-7:])) if len(history) >= 7 else std_sales
            forecast_points.append(
                ForecastPoint(
                    date=current_date.strftime("%Y-%m-%d"),
                    predicted_sales=round(prediction, 2),
                    lower_bound=round(max(0.0, prediction - 1.5 * std7), 2),
                    upper_bound=round(prediction + 1.5 * std7, 2),
                )
            )
            history.append(prediction)

        return ForecastResponse(
            category_name=payload.category_name,
            market=payload.market,
            periods=payload.periods,
            forecast=forecast_points,
            model_version=str(metadata.get("trained_at") or metadata.get("version") or "0.1.0"),
        )

    def _start_date(self, payload: ForecastInput) -> datetime:
        if payload.order_year and payload.order_month:
            return datetime(payload.order_year, payload.order_month, 1)
        return datetime.today()

    def _get_group_stats(self, category: str, market: str) -> dict[str, Any]:
        stats = model_registry.forecast_group_stats or []
        for row in stats:
            if row.get("Category Name") == category and row.get("Market") == market:
                return row
        if not stats:
            return dict(self.fallback_stats)
        return {
            "mean_sales": float(np.mean([row.get("mean_sales", self.fallback_stats["mean_sales"]) for row in stats])),
            "std_sales": float(np.mean([row.get("std_sales", self.fallback_stats["std_sales"]) for row in stats])),
            "mean_qty": float(np.mean([row.get("mean_qty", self.fallback_stats["mean_qty"]) for row in stats])),
        }

    def _build_feature_row(
        self,
        current_date: datetime,
        category_encoded: int,
        market_encoded: int,
        history: list[float],
        mean_sales: float,
        std_sales: float,
        mean_qty: float,
    ) -> dict[str, Any]:
        return {
            "cat_encoded": category_encoded,
            "mkt_encoded": market_encoded,
            "dayofweek": current_date.weekday(),
            "month": current_date.month,
            "quarter": (current_date.month - 1) // 3 + 1,
            "is_weekend": int(current_date.weekday() >= 5),
            "year": current_date.year,
            "lag_1": history[-1],
            "lag_7": history[-7] if len(history) >= 7 else mean_sales,
            "lag_14": history[-14] if len(history) >= 14 else mean_sales,
            "lag_30": history[-30] if len(history) >= 30 else mean_sales,
            "roll_mean_7": float(np.mean(history[-7:])),
            "roll_mean_14": float(np.mean(history[-14:])),
            "roll_mean_30": float(np.mean(history[-30:])),
            "roll_std_7": float(np.std(history[-7:])) if len(history) >= 7 else std_sales,
            "roll_std_14": float(np.std(history[-14:])) if len(history) >= 14 else std_sales,
            "roll_std_30": float(np.std(history[-30:])) if len(history) >= 30 else std_sales,
            "roll_max_7": float(np.max(history[-7:])),
            "roll_max_14": float(np.max(history[-14:])),
            "roll_max_30": float(np.max(history[-30:])),
            "order_count": max(1, round(mean_qty)),
            "total_qty": round(mean_qty),
        }


forecast_service = ForecastService()


def get_forecast_status() -> dict[str, Any]:
    return forecast_service.health()
