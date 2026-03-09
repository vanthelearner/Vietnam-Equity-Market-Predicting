from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .contracts import PipelineConfig


@dataclass(frozen=True)
class OutputPaths:
    root: Path
    out_00: Path
    out_01: Path
    out_02: Path
    out_03: Path
    meta: Path
    intermediate: Path
    raw_stock_summary: Path
    raw_stock_missing_share: Path
    raw_macro_missing_share: Path
    transformed_stock: Path
    clean_stock: Path
    clean_summary: Path
    macro_base: Path
    macro_missing_share: Path
    macro_lagged: Path
    macro_lag_diag: Path
    model_data: Path


def build_output_paths(config: PipelineConfig) -> OutputPaths:
    root = config.outputs.root_dir
    out_00 = root / '00_validation'
    out_01 = root / '01_stock'
    out_02 = root / '02_macro'
    out_03 = root / '03_model_data'
    meta = root / '_meta'
    intermediate = root / '_intermediate'
    for p in [root, out_00, out_01, out_02, out_03, meta, intermediate]:
        p.mkdir(parents=True, exist_ok=True)
    return OutputPaths(
        root=root,
        out_00=out_00,
        out_01=out_01,
        out_02=out_02,
        out_03=out_03,
        meta=meta,
        intermediate=intermediate,
        raw_stock_summary=out_00 / 'raw_stock_summary.csv',
        raw_stock_missing_share=out_00 / 'raw_stock_missing_share.csv',
        raw_macro_missing_share=out_00 / 'raw_macro_missing_share.csv',
        transformed_stock=intermediate / 'stock_transformed.csv',
        clean_stock=out_01 / 'clean_stock_daily.csv',
        clean_summary=out_01 / 'clean_stock_summary.csv',
        macro_base=out_02 / 'clean_macro_daily.csv',
        macro_missing_share=out_02 / 'macro_missing_share.csv',
        macro_lagged=out_03 / 'macro_lagged_daily.csv',
        macro_lag_diag=out_03 / 'macro_release_lag_diagnostics.csv',
        model_data=out_03 / 'daily_model_data.csv',
    )
