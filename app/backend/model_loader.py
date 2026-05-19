"""Helpers for exporting model artifacts from notebooks or training scripts."""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

from .config import settings


class ArtifactExporter:
    """Writes model artifacts to the same paths consumed by ModelRegistry."""

    def save_champion_model(self, model: Any, metadata: dict[str, Any]) -> None:
        self._dump_pickle(model, settings.champion_model_path)
        self._dump_json(metadata, settings.champion_metadata_path)

    def save_forecast_artifacts(
        self,
        model: Any,
        category_encoder: Any,
        market_encoder: Any,
        metadata: dict[str, Any],
        group_stats: list[dict[str, Any]],
    ) -> None:
        output_dir = settings.forecast_model_dir
        self._dump_pickle(model, output_dir / "forecast_model.pkl")
        self._dump_pickle(category_encoder, output_dir / "forecast_cat_encoder.pkl")
        self._dump_pickle(market_encoder, output_dir / "forecast_mkt_encoder.pkl")
        self._dump_json(metadata, output_dir / "forecast_metadata.json")
        self._dump_json(group_stats, output_dir / "forecast_group_stats.json")

    def save_legacy_risk_candidate(
        self,
        model: Any,
        scaler: Any | None = None,
        freq_maps: dict[str, Any] | None = None,
        feature_list: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        output_dir = settings.legacy_risk_model_dir
        self._dump_pickle(model, output_dir / "risk_model.pkl")
        if scaler is not None:
            self._dump_pickle(scaler, output_dir / "risk_scaler.pkl")
        if freq_maps is not None:
            self._dump_json(freq_maps, output_dir / "risk_freq_maps.json")
        if feature_list is not None:
            self._dump_json(feature_list, output_dir / "risk_features.json")
        if metadata is not None:
            self._dump_json(metadata, output_dir / "risk_metadata.json")

    def _dump_pickle(self, artifact: Any, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as file:
            pickle.dump(artifact, file)

    def _dump_json(self, artifact: Any, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(artifact, file, indent=2, ensure_ascii=False)


artifact_exporter = ArtifactExporter()


def save_champion_model(model: Any, metadata: dict[str, Any]) -> None:
    artifact_exporter.save_champion_model(model, metadata)


def save_forecast_artifacts(
    model: Any,
    category_encoder: Any,
    market_encoder: Any,
    metadata: dict[str, Any],
    group_stats: list[dict[str, Any]],
) -> None:
    artifact_exporter.save_forecast_artifacts(
        model=model,
        category_encoder=category_encoder,
        market_encoder=market_encoder,
        metadata=metadata,
        group_stats=group_stats,
    )


def save_legacy_risk_candidate(
    model: Any,
    scaler: Any | None = None,
    freq_maps: dict[str, Any] | None = None,
    feature_list: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    artifact_exporter.save_legacy_risk_candidate(
        model=model,
        scaler=scaler,
        freq_maps=freq_maps,
        feature_list=feature_list,
        metadata=metadata,
    )