# contracts.py

## Purpose
This note documents `/process/src/v2_process/contracts.py`, which defines the typed schema used throughout the process pipeline.

## Where it sits in the pipeline
It sits underneath `config.py` and above all stage code. The contracts give the pipeline one consistent configuration and stage-result structure.

## Inputs
- `/process/src/v2_process/contracts.py`

## Outputs / side effects
No file outputs. This file defines dataclasses that are instantiated elsewhere.

## How the code works
The main dataclasses are:
- `InputPaths`
- `RuntimeConfig`
- `CleaningConfig`
- `MacroConfig`
- `OutputConfig`
- `PipelineConfig`
- `StageResult`

`PipelineConfig` bundles all runtime configuration into one object that stage functions can consume consistently.

`StageResult` is the runner’s unit of execution reporting. Each stage records:
- stage name
- success/failure
- elapsed seconds
- outputs
- metrics
- warnings
- errors

## Core Code
```python
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
class StageResult:
    stage: str
    ok: bool
    seconds: float
    outputs: Dict[str, str] = field(default_factory=dict)
```

## Math / logic
The dataclasses enforce a schema, not a transformation. The main logic is that all stages share one structured configuration object instead of loosely passing dictionaries.

## Worked Example
A stage can rely on:
- `config.cleaning.roll_days`
- `config.macro.release_lags`
- `config.outputs.root_dir`

without checking whether those keys exist in arbitrary dictionaries, because the dataclass schema guarantees them.

## Visual Flow
```mermaid
flowchart LR
    A[/config.py/] --> B[PipelineConfig]
    B --> C[stage run functions]
    C --> D[StageResult]
    D --> E[/quality_report.py/]
```

## What depends on it
- [Config loader](05_src_v2_process_config.md)
- [Runner](09_src_v2_process_runner.md)
- all stage notes

## Important caveats / assumptions
- The schema is only as accurate as the code that uses it. At present, some clipping thresholds are still hard-coded downstream even though matching config fields exist here.

## Linked Notes
- [Process config](03_configs_default_yaml.md)
- [Config loader](05_src_v2_process_config.md)
- [Runner](09_src_v2_process_runner.md)
- [Quality report stage](16_src_v2_process_stages_quality_report.md)
