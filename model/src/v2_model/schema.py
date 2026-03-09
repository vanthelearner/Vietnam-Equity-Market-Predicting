from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd

REQUIRED_PANEL_COLUMNS = ["id", "eom", "prc", "me", "ret", "ret_exc", "ret_exc_lead1m", "be_me", "ret_12_1"]
REQUIRED_BENCHMARK_COLUMNS = ["eom", "benchmark_ret"]


@dataclass
class SchemaReport:
    n_rows: int
    n_assets: int
    date_min: str
    date_max: str


def validate_columns(df: pd.DataFrame, required: Iterable[str], name: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")


def validate_no_duplicate_keys(df: pd.DataFrame, key_cols: list[str], name: str) -> None:
    dup = df.duplicated(subset=key_cols, keep=False)
    if dup.any():
        raise ValueError(f"{name} has duplicated keys on {key_cols}")


def validate_panel_schema(panel: pd.DataFrame) -> SchemaReport:
    validate_columns(panel, REQUIRED_PANEL_COLUMNS, "panel")
    panel = panel.copy()
    panel["eom"] = pd.to_datetime(panel["eom"], errors="coerce")
    if panel["eom"].isna().any():
        raise ValueError("panel.eom contains unparsable dates")
    validate_no_duplicate_keys(panel, ["id", "eom"], "panel")
    for c in ["prc", "me", "ret", "ret_exc", "ret_exc_lead1m", "be_me", "ret_12_1"]:
        if not pd.api.types.is_numeric_dtype(panel[c]):
            raise ValueError(f"panel column {c} must be numeric")
    return SchemaReport(int(len(panel)), int(panel["id"].nunique()), str(panel["eom"].min().date()), str(panel["eom"].max().date()))


def validate_benchmark_schema(benchmark: pd.DataFrame) -> SchemaReport:
    validate_columns(benchmark, REQUIRED_BENCHMARK_COLUMNS, "benchmark")
    benchmark = benchmark.copy()
    benchmark["eom"] = pd.to_datetime(benchmark["eom"], errors="coerce")
    if benchmark["eom"].isna().any():
        raise ValueError("benchmark.eom contains unparsable dates")
    return SchemaReport(int(len(benchmark)), 1, str(benchmark["eom"].min().date()), str(benchmark["eom"].max().date()))
