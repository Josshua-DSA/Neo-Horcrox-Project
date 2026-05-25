import numpy as np
import pandas as pd
import logging
from typing import List

from backend.core.model_registry import model_registry
from backend.schemas.forecast_supplier import SupplierInput, SupplierResponse, SupplierScore

logger = logging.getLogger(__name__)

NOT_READY = "Supplier model belum di-load. Jalankan pipeline notebook terlebih dahulu."

SUP_FEATURES = [
    'dept_enc', 'mode_enc', 'mkt_enc',
    'total_orders', 'late_rate', 'mean_delay', 'std_delay',
    'mean_profit', 'mean_profit_ratio', 'total_sales',
    'mean_qty', 'price_inconsistency_rate',
]


def _lookup_score(dept: str, mode: str, market: str):
    for row in (model_registry.supplier_lookup or []):
        if row.get("Department Name") == dept and row.get("Shipping Mode") == mode and row.get("Market") == market:
            return row
    return None


def _model_score(dept: str, mode: str, market: str, payload: SupplierInput) -> float:
    model    = model_registry.supplier_model
    metadata = model_registry.supplier_metadata or {}
    dept_enc = model_registry.supplier_dept_encoder
    mode_enc = model_registry.supplier_mode_encoder
    mkt_enc  = model_registry.supplier_mkt_encoder

    d = int(dept_enc.transform([dept])[0]) if dept in metadata.get("departments", []) else 0
    m = int(mode_enc.transform([mode])[0]) if mode in metadata.get("shipping_modes", []) else 0
    k = int(mkt_enc.transform([market])[0]) if market in metadata.get("markets", []) else 0

    row = pd.DataFrame([{
        'dept_enc': d, 'mode_enc': m, 'mkt_enc': k,
        'total_orders': 50, 'late_rate': 0.5, 'mean_delay': 0.0, 'std_delay': 1.0,
        'mean_profit': payload.order_item_product_price * 0.15,
        'mean_profit_ratio': 0.15,
        'total_sales': payload.order_item_product_price * payload.order_item_quantity,
        'mean_qty': payload.order_item_quantity,
        'price_inconsistency_rate': 0.0,
    }])[SUP_FEATURES]

    return float(np.clip(model.predict(row)[0], 0.0, 1.0))


def _label(score: float) -> str:
    if score >= 0.75: return "✅ Sangat Direkomendasikan"
    if score >= 0.55: return "👍 Direkomendasikan"
    if score >= 0.40: return "⚠️ Pertimbangkan Alternatif"
    return "❌ Tidak Direkomendasikan"


def recommend_supplier(payload: SupplierInput) -> SupplierResponse:
    if model_registry.supplier_model is None:
        raise RuntimeError(NOT_READY)

    lookup = model_registry.supplier_lookup or []
    candidates = [r for r in lookup if r.get("Market") == payload.market and r.get("Shipping Mode") == payload.shipping_mode]
    if not candidates:
        candidates = [r for r in lookup if r.get("Market") == payload.market]

    candidates = sorted(candidates, key=lambda r: r.get("supplier_score", 0), reverse=True)[:5]

    recommendations: List[SupplierScore] = []
    for row in candidates:
        score = float(row.get("supplier_score", 0.5))
        recommendations.append(SupplierScore(
            supplier_id=f"{row['Department Name']}_{row['Shipping Mode']}_{row['Market']}".replace(" ", "_"),
            department_name=row["Department Name"],
            score=round(score, 4),
            predicted_delay_risk=round(float(row.get("late_rate", 0.5)), 4),
            recommendation=_label(score),
        ))

    if payload.department_name not in {r.department_name for r in recommendations}:
        score = _model_score(payload.department_name, payload.shipping_mode, payload.market, payload)
        recommendations.insert(0, SupplierScore(
            supplier_id=f"{payload.department_name}_{payload.shipping_mode}_{payload.market}".replace(" ", "_"),
            department_name=payload.department_name,
            score=round(score, 4),
            predicted_delay_risk=0.5,
            recommendation=_label(score),
        ))

    return SupplierResponse(recommendations=recommendations)