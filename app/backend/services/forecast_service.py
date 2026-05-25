import numpy as np
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List

from backend.core.model_registry import model_registry
from backend.schemas.forecast_supplier import ForecastInput, ForecastResponse, ForecastPoint

logger = logging.getLogger(__name__)

NOT_READY = "Forecast model belum di-load. Jalankan pipeline notebook terlebih dahulu."

FC_FEATURES = [
    'cat_encoded', 'mkt_encoded',
    'dayofweek', 'month', 'quarter', 'is_weekend', 'year',
    'lag_1', 'lag_7', 'lag_14', 'lag_30',
    'roll_mean_7', 'roll_mean_14', 'roll_mean_30',
    'roll_std_7', 'roll_std_14', 'roll_std_30',
    'roll_max_7', 'roll_max_14', 'roll_max_30',
    'order_count', 'total_qty',
]


def _get_group_stats(category: str, market: str) -> dict:
    stats = model_registry.forecast_group_stats or []
    for row in stats:
        if row.get("Category Name") == category and row.get("Market") == market:
            return row
    if stats:
        return {
            "mean_sales": np.mean([r.get("mean_sales", 100) for r in stats]),
            "std_sales":  np.mean([r.get("std_sales", 20)  for r in stats]),
            "mean_qty":   np.mean([r.get("mean_qty", 2)    for r in stats]),
        }
    return {"mean_sales": 100.0, "std_sales": 20.0, "mean_qty": 2.0}


def predict_forecast(payload: ForecastInput) -> ForecastResponse:
    model       = model_registry.forecast_model
    cat_encoder = model_registry.forecast_cat_encoder
    mkt_encoder = model_registry.forecast_mkt_encoder
    metadata    = model_registry.forecast_metadata or {}

    if model is None:
        raise RuntimeError(NOT_READY)

    known_cats = metadata.get("categories", [])
    known_mkts = metadata.get("markets", [])

    if payload.category_name not in known_cats:
        raise ValueError(f"Category '{payload.category_name}' tidak dikenal. Tersedia: {known_cats}")
    if payload.market not in known_mkts:
        raise ValueError(f"Market '{payload.market}' tidak dikenal. Tersedia: {known_mkts}")

    cat_enc = int(cat_encoder.transform([payload.category_name])[0])
    mkt_enc = int(mkt_encoder.transform([payload.market])[0])

    stats      = _get_group_stats(payload.category_name, payload.market)
    mean_sales = stats.get("mean_sales", 100.0)
    std_sales  = stats.get("std_sales", 20.0)
    mean_qty   = stats.get("mean_qty", 2.0)

    start_date = datetime.today()
    if payload.order_year and payload.order_month:
        start_date = datetime(payload.order_year, payload.order_month, 1)

    history = [mean_sales] * 30
    forecast_points: List[ForecastPoint] = []

    for i in range(payload.periods):
        current_date = start_date + timedelta(days=i)

        row = pd.DataFrame([{
            'cat_encoded':   cat_enc,
            'mkt_encoded':   mkt_enc,
            'dayofweek':     current_date.weekday(),
            'month':         current_date.month,
            'quarter':       (current_date.month - 1) // 3 + 1,
            'is_weekend':    int(current_date.weekday() >= 5),
            'year':          current_date.year,
            'lag_1':         history[-1],
            'lag_7':         history[-7]  if len(history) >= 7  else mean_sales,
            'lag_14':        history[-14] if len(history) >= 14 else mean_sales,
            'lag_30':        history[-30] if len(history) >= 30 else mean_sales,
            'roll_mean_7':   np.mean(history[-7:]),
            'roll_mean_14':  np.mean(history[-14:]),
            'roll_mean_30':  np.mean(history[-30:]),
            'roll_std_7':    np.std(history[-7:])  if len(history) >= 7  else std_sales,
            'roll_std_14':   np.std(history[-14:]) if len(history) >= 14 else std_sales,
            'roll_std_30':   np.std(history[-30:]) if len(history) >= 30 else std_sales,
            'roll_max_7':    np.max(history[-7:]),
            'roll_max_14':   np.max(history[-14:]),
            'roll_max_30':   np.max(history[-30:]),
            'order_count':   max(1, round(mean_qty)),
            'total_qty':     round(mean_qty),
        }])[FC_FEATURES]

        pred  = max(0.0, float(model.predict(row)[0]))
        std7  = np.std(history[-7:]) if len(history) >= 7 else std_sales

        forecast_points.append(ForecastPoint(
            date=current_date.strftime("%Y-%m-%d"),
            predicted_sales=round(pred, 2),
            lower_bound=round(max(0.0, pred - 1.5 * std7), 2),
            upper_bound=round(pred + 1.5 * std7, 2),
        ))
        history.append(pred)

    return ForecastResponse(
        category_name=payload.category_name,
        market=payload.market,
        periods=payload.periods,
        forecast=forecast_points,
    )