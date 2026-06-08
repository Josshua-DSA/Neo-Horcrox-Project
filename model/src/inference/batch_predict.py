"""Batch inference helpers."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .predict_late_shipment import predict_probability


def batch_predict(model: Any, frame: pd.DataFrame):
    return model.predict(frame)


def batch_predict_probability(model: Any, frame: pd.DataFrame):
    return predict_probability(model, frame)
