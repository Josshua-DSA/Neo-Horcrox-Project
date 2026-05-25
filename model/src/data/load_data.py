"""Load raw supply-chain datasets."""

from pathlib import Path

import pandas as pd

from src.utils.config import RAW_DATA_DIR


def load_supply_chain_data(filename: str = "DataCoSupplyChainDataset.csv") -> pd.DataFrame:
    return pd.read_csv(Path(RAW_DATA_DIR) / filename, encoding="latin-1")
