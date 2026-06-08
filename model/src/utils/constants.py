"""Shared model constants."""

TARGET_LATE_SHIPMENT = "Late_delivery_risk"

LATE_SHIPMENT_FEATURES = [
    "Latitude",
    "geo_distance_proxy",
    "order_hour",
    "order_period",
    "scheduled_days",
    "scheduled_by_mode",
    "expected_scheduled_days_by_mode",
    "is_first_class_mode",
    "is_second_class_mode",
    "is_medium_shipping",
]

SHIPPING_MODE_DAYS = {
    "same day": 0,
    "first class": 1,
    "second class": 2,
    "standard class": 4,
}
