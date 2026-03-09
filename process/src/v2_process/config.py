from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .contracts import CleaningConfig, InputPaths, MacroConfig, OutputConfig, PipelineConfig, RuntimeConfig


def _merge_obj(default_obj, data: dict[str, Any] | None):
    if not data:
        return default_obj
    for k, v in data.items():
        if hasattr(default_obj, k):
            setattr(default_obj, k, v)
    return default_obj


def _resolve_path(v: str | None, root: Path) -> Path | None:
    if v is None:
        return None
    p = Path(v).expanduser()
    if not p.is_absolute():
        p = (root / p).resolve()
    return p


def load_config(config_path: str | Path) -> tuple[PipelineConfig, Path]:
    cfg_path = Path(config_path).expanduser().resolve()
    raw = yaml.safe_load(cfg_path.read_text(encoding='utf-8')) or {}
    project_root = cfg_path.parent.parent
    runtime = _merge_obj(RuntimeConfig(), raw.get('runtime'))
    cleaning = _merge_obj(CleaningConfig(), raw.get('cleaning'))
    macro = _merge_obj(MacroConfig(), raw.get('macro'))
    paths_raw = raw.get('paths', {})
    p_in = paths_raw.get('input', {})
    p_out = paths_raw.get('output', {})
    inputs = InputPaths(
        stock_raw_csv=_resolve_path(p_in.get('stock_raw_csv', '../data/raw_stock_data.csv'), project_root),
        macro_raw_csv=_resolve_path(p_in.get('macro_raw_csv', '../data/raw_macro_data.csv'), project_root),
    )
    outputs = OutputConfig(root_dir=_resolve_path(p_out.get('root_dir', 'outputs'), project_root))
    return PipelineConfig(project_root=project_root, inputs=inputs, outputs=outputs, runtime=runtime, cleaning=cleaning, macro=macro), cfg_path
