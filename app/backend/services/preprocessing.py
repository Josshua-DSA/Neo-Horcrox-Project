"""
services/preprocessing.py
--------------------------
Mirrors the feature engineering pipeline from
notebook/dataset_engineered/Feature_engineering{f&l}.ipynb
so that inference input is transformed identically to training data.
"""

import numpy as np
import pandas as pd
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Columns dropped during training (PII / leakage / irrelevant)
DROPPED_COLS = [
    "Product Description", "Product Image", "Product Category Id",
    "Order Zipcode", "Customer Fname", "Customer Lname", "Customer Email",
    "Customer Street", "Customer Zipcode", "Customer Password",
    "Order Customer Id",
    # Leakage columns for risk model
    "Delivery Status", "actual_delay", "is_late", "is_early",
    "severe_delay", "shipping_speed_ratio",
]

# Target column
TARGET_COL = "Late_delivery_risk"

# Rare category threshold used during training
RARE_THRESHOLD = 20


def compute_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all engineered features on a raw or partial DataFrame.
    Safe to call at inference (no target leakage).
    """
    df = df.copy()

    # --- Shipping / delay features ---
    if "Days for shipping (real)" in df.columns and "Days for shipment (scheduled)" in df.columns:
        df["actual_delay"] = (
            df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]
        )
        df["shipping_speed_ratio"] = df.apply(
            lambda r: (
                r["Days for shipping (real)"] / r["Days for shipment (scheduled)"]
                if r["Days for shipment (scheduled)"] != 0 else np.nan
            ),
            axis=1,
        )
        df["is_late"]  = (df["actual_delay"] > 0).astype(int)
        df["is_early"] = (df["actual_delay"] < 0).astype(int)
        df["severe_delay"] = (df["actual_delay"] > 5).astype(int)

    # --- Financial consistency ---
    if all(c in df.columns for c in [
        "Order Item Product Price", "Order Item Quantity", "Order Item Discount"
    ]):
        df["calculated_item_total"] = (
            df["Order Item Product Price"] * df["Order Item Quantity"]
            - df["Order Item Discount"]
        )
        df["item_total_gap"] = df["Order Item Total"] - df["calculated_item_total"]
        df["abs_item_total_gap"] = df["item_total_gap"].abs()
        df["has_price_inconsistency"] = (df["abs_item_total_gap"] > 1e-3).astype(int)

    # --- Geo mismatch ---
    if "Customer Country" in df.columns and "Order Country" in df.columns:
        df["country_mismatch"] = (df["Customer Country"] != df["Order Country"]).astype(int)
    if "Customer State" in df.columns and "Order State" in df.columns:
        df["state_mismatch"] = (df["Customer State"] != df["Order State"]).astype(int)
    if "Customer City" in df.columns and "Order City" in df.columns:
        df["city_mismatch"] = (df["Customer City"] != df["Order City"]).astype(int)

    # --- Price ratio ---
    if "Order Item Product Price" in df.columns and "Product Price" in df.columns:
        df["Price_Ratio"] = df.apply(
            lambda r: (
                r["Order Item Product Price"] / r["Product Price"]
                if r["Product Price"] != 0 else np.nan
            ),
            axis=1,
        )

    return df


def apply_frequency_encoding(
    df: pd.DataFrame,
    category_cols: list,
    freq_maps: dict,
    rare_maps: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Apply frequency encoding with rare-category handling, using maps
    learned during training (loaded from artifacts/risk_freq_maps.json).
    """
    df = df.copy()
    for col in category_cols:
        if col not in df.columns:
            continue
        if col not in freq_maps:
            logger.warning(f"No freq map for column: {col}, filling with 0")
            df[col] = 0
            continue

        fmap = freq_maps[col]
        mode_val = fmap.get("__mode__", "Unknown")
        df[col] = df[col].fillna(mode_val)

        # Rare → "__rare__"
        valid_cats = set(fmap.get("__valid_categories__", []))
        df[col] = df[col].where(df[col].isin(valid_cats), "__rare__")

        # Map to frequency
        df[col] = df[col].map(fmap).fillna(0)

    return df


def preprocess_for_risk(
    df: pd.DataFrame,
    scaler,
    freq_maps: dict,
    feature_list: list,
) -> np.ndarray:
    """
    Full preprocessing pipeline for the risk model.
    Returns a numpy array ready for model.predict / model.predict_proba.
    """
    # 1. Compute engineered features
    df = compute_engineered_features(df)

    # 2. Determine column types
    category_cols = df.select_dtypes(include=["object"]).columns.tolist()
    numeric_cols  = df.select_dtypes(include=["int64", "float64", "int32", "float32"]).columns.tolist()

    # 3. Frequency-encode categoricals
    df = apply_frequency_encoding(df, category_cols, freq_maps)

    # 4. Select & order features
    missing_features = [f for f in feature_list if f not in df.columns]
    if missing_features:
        logger.warning(f"Missing features at inference: {missing_features}")
        for f in missing_features:
            df[f] = 0

    df = df[feature_list]

    # 5. Scale numerics (scaler was fit on numeric_cols subset during training)
    # If scaler is available, transform the entire feature matrix
    if scaler is not None:
        X = scaler.transform(df)
    else:
        X = df.values

    return X