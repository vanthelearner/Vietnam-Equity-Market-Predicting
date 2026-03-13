# tests/test_compare.py

## Purpose
Test/support file describing or enforcing part of the active model contract. Source: `/model/tests/test_compare.py`.

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

from v2_model.compare import build_cumulative_tables


def test_cumulative_tables_are_wealth_not_log_sum():
    tb = {
        'ENET': pd.DataFrame({
            'eom': ['2020-01-31', '2020-02-29'],
            'long_ret_ew': [0.10, 0.10],
            'short_ret_ew': [0.0, 0.0],
            'long_ret_vw': [0.10, 0.10],
            'short_ret_vw': [0.0, 0.0],
        })
    }
    bench = pd.DataFrame({'eom': ['2020-01-31', '2020-02-29'], 'benchmark_ret': [0.0, 0.0]})
    ew, _ = build_cumulative_tables(tb, bench)
    final = ew['ENET_long'].iloc[-1]
    assert abs(final - 1.21) < 1e-9
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

