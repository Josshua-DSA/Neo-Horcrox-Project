"""Read-only supplier selection APIs backed by CSV/JSON artifacts."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd

from backend.core.config import settings
from backend.schemas.supplier_selection_schema import (
    SupplierCandidate,
    SupplierCandidateDetail,
    SupplierCategory,
    SupplierHealth,
    SupplierWeight,
)
from backend.services.dashboard_dataset import dashboard_dataset_repository


class SupplierSelectionService:
    def health(self) -> SupplierHealth:
        full = self._full_results()
        categories = self.categories()
        return SupplierHealth(
            status="ok" if not full.empty else "missing_data",
            data_loaded=not full.empty,
            total_categories=len(categories),
            total_candidates=int(len(full)),
            source_files={
                "full_result": str(settings.supplier_full_result_path),
                "primary_per_category": str(settings.supplier_primary_path),
                "summary": str(settings.supplier_summary_path),
                "weights": str(settings.supplier_weights_path),
            },
        )

    def categories(self) -> list[SupplierCategory]:
        primary = self._primary_results()
        full = self._full_results()
        if full.empty:
            return []

        counts = full.groupby("category_id", dropna=False)["candidate_id"].count()
        primary_by_category = {}
        if not primary.empty:
            for _, primary_row in primary.iterrows():
                primary_by_category[_string_id(primary_row.get("category_id"))] = primary_row

        categories: list[SupplierCategory] = []

        grouped = full.groupby(["category_id", "category_name"], dropna=False).size().reset_index(name="count")
        for _, row in grouped.sort_values("category_name").iterrows():
            category_id = _string_id(row.get("category_id"))
            if not category_id:
                continue
            primary_row = primary_by_category.get(category_id)
            categories.append(
                SupplierCategory(
                    category_id=category_id,
                    category_name=str(row.get("category_name") or "Unknown"),
                    total_candidates=int(counts.get(row.get("category_id"), 0) or row.get("count") or 0),
                    primary_candidate_id=_string_id(primary_row.get("candidate_id")) if primary_row is not None else None,
                    primary_candidate_name=_clean_text(primary_row.get("candidate_name")) if primary_row is not None else None,
                )
            )

        deduped: dict[str, SupplierCategory] = {}
        for category in categories:
            deduped[category.category_id] = category
        return list(deduped.values())

    def products(
        self,
        category_id: str,
        limit: int = 25,
        include_rejected: bool = True,
    ) -> list[SupplierCandidate]:
        full = self._full_results()
        if full.empty:
            return []

        matches = full[full["category_id"].map(_string_id) == str(category_id)]
        if not include_rejected and "prequalified" in matches.columns:
            matches = matches[matches["prequalified"].map(_coerce_bool)]

        matches = matches.sort_values(
            by=["final_rank_in_category", "topsis_score"],
            ascending=[True, False],
            na_position="last",
        ).head(limit)

        return [self._candidate_from_row(row) for _, row in matches.iterrows()]

    def product_detail(self, candidate_id: str) -> SupplierCandidateDetail | None:
        full = self._full_results()
        if full.empty:
            return None

        matches = full[full["candidate_id"].map(_string_id) == str(candidate_id)]
        if matches.empty:
            return None

        row = matches.iloc[0]
        candidate = self._candidate_from_row(row)
        related = [
            item
            for item in self.products(candidate.category_id, limit=5, include_rejected=True)
            if item.candidate_id != candidate.candidate_id
        ]
        profile = self._dataset_profile(row)

        return SupplierCandidateDetail(
            candidate=candidate.model_dump(),
            related_candidates=related,
            dataset_profile=profile,
            forecast_input=profile.get("forecast_input", {}),
            risk_input=profile.get("risk_input", {}),
        )

    def summary(self) -> dict[str, Any]:
        summary = _read_json(str(settings.supplier_summary_path))
        if summary:
            return summary
        full = self._full_results()
        return {
            "total_categories": int(full["category_id"].nunique()) if not full.empty else 0,
            "total_candidates": int(len(full)),
            "prequalified_candidates": int(full.get("prequalified", pd.Series(dtype=bool)).map(_coerce_bool).sum())
            if not full.empty
            else 0,
        }

    def weights(self) -> list[SupplierWeight]:
        weights = _read_csv(str(settings.supplier_weights_path))
        if weights.empty:
            return []
        return [
            SupplierWeight(criteria=str(row.get("criteria")), weight=float(row.get("weight") or 0))
            for _, row in weights.iterrows()
        ]

    def _candidate_from_row(self, row: pd.Series) -> SupplierCandidate:
        return SupplierCandidate(
            candidate_id=_string_id(row.get("candidate_id")),
            candidate_name=str(row.get("candidate_name") or "Unknown"),
            category_id=_string_id(row.get("category_id")),
            category_name=str(row.get("category_name") or "Unknown"),
            final_rank_in_category=_optional_int(row.get("final_rank_in_category")),
            recommendation=_clean_text(row.get("recommendation")),
            risk_level=_clean_text(row.get("risk_level")),
            risk_score=_optional_float(row.get("risk_score")),
            topsis_score=_optional_float(row.get("topsis_score")),
            total_orders=_optional_int(row.get("total_orders")),
            total_sales=_optional_float(row.get("total_sales")),
            total_profit=_optional_float(row.get("total_profit")),
            late_rate=_optional_float(row.get("late_rate")),
            prequalified=_coerce_bool(row.get("prequalified")),
            compliance_passed=_coerce_bool(row.get("compliance_passed")),
            metrics=_clean_dict(row.to_dict()),
        )

    def _dataset_profile(self, row: pd.Series) -> dict[str, Any]:
        candidate_id = _string_id(row.get("candidate_id"))
        category_name = str(row.get("category_name") or "")
        raw = self._raw_dataset()

        product_rows = pd.DataFrame()
        if not raw.empty and "Product Card Id" in raw.columns:
            product_rows = raw[raw["Product Card Id"].map(_string_id) == candidate_id].copy()

        if product_rows.empty:
            forecast_input = {
                "category_name": category_name,
                "market": "USCA",
                "periods": 14,
            }
            return {
                "summary": {
                    "total_orders": _optional_int(row.get("total_orders")) or 0,
                    "total_revenue": _optional_float(row.get("total_sales")) or 0.0,
                    "total_quantity": _optional_int(row.get("total_quantity")) or 0,
                    "late_rate": _optional_float(row.get("late_rate")) or 0.0,
                },
                "trend": [],
                "shipping_modes": [],
                "forecast_input": forecast_input,
                "risk_input": {},
            }

        product_rows["order_date"] = pd.to_datetime(
            product_rows.get("order date (DateOrders)"),
            errors="coerce",
        )
        latest = product_rows.sort_values("order_date", na_position="first").iloc[-1].to_dict()
        market = _mode_or_default(product_rows.get("Market"), "USCA")
        max_date = product_rows["order_date"].dropna().max()

        forecast_input = {
            "category_name": category_name or _mode_or_default(product_rows.get("Category Name"), ""),
            "market": market,
            "periods": 14,
        }
        if pd.notna(max_date):
            forecast_input["order_year"] = int(max_date.year)
            forecast_input["order_month"] = int(max_date.month)

        summary = {
            "total_orders": int(product_rows["Order Id"].nunique()) if "Order Id" in product_rows else int(len(product_rows)),
            "total_revenue": round(float(product_rows.get("Sales", pd.Series(dtype=float)).sum()), 2),
            "total_quantity": int(product_rows.get("Order Item Quantity", pd.Series(dtype=float)).sum()),
            "total_profit": round(float(product_rows.get("Order Profit Per Order", pd.Series(dtype=float)).sum()), 2),
            "late_rate": round(float(product_rows.get("Late_delivery_risk", pd.Series(dtype=float)).mean()), 4),
        }

        # Build risk_input explicitly with exact field names expected by
        # build_late_shipment_features. Geo values are unique per product
        # and drive model variance. order_hour is left None so the frontend
        # injects the current hour at click-time; order_period is then derived
        # automatically in the backend feature builder.
        lat = _optional_float(latest.get("Latitude"))
        lon = _optional_float(latest.get("Longitude"))
        mode = _clean_text(latest.get("Shipping Mode")) or "Standard Class"
        sched = _optional_int(latest.get("Days for shipment (scheduled)"))

        risk_input: dict[str, Any] = {
            # Geo — unique per product; drives geo_distance_proxy in feature builder
            "Latitude": lat,
            "Longitude": lon,
            # Shipping — will be overridden by the shipping tab the user selects
            "Shipping Mode": mode,
            "Days for shipment (scheduled)": sched,
            # Intentionally None — frontend injects order_hour = new Date().getHours()
            # at predict-click time; build_late_shipment_features derives order_period.
            "order_hour": None,
            "order_period": None,
        }

        return {
            "summary": summary,
            "trend": self._trend(product_rows),
            "shipping_modes": self._shipping_modes(product_rows),
            "forecast_input": forecast_input,
            "risk_input": risk_input,
        }

    def _trend(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        if "order_date" not in frame or frame["order_date"].dropna().empty:
            return []
        working = frame.dropna(subset=["order_date"]).copy()
        working["month"] = working["order_date"].dt.to_period("M").astype(str)
        grouped = working.groupby("month", dropna=False).agg(
            revenue=("Sales", "sum"),
            quantity=("Order Item Quantity", "sum"),
            orders=("Order Id", "nunique"),
        )
        return [
            {
                "date": str(index),
                "revenue": round(float(row["revenue"]), 2),
                "quantity": int(row["quantity"]),
                "orders": int(row["orders"]),
            }
            for index, row in grouped.tail(12).iterrows()
        ]

    def _shipping_modes(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        if "Shipping Mode" not in frame:
            return []
        grouped = frame.groupby("Shipping Mode", dropna=False).agg(
            order_count=("Order Id", "nunique"),
            scheduled_days=("Days for shipment (scheduled)", "mean"),
            real_days=("Days for shipping (real)", "mean"),
            late_rate=("Late_delivery_risk", "mean"),
        )
        return [
            {
                "mode": str(index),
                "order_count": int(row["order_count"]),
                "scheduled_days": round(float(row["scheduled_days"]), 2),
                "real_days": round(float(row["real_days"]), 2),
                "late_rate": round(float(row["late_rate"]), 4),
            }
            for index, row in grouped.sort_values("order_count", ascending=False).iterrows()
        ]

    def _full_results(self) -> pd.DataFrame:
        return _read_csv(str(settings.supplier_full_result_path))

    def _primary_results(self) -> pd.DataFrame:
        return _read_csv(str(settings.supplier_primary_path))

    def _raw_dataset(self) -> pd.DataFrame:
        columns = [
            "Type",
            "Days for shipping (real)",
            "Days for shipment (scheduled)",
            "Sales per customer",
            "Late_delivery_risk",
            "Category Name",
            "Customer Segment",
            "Department Name",
            "Latitude",
            "Longitude",
            "Market",
            "Order Country",
            "order date (DateOrders)",
            "Order Id",
            "Order Item Quantity",
            "Sales",
            "Order Profit Per Order",
            "Order Region",
            "Order State",
            "Order Status",
            "Product Card Id",
            "Product Name",
            "Product Price",
            "shipping date (DateOrders)",
            "Shipping Mode",
        ]
        return dashboard_dataset_repository.load(columns)


@lru_cache(maxsize=8)
def _read_csv(path_text: str) -> pd.DataFrame:
    path = Path(path_text)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@lru_cache(maxsize=8)
def _read_json(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _clean_dict(data: dict[str, Any]) -> dict[str, Any]:
    return {str(key): _clean_value(value) for key, value in data.items()}


def _clean_value(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _clean_text(value: Any) -> str | None:
    cleaned = _clean_value(value)
    return None if cleaned is None else str(cleaned)


def _string_id(value: Any) -> str:
    number = _optional_int(value)
    if number is not None:
        return str(number)
    cleaned = _clean_value(value)
    return "" if cleaned is None else str(cleaned)


def _optional_float(value: Any) -> float | None:
    cleaned = _clean_value(value)
    if cleaned is None or cleaned == "":
        return None
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def _optional_int(value: Any) -> int | None:
    number = _optional_float(value)
    if number is None:
        return None
    return int(number)


def _coerce_bool(value: Any) -> bool:
    cleaned = _clean_value(value)
    if isinstance(cleaned, bool):
        return cleaned
    return str(cleaned).strip().lower() in {"true", "1", "yes", "passed"}


def _mode_or_default(series: pd.Series | None, default: str) -> str:
    if series is None:
        return default
    values = series.dropna().astype(str)
    if values.empty:
        return default
    return str(values.mode().iloc[0])


supplier_selection_service = SupplierSelectionService()
