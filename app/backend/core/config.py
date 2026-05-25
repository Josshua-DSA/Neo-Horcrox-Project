"""Application settings and runtime paths."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[3]


def _resolve_path(value: str | Path, base: Path = REPO_ROOT) -> Path:
    path = Path(value)
    return path if path.is_absolute() else base / path


class Settings(BaseSettings):
    APP_NAME: str = "Neo-Horcrox Supply Chain API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    API_PREFIX: str = "/api"
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: str = "*"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5417/neo_horcrox"

    MODEL_ROOT: str = "model"
    ARTIFACTS_DIR: str | None = None
    CHAMPION_MODEL_PATH: str | None = None
    CHAMPION_METADATA_PATH: str | None = None
    FORECAST_MODEL_DIR: str | None = None
    LEGACY_RISK_MODEL_DIR: str | None = None
    SUPPLIER_SELECTION_OUTPUT_DIR: str | None = None
    RAW_SUPPLY_CHAIN_DATASET_PATH: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins(self) -> list[str]:
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]

    @property
    def model_root(self) -> Path:
        return _resolve_path(self.MODEL_ROOT)

    @property
    def artifacts_root(self) -> Path:
        if self.ARTIFACTS_DIR:
            return _resolve_path(self.ARTIFACTS_DIR)
        return self.model_root / "artifacts"

    @property
    def champion_model_path(self) -> Path:
        if self.CHAMPION_MODEL_PATH:
            return _resolve_path(self.CHAMPION_MODEL_PATH)
        return self.artifacts_root / "models" / "champion_model" / "late_shipment_model.pkl"

    @property
    def champion_metadata_path(self) -> Path:
        if self.CHAMPION_METADATA_PATH:
            return _resolve_path(self.CHAMPION_METADATA_PATH)
        return self.artifacts_root / "models" / "champion_model" / "metadata.json"

    @property
    def forecast_model_dir(self) -> Path:
        if self.FORECAST_MODEL_DIR:
            return _resolve_path(self.FORECAST_MODEL_DIR)
        return self.artifacts_root / "models" / "forecast"

    @property
    def legacy_risk_model_dir(self) -> Path:
        if self.LEGACY_RISK_MODEL_DIR:
            return _resolve_path(self.LEGACY_RISK_MODEL_DIR)
        return self.artifacts_root / "models" / "risk"

    @property
    def supplier_selection_output_dir(self) -> Path:
        if self.SUPPLIER_SELECTION_OUTPUT_DIR:
            return _resolve_path(self.SUPPLIER_SELECTION_OUTPUT_DIR)
        return self.artifacts_root / "metrics" / "supplier_selection_outputs"

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
        if self.RAW_SUPPLY_CHAIN_DATASET_PATH:
            return _resolve_path(self.RAW_SUPPLY_CHAIN_DATASET_PATH)
        return self.model_root / "dataset" / "raw" / "DataCoSupplyChainDataset.csv"


settings = Settings()
