from __future__ import annotations

import time
from datetime import datetime

from .contracts import PipelineConfig, StageResult
from .logging_utils import get_logger
from .paths import OutputPaths, build_output_paths
from .stages import build_model_data, process_macro, process_stock, quality_report, transform_stock, validate_raw

STAGE_ORDER = ['transform', 'validate', 'process_stock', 'process_macro', 'build_model']
STAGE_FUNCS = {
    'transform': transform_stock.run,
    'validate': validate_raw.run,
    'process_stock': process_stock.run,
    'process_macro': process_macro.run,
    'build_model': build_model_data.run,
}


def _iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


def run_pipeline(config: PipelineConfig, config_path: str, stages: list[str] | None = None) -> tuple[dict, OutputPaths]:
    logger = get_logger()
    paths = build_output_paths(config)
    stage_order = STAGE_ORDER if not stages or stages == ['all'] else stages
    # The context acts as the handoff contract between stages.
    context = {'stock_raw_csv': str(config.inputs.stock_raw_csv), 'macro_raw_csv': str(config.inputs.macro_raw_csv)}
    stage_results: list[StageResult] = []
    started_at = _iso_now()
    for stage in stage_order:
        logger.info('Running stage: %s', stage)
        t0 = time.perf_counter()
        try:
            out = STAGE_FUNCS[stage](config=config, paths=paths, context=context)
            seconds = time.perf_counter() - t0
            # Persist each stage's declared outputs so later stages can reuse them.
            for k, v in out.get('outputs', {}).items():
                context[k] = str(v)
            stage_results.append(StageResult(stage=stage, ok=True, seconds=seconds, outputs={k: str(v) for k, v in out.get('outputs', {}).items()}, metrics=out.get('metrics', {}), warnings=out.get('warnings', []), errors=[]))
            logger.info('Completed stage: %s (%.2fs)', stage, seconds)
        except Exception as exc:
            seconds = time.perf_counter() - t0
            stage_results.append(StageResult(stage=stage, ok=False, seconds=seconds, outputs={}, metrics={}, warnings=[], errors=[str(exc)]))
            logger.exception('Stage failed: %s', stage)
            if not config.runtime.continue_on_error:
                break
    # Always write the manifest so partial runs still leave an audit trail.
    manifest = quality_report.write_meta(config=config, config_path=str(config_path), paths=paths, stage_order=stage_order, stage_results=stage_results, context=context, started_at=started_at)
    return manifest, paths
