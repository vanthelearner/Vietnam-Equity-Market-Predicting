from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class InputPaths:
    stock_raw_csv: Path
    macro_raw_csv: Path


@dataclass
class RuntimeConfig:
    continue_on_error: bool = False


@dataclass
class CleaningConfig:
    start_date: str = '2000-01-01'
    roll_days: int = 252
    min_base_days: int = 60
    min_rel: float = 0.70
    min_stocks_early: int = 300
    min_price: float = 1000.0
    liq_win: int = 60
    liq_minp: int = 20
    target_clip: float = 0.50
    outlier_abs_ret_flag: float = 1.0
    stale_limit_days: int = 252


@dataclass
class MacroConfig:
    max_missing_share: float = 0.995
    release_lags: dict[str, int] = field(default_factory=lambda: {'US_GDP_QoQ': 30, 'US_CPI_YoY': 14, 'VN_CPI_YoY': 0})


@dataclass
class OutputConfig:
    root_dir: Path


@dataclass
class PipelineConfig:
    project_root: Path | None = None
    inputs: InputPaths | None = None
    outputs: OutputConfig | None = None
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    cleaning: CleaningConfig = field(default_factory=CleaningConfig)
    macro: MacroConfig = field(default_factory=MacroConfig)


@dataclass
class StageResult:
    stage: str
    ok: bool
    seconds: float
    outputs: dict[str, str] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
