"""Read-only supplier selection service backed by ranking CSV/JSON outputs."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import settings
from ..schemas.supplier_selection_schema import SupplierCandidate, SupplierCategory
from .dashboard_dataset import dashboard_dataset_repository


class SupplierSelectionService:
    """Exposes supplier ranking artifacts without training or inference."""

    def __init__(self) -> None:
        self.full_result_path = settings.supplier_full_result_path
        self.primary_path = settings.supplier_primary_path
        self.summary_path = settings.supplier_summary_path
        self.weights_path = settings.supplier_weights_path
        self._full_rows: list[dict[str, Any]] | None = None
        self._primary_rows: list[dict[str, Any]] | None = None
        self._summary: dict[str, Any] | None = None
        self._weights: list[dict[str, Any]] | None = None
        self._raw_dataset: pd.DataFrame | None = None

    def health(self) -> dict[str, Any]:
        full_rows = self._load_full_rows()
        categories = {str(row.get("category_id", "")) for row in full_rows}
        return {
            "status": "ok" if full_rows else "missing_data",
            "data_loaded": bool(full_rows),
            "total_categories": len(categories),
            "total_candidates": len(full_rows),
            "source_files": {
                "full_result": str(self.full_result_path),
                "primary": str(self.primary_path),
                "summary": str(self.summary_path),
                "weights": str(self.weights_path),
            },
        }

    def categories(self) -> list[SupplierCategory]:
        full_rows = self._load_full_rows()
        primary_by_category = {
            str(row.get("category_id")): row
            for row in self._load_primary_rows()
        }
        grouped: dict[str, dict[str, Any]] = {}

        for row in full_rows:
            category_id = str(row.get("category_id"))
            if category_id not in grouped:
                primary = primary_by_category.get(category_id, {})
                grouped[category_id] = {
                    "category_id": category_id,
                    "category_name": str(row.get("category_name", "")),
                    "total_candidates": 0,
                    "primary_candidate_id": self._to_optional_str(primary.get("candidate_id")),
                    "primary_candidate_name": self._to_optional_str(primary.get("candidate_name")),
                }
            grouped[category_id]["total_candidates"] += 1

        return [
            SupplierCategory(**item)
            for item in sorted(grouped.values(), key=lambda value: value["category_name"])
        ]

    def products_by_category(
        self,
        category_id: str,
        limit: int = 20,
        include_rejected: bool = False,
    ) -> list[SupplierCandidate]:
        rows = [
            row for row in self._load_full_rows()
            if str(row.get("category_id")) == str(category_id)
        ]
        if not rows:
            raise LookupError(f"Category {category_id} was not found.")

        if not include_rejected:
            accepted = [
                row for row in rows
                if self._to_bool(row.get("prequalified")) and self._to_bool(row.get("compliance_passed"))
            ]
            if accepted:
                rows = accepted

        rows = sorted(rows, key=lambda row: self._to_int(row.get("final_rank_in_category"), 999999))
        return [self._candidate_from_row(row) for row in rows[:limit]]

    def product_profile(self, candidate_id: str) -> dict[str, Any]:
        matches = [
            row for row in self._load_full_rows()
            if str(row.get("candidate_id")) == str(candidate_id)
        ]
        if not matches:
            raise LookupError(f"Candidate {candidate_id} was not found.")

        matches = sorted(matches, key=lambda row: self._to_int(row.get("final_rank_in_category"), 999999))
        candidate = self._convert_row(matches[0])
        related = self.products_by_category(str(matches[0].get("category_id")), limit=10, include_rejected=True)
        return {
            "candidate": candidate,
            "related_candidates": [item.model_dump() for item in related],
            "dataset_profile": self._dataset_profile(candidate),
        }

    def columns(self) -> dict[str, Any]:
        rows = self._load_full_rows()
        return {
            "columns": list(rows[0].keys()) if rows else [],
            "total_columns": len(rows[0].keys()) if rows else 0,
        }

    def preview_by_category(self, category_id: str, limit: int = 5) -> dict[str, Any]:
        rows = [
            self._convert_row(row)
            for row in self._load_full_rows()
            if str(row.get("category_id")) == str(category_id)
        ]
        if not rows:
            raise LookupError(f"Category {category_id} was not found.")
        return {
            "total": len(rows),
            "columns": list(rows[0].keys()),
            "data": rows[:limit],
        }

    def summary(self) -> dict[str, Any]:
        if self._summary is None:
            self._summary = self._read_json(self.summary_path, default={})
        return dict(self._summary)

    def weights(self) -> list[dict[str, Any]]:
        if self._weights is None:
            self._weights = [self._convert_row(row) for row in self._read_csv(self.weights_path)]
        return list(self._weights)

    def _load_full_rows(self) -> list[dict[str, Any]]:
        if self._full_rows is None:
            self._full_rows = self._read_csv(self.full_result_path)
        return self._full_rows

    def _load_primary_rows(self) -> list[dict[str, Any]]:
        if self._primary_rows is None:
            self._primary_rows = self._read_csv(self.primary_path)
        return self._primary_rows

    def _read_csv(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return [dict(row) for row in csv.DictReader(file)]

    def _read_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _candidate_from_row(self, row: dict[str, Any]) -> SupplierCandidate:
        converted = self._convert_row(row)
        return SupplierCandidate(
            candidate_id=str(converted.get("candidate_id")),
            candidate_name=str(converted.get("candidate_name")),
            category_id=str(converted.get("category_id")),
            category_name=str(converted.get("category_name")),
            final_rank_in_category=converted.get("final_rank_in_category"),
            recommendation=converted.get("recommendation"),
            risk_level=converted.get("risk_level"),
            risk_score=converted.get("risk_score"),
            topsis_score=converted.get("topsis_score"),
            total_orders=converted.get("total_orders"),
            total_sales=converted.get("total_sales"),
            total_profit=converted.get("total_profit"),
            late_rate=converted.get("late_rate"),
            prequalified=converted.get("prequalified"),
            compliance_passed=converted.get("compliance_passed"),
            metrics=converted,
        )

    def _dataset_profile(self, candidate: dict[str, Any]) -> dict[str, Any]:
        frame = self._load_raw_dataset()
        candidate_id = candidate.get("candidate_id")
        category_name = candidate.get("category_name")
        if frame.empty:
            return self._fallback_dataset_profile(candidate)

        product_rows = frame[frame["Product Card Id"].astype(str) == str(candidate_id)]
        if product_rows.empty and category_name:
            product_rows = frame[frame["Category Name"].astype(str) == str(category_name)]
        if product_rows.empty:
            return self._fallback_dataset_profile(candidate)

        product_rows = product_rows.copy()
        product_rows["order_date"] = pd.to_datetime(product_rows["order date (DateOrders)"], errors="coerce")
        latest = product_rows.sort_values("order_date", ascending=False).iloc[0].to_dict()
        market = self._mode(product_rows, "Market")
        shipping_modes = self._shipping_modes(product_rows)

        return {
            "summary": {
                "total_revenue": round(float(product_rows["Sales"].sum()), 2),
                "total_quantity": int(product_rows["Order Item Quantity"].sum()),
                "total_orders": int(product_rows["Order Id"].nunique()),
                "avg_late_rate": round(float(product_rows["Late_delivery_risk"].mean()), 4),
                "market": market,
            },
            "risk_input": {
                "Latitude": self._safe_float(latest.get("Latitude")),
                "Longitude": self._safe_float(latest.get("Longitude")),
                "order_date": str(latest.get("order date (DateOrders)") or ""),
                "scheduled_days": self._safe_float(latest.get("Days for shipment (scheduled)")),
                "Shipping Mode": str(latest.get("Shipping Mode") or ""),
            },
            "forecast_input": {
                "category_name": str(category_name or latest.get("Category Name") or ""),
                "market": str(market or latest.get("Market") or ""),
                "periods": 30,
            },
            "shipping_modes": shipping_modes,
            "trend": self._monthly_trend(product_rows),
        }

    def _fallback_dataset_profile(self, candidate: dict[str, Any]) -> dict[str, Any]:
        return {
            "summary": {
                "total_revenue": candidate.get("total_sales") or 0,
                "total_quantity": candidate.get("total_quantity") or 0,
                "total_orders": candidate.get("total_orders") or 0,
                "avg_late_rate": candidate.get("late_rate") or 0,
                "market": None,
            },
            "risk_input": {},
            "forecast_input": {
                "category_name": candidate.get("category_name"),
                "market": None,
                "periods": 30,
            },
            "shipping_modes": [],
            "trend": [],
        }

    def _load_raw_dataset(self) -> pd.DataFrame:
        if self._raw_dataset is not None:
            return self._raw_dataset
        columns = [
            "Product Card Id",
            "Category Name",
            "Sales",
            "Order Item Quantity",
            "Order Id",
            "Late_delivery_risk",
            "Latitude",
            "Longitude",
            "order date (DateOrders)",
            "Days for shipment (scheduled)",
            "Shipping Mode",
            "Market",
        ]
        self._raw_dataset = dashboard_dataset_repository.load(columns)
        return self._raw_dataset

    def _mode(self, frame: pd.DataFrame, column: str) -> str | None:
        if column not in frame.columns or frame.empty:
            return None
        modes = frame[column].dropna().astype(str).mode()
        return str(modes.iloc[0]) if not modes.empty else None

    def _shipping_modes(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        if "Shipping Mode" not in frame.columns:
            return []
        grouped = frame.groupby("Shipping Mode", dropna=False).agg(
            scheduled_days=("Days for shipment (scheduled)", "median"),
            total_orders=("Order Id", "nunique"),
            late_rate=("Late_delivery_risk", "mean"),
        )
        return [
            {
                "mode": str(index),
                "scheduled_days": self._safe_float(row["scheduled_days"]),
                "total_orders": int(row["total_orders"]),
                "late_rate": round(float(row["late_rate"]), 4),
            }
            for index, row in grouped.sort_values("total_orders", ascending=False).iterrows()
        ]

    def _monthly_trend(self, frame: pd.DataFrame) -> list[dict[str, Any]]:
        if "order_date" not in frame.columns:
            return []
        valid = frame.dropna(subset=["order_date"]).copy()
        if valid.empty:
            return []
        valid["month"] = valid["order_date"].dt.to_period("M").astype(str)
        grouped = valid.groupby("month").agg(
            revenue=("Sales", "sum"),
            quantity=("Order Item Quantity", "sum"),
        )
        return [
            {
                "date": str(index),
                "revenue": round(float(row["revenue"]), 2),
                "quantity": int(row["quantity"]),
            }
            for index, row in grouped.tail(12).iterrows()
        ]

    def _safe_float(self, value: Any) -> float | None:
        try:
            if value in (None, "") or pd.isna(value):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _convert_row(self, row: dict[str, Any]) -> dict[str, Any]:
        converted: dict[str, Any] = {}
        for key, value in row.items():
            if value is None or value == "":
                converted[key] = None
            elif str(value).lower() in {"true", "false"}:
                converted[key] = self._to_bool(value)
            else:
                converted[key] = self._to_number(value)
        return converted

    def _to_number(self, value: Any) -> Any:
        text = str(value)
        try:
            if "." not in text and "e" not in text.lower():
                return int(text)
            return float(text)
        except ValueError:
            return value

    def _to_int(self, value: Any, default: int) -> int:
        try:
            return int(float(str(value)))
        except (TypeError, ValueError):
            return default

    def _to_bool(self, value: Any) -> bool:
        return str(value).strip().lower() in {"1", "true", "yes", "y"}

    def _to_optional_str(self, value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value)


supplier_selection_service = SupplierSelectionService()


def get_supplier_selection_status() -> dict[str, Any]:
    return supplier_selection_service.health()
