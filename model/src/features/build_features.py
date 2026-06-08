"""Feature-building entry points used by training and backend inference."""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

import pandas as pd

from ..utils.constants import LATE_SHIPMENT_FEATURES, SHIPPING_MODE_DAYS


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.copy()


def build_late_shipment_features(
    records: Iterable[dict[str, Any]],
    feature_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Build the 10 late-shipment model features from raw request records."""

    selected_features = feature_names or LATE_SHIPMENT_FEATURES
    rows = []
    missing_by_record: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        row = dict(record)
        _add_geo_features(row)
        _add_order_time_features(row)
        _add_shipping_mode_features(row)

        feature_row = {feature: _coerce_number(row.get(feature)) for feature in selected_features}
        missing = [feature for feature, value in feature_row.items() if value is None]
        if missing:
            missing_by_record.append({"index": index, "missing_features": missing})

        rows.append(feature_row)

    if missing_by_record:
        raise ValueError(f"Missing late shipment features: {missing_by_record}")

    return rows


def _add_geo_features(row: dict[str, Any]) -> None:
    latitude = _first_present(row, "Latitude", "latitude")
    longitude = _first_present(row, "Longitude", "longitude")

    if "Latitude" not in row and latitude is not None:
        row["Latitude"] = latitude

    if row.get("geo_distance_proxy") is None and latitude is not None:
        lat = _coerce_number(latitude)
        lon = _coerce_number(longitude) or 0.0
        if lat is not None:
            row["geo_distance_proxy"] = math.sqrt((lat**2) + (lon**2))


def _add_order_time_features(row: dict[str, Any]) -> None:
    order_date = _first_present(
        row,
        "order_date",
        "order_datetime",
        "order_timestamp",
        "order date (DateOrders)",
    )

    if row.get("order_hour") is None and order_date is not None:
        parsed = pd.to_datetime(order_date, errors="coerce")
        if not pd.isna(parsed):
            row["order_hour"] = int(parsed.hour)

    hour = _coerce_number(row.get("order_hour"))
    if row.get("order_period") is None and hour is not None:
        row["order_period"] = _order_period_from_hour(int(hour))


def _add_shipping_mode_features(row: dict[str, Any]) -> None:
    mode = _normalize_shipping_mode(
        _first_present(row, "shipping_mode", "Shipping Mode", "shippingMode")
    )
    expected_days = SHIPPING_MODE_DAYS.get(mode) if mode else None

    if row.get("expected_scheduled_days_by_mode") is None and expected_days is not None:
        row["expected_scheduled_days_by_mode"] = expected_days

    if row.get("scheduled_by_mode") is None and expected_days is not None:
        row["scheduled_by_mode"] = expected_days

    if row.get("scheduled_days") is None:
        scheduled_source = _first_present(row, "Days for shipment (scheduled)", "scheduledDays")
        row["scheduled_days"] = scheduled_source if scheduled_source is not None else expected_days

    if row.get("is_first_class_mode") is None and mode:
        row["is_first_class_mode"] = int(mode == "first class")

    if row.get("is_second_class_mode") is None and mode:
        row["is_second_class_mode"] = int(mode == "second class")

    scheduled_days = _coerce_number(row.get("scheduled_days"))
    if row.get("is_medium_shipping") is None and scheduled_days is not None:
        row["is_medium_shipping"] = int(2 <= scheduled_days <= 3)


def _order_period_from_hour(hour: int) -> float:
    if 0 <= hour <= 5:
        return 0.0
    if 6 <= hour <= 11:
        return 1.0
    if 12 <= hour <= 17:
        return 2.0
    if 18 <= hour <= 23:
        return 3.0
    raise ValueError("order_hour must be between 0 and 23")


def _normalize_shipping_mode(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().replace("_", " ").replace("-", " ").lower()
    normalized = " ".join(normalized.split())
    return normalized or None


def _first_present(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return value
    return None


def _coerce_number(value: Any) -> float | int | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    if number.is_integer():
        return int(number)
    return number
