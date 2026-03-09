from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

import pandas as pd

from ..contracts import PipelineConfig, StageResult
from ..paths import OutputPaths


def _iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def write_meta(config: PipelineConfig, config_path: str, paths: OutputPaths, stage_order: list[str], stage_results: list[StageResult], context: dict, started_at: str) -> dict:
    finished_at = _iso_now()
    manifest = {
        'config_path': str(config_path),
        'started_at': started_at,
        'finished_at': finished_at,
        'stage_order': stage_order,
        'stage_results': [asdict(s) for s in stage_results],
        'context': {k: str(v) for k, v in context.items()},
    }
    (paths.meta / 'run_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    pd.DataFrame([{'stage': s.stage, 'ok': bool(s.ok), 'seconds': float(s.seconds), 'warnings': ' | '.join(s.warnings), 'errors': ' | '.join(s.errors)} for s in stage_results]).to_csv(paths.meta / 'stage_timings.csv', index=False)
    pd.DataFrame([
        {'gate': 'all_requested_stages_ok', 'pass': bool(all(s.ok for s in stage_results)), 'detail': 'All requested stages completed.'},
        {'gate': 'core_outputs_exist', 'pass': bool(paths.raw_stock_summary.exists() and paths.clean_stock.exists() and paths.macro_base.exists() and paths.model_data.exists()), 'detail': 'Key outputs exist.'},
    ]).to_csv(paths.meta / 'quality_gates.csv', index=False)
    return manifest
