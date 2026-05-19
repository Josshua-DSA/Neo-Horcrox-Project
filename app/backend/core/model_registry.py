"""Model and artifact registry for backend inference services."""

from __future__ import annotations

import json
import logging
import pickle
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ArtifactStatus:
    name: str
    path: str
    loaded: bool = False
    error: str | None = None


class ModelRegistry:
    """Loads production model artifacts once and exposes them to services."""

    def __init__(self) -> None:
        self.champion_model: Any | None = None
        self.champion_metadata: dict[str, Any] = {}

        self.forecast_model: Any | None = None
        self.forecast_cat_encoder: Any | None = None
        self.forecast_mkt_encoder: Any | None = None
        self.forecast_metadata: dict[str, Any] = {}
        self.forecast_group_stats: list[dict[str, Any]] = []

        self.legacy_risk_model: Any | None = None
        self.legacy_risk_scaler: Any | None = None
        self.legacy_risk_freq_maps: dict[str, Any] = {}
        self.legacy_risk_features: list[str] = []
        self.legacy_risk_metadata: dict[str, Any] = {}

        self._statuses: dict[str, ArtifactStatus] = {}

    def load_all(self) -> None:
        """Load every runtime artifact. Missing artifacts are reported, not fatal."""
        logger.info("Loading model artifacts from %s", settings.artifacts_root)
        self._statuses.clear()
        self._load_production_risk()
        self._load_forecast()
        self._load_legacy_risk_candidate()

    def clear(self) -> None:
        self.__init__()

    def status(self) -> dict[str, Any]:
        return {
            "production_risk": {
                "model_loaded": self.champion_model is not None,
                "metadata_loaded": bool(self.champion_metadata),
                "model_path": str(settings.champion_model_path),
                "metadata_path": str(settings.champion_metadata_path),
                "features": self.champion_metadata.get("features", []),
                "target": self.champion_metadata.get("target", "Late_delivery_risk"),
                "threshold": self.champion_metadata.get("threshold", 0.5),
            },
            "forecast": {
                "model_loaded": self.forecast_model is not None,
                "cat_encoder_loaded": self.forecast_cat_encoder is not None,
                "market_encoder_loaded": self.forecast_mkt_encoder is not None,
                "metadata_loaded": bool(self.forecast_metadata),
                "group_stats_loaded": bool(self.forecast_group_stats),
                "model_path": str(settings.forecast_model_dir / "forecast_model.pkl"),
            },
            "legacy_risk_candidate": {
                "model_loaded": self.legacy_risk_model is not None,
                "metadata_loaded": bool(self.legacy_risk_metadata),
                "kept_for_experiment": True,
                "path": str(settings.legacy_risk_model_dir),
            },
            "artifacts": {
                name: asdict(status)
                for name, status in sorted(self._statuses.items())
            },
        }

    def _load_production_risk(self) -> None:
        self.champion_model = self._load_pickle(
            "production_risk_model",
            settings.champion_model_path,
        )
        self.champion_metadata = self._load_json(
            "production_risk_metadata",
            settings.champion_metadata_path,
            default={},
        )

    def _load_forecast(self) -> None:
        forecast_dir = settings.forecast_model_dir
        self.forecast_model = self._load_pickle(
            "forecast_model",
            forecast_dir / "forecast_model.pkl",
        )
        self.forecast_cat_encoder = self._load_pickle(
            "forecast_cat_encoder",
            forecast_dir / "forecast_cat_encoder.pkl",
        )
        self.forecast_mkt_encoder = self._load_pickle(
            "forecast_mkt_encoder",
            forecast_dir / "forecast_mkt_encoder.pkl",
        )
        self.forecast_metadata = self._load_json(
            "forecast_metadata",
            forecast_dir / "forecast_metadata.json",
            default={},
        )
        self.forecast_group_stats = self._load_json(
            "forecast_group_stats",
            forecast_dir / "forecast_group_stats.json",
            default=[],
        )

    def _load_legacy_risk_candidate(self) -> None:
        risk_dir = settings.legacy_risk_model_dir
        self.legacy_risk_model = self._load_pickle("legacy_risk_model", risk_dir / "risk_model.pkl")
        self.legacy_risk_scaler = self._load_pickle("legacy_risk_scaler", risk_dir / "risk_scaler.pkl")
        self.legacy_risk_freq_maps = self._load_json("legacy_risk_freq_maps", risk_dir / "risk_freq_maps.json", default={})
        self.legacy_risk_features = self._load_json("legacy_risk_features", risk_dir / "risk_features.json", default=[])
        self.legacy_risk_metadata = self._load_json("legacy_risk_metadata", risk_dir / "risk_metadata.json", default={})

    def _load_pickle(self, name: str, path: Path) -> Any | None:
        status = ArtifactStatus(name=name, path=str(path))
        self._statuses[name] = status
        if not path.exists():
            status.error = "file not found"
            logger.warning("Artifact %s not found at %s", name, path)
            return None
        try:
            with path.open("rb") as file:
                artifact = pickle.load(file)
        except Exception as exc:
            status.error = f"{type(exc).__name__}: {exc}"
            logger.exception("Could not load pickle artifact %s from %s", name, path)
            return None
        status.loaded = True
        logger.info("Loaded pickle artifact %s from %s", name, path)
        return artifact

    def _load_json(self, name: str, path: Path, default: Any) -> Any:
        status = ArtifactStatus(name=name, path=str(path))
        self._statuses[name] = status
        if not path.exists():
            status.error = "file not found"
            logger.warning("JSON artifact %s not found at %s", name, path)
            return default
        try:
            with path.open("r", encoding="utf-8") as file:
                artifact = json.load(file)
        except Exception as exc:
            status.error = f"{type(exc).__name__}: {exc}"
            logger.exception("Could not load JSON artifact %s from %s", name, path)
            return default
        status.loaded = True
        logger.info("Loaded JSON artifact %s from %s", name, path)
        return artifact


model_registry = ModelRegistry()
