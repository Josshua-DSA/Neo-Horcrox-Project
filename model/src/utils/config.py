"""Shared model project paths."""

from pathlib import Path


MODEL_ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = MODEL_ROOT / "dataset"
RAW_DATA_DIR = DATASET_DIR / "raw"
PROCESSED_DATA_DIR = DATASET_DIR / "processed"
ENGINEERED_DATA_DIR = DATASET_DIR / "engineered"
ARTIFACTS_DIR = MODEL_ROOT / "artifacts"
REPORTS_DIR = MODEL_ROOT / "reports"

CHAMPION_MODEL_DIR = ARTIFACTS_DIR / "models" / "champion_model"
CHAMPION_MODEL_PATH = CHAMPION_MODEL_DIR / "late_shipment_model.pkl"
CHAMPION_METADATA_PATH = CHAMPION_MODEL_DIR / "metadata.json"

SUPPLIER_SELECTION_OUTPUT_DIR = ARTIFACTS_DIR / "metrics" / "supplier_selection_outputs"
