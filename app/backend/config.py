"""Runtime configuration and project paths for the FastAPI backend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "app"
BACKEND_ROOT = APP_ROOT / "backend"


def resolve_project_path(value: str | Path) -> Path:
    """Resolve relative env paths from the project root."""
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


class Settings(BaseSettings):
    """Central settings object used by routes, services, Docker, and CI."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Neo Horcrox Supply Chain API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    API_PREFIX: str = "/api"
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    MODEL_ROOT: Path = PROJECT_ROOT / "model"
    DATASET_ROOT: Path | None = None
    ARTIFACTS_ROOT: Path | None = None

    CHAMPION_MODEL_DIR: Path | None = None
    CHAMPION_MODEL_PATH: Path | None = None
    CHAMPION_METADATA_PATH: Path | None = None

    LEGACY_RISK_MODEL_DIR: Path | None = None
    FORECAST_MODEL_DIR: Path | None = None
    SUPPLIER_SELECTION_OUTPUT_DIR: Path | None = None

    RAW_SUPPLY_CHAIN_DATASET_PATH: Path | None = None

    MONGODB_ENABLED: bool = True
    MONGODB_REQUIRED: bool = False
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "neo_horcrox"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def split_origins(cls, value: Any) -> list[str]:
        if value is None or value == "":
            return ["*"]
        if isinstance(value, str):
            if value.strip().startswith("["):
                return json.loads(value)
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator(
        "MODEL_ROOT",
        "DATASET_ROOT",
        "ARTIFACTS_ROOT",
        "CHAMPION_MODEL_DIR",
        "CHAMPION_MODEL_PATH",
        "CHAMPION_METADATA_PATH",
        "LEGACY_RISK_MODEL_DIR",
        "FORECAST_MODEL_DIR",
        "SUPPLIER_SELECTION_OUTPUT_DIR",
        "RAW_SUPPLY_CHAIN_DATASET_PATH",
        mode="after",
    )
    @classmethod
    def resolve_paths(cls, value: Path | None) -> Path | None:
        if value is None:
            return None
        return resolve_project_path(value)

    @property
    def dataset_root(self) -> Path:
        return self.DATASET_ROOT or self.MODEL_ROOT / "dataset"

    @property
    def artifacts_root(self) -> Path:
        return self.ARTIFACTS_ROOT or self.MODEL_ROOT / "artifacts"

    @property
    def models_root(self) -> Path:
        return self.artifacts_root / "models"

    @property
    def champion_model_dir(self) -> Path:
        return self.CHAMPION_MODEL_DIR or self.models_root / "champion_model"

    @property
    def champion_model_path(self) -> Path:
        return self.CHAMPION_MODEL_PATH or self.champion_model_dir / "late_shipment_model.pkl"

    @property
    def champion_metadata_path(self) -> Path:
        return self.CHAMPION_METADATA_PATH or self.champion_model_dir / "metadata.json"

    @property
    def legacy_risk_model_dir(self) -> Path:
        return self.LEGACY_RISK_MODEL_DIR or self.models_root / "risk"

    @property
    def forecast_model_dir(self) -> Path:
        return self.FORECAST_MODEL_DIR or self.models_root / "forecast"

    @property
    def supplier_selection_output_dir(self) -> Path:
        return (
            self.SUPPLIER_SELECTION_OUTPUT_DIR
            or self.artifacts_root / "metrics" / "supplier_selection_outputs"
        )

    @property
    def supplier_full_result_path(self) -> Path:
        return self.supplier_selection_output_dir / "supplier_selection_by_category_full_result.csv"

    @property
    def supplier_primary_path(self) -> Path:
        return self.supplier_selection_output_dir / "supplier_selection_primary_per_category.csv"

    @property
    def supplier_summary_path(self) -> Path:
        return self.supplier_selection_output_dir / "supplier_selection_by_category_summary.json"

    @property
    def supplier_weights_path(self) -> Path:
        return self.supplier_selection_output_dir / "supplier_selection_ahp_weights.csv"

    @property
    def raw_supply_chain_dataset_path(self) -> Path:
        return (
            self.RAW_SUPPLY_CHAIN_DATASET_PATH
            or self.dataset_root / "raw" / "DataCoSupplyChainDataset.csv"
        )


settings = Settings()
