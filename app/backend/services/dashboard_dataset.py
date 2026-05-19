"""Raw dataset access helpers used by dashboard and product profiling."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd

from ..config import settings


class DashboardDatasetRepository:
    """Loads the raw supply-chain CSV with tolerant encoding handling."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.raw_supply_chain_dataset_path

    def load(self, columns: Iterable[str] | None = None) -> pd.DataFrame:
        requested = tuple(columns or ())
        return _load_raw_dataset(str(self.path), requested).copy()


@lru_cache(maxsize=16)
def _load_raw_dataset(path_text: str, columns: tuple[str, ...]) -> pd.DataFrame:
    path = Path(path_text)
    if not path.exists():
        return pd.DataFrame(columns=list(columns))

    read_kwargs = {"usecols": list(columns)} if columns else {}
    for encoding in ("utf-8", "utf-8-sig", "latin1", "cp1252"):
        try:
            return pd.read_csv(path, encoding=encoding, **read_kwargs)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="latin1", **read_kwargs)


dashboard_dataset_repository = DashboardDatasetRepository()
