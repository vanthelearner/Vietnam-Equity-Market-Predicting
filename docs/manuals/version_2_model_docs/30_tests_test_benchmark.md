# tests/test_benchmark.py

## Purpose
Test/support file describing or enforcing part of the active model contract. Source: `/model/tests/test_benchmark.py`.

## Where it sits in the pipeline
This file supports the active model pipeline and is part of the maintained code path.

## Inputs
- Code-level inputs vary by caller; see the core code snippet below.
 
## Outputs / side effects
- Depends on caller; configuration, path resolution, testing, or derived tables depending on the file.
 
## How the code works
The file is part of the active `version_2/model` implementation and should be read together with the linked notes for the surrounding workflow.

## Core Code
```python
import pandas as pd

from v2_model.benchmark import compare_vs_benchmark


def test_benchmark_label_uses_target_bps():
    ls = pd.DataFrame({
        'eom': ['2020-01-31', '2020-02-29'],
        'net_excess_ew_20bps': [0.01, 0.02],
        'net_excess_vw_20bps': [0.01, 0.02],
    })
    bench = pd.DataFrame({
        'eom': ['2020-01-31', '2020-02-29'],
        'benchmark_exc': [0.0, 0.0],
    })
    out = compare_vs_benchmark(ls, bench, model_name='ENET', target_bps=20, strategy_ew_col='net_excess_ew_20bps', strategy_vw_col='net_excess_vw_20bps')
    assert out['strategy'].str.contains('20bps').all()
```

## Math / logic
Use the linked notes for the main pipeline math. This file is mostly structural support around the active model workflow.

## Worked Example
Example: this file participates when the notebook calls the CLI or when the pipeline builds/validates rolling windows and output artifacts.

## Visual Flow
```mermaid
flowchart LR
    A[file] --> B[active model pipeline]
```

## What depends on it
- Other active files in `/model/src/v2_model` and the notebooks.

## Important caveats / assumptions
- This note focuses on the active code only. `model/not_working` is excluded from the maintained manuals.

## Linked Notes
- [Pipeline map](00_version_2_model_pipeline_map.md)
- [Pipeline orchestrator](17_src_v2_model_pipeline.md)

