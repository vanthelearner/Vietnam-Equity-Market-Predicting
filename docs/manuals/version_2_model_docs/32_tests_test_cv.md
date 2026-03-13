# tests/test_cv.py

## Purpose
Test/support file describing or enforcing part of the active model contract. Source: `/model/tests/test_cv.py`.

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
from v2_model.cv import build_rolling_windows


def test_build_rolling_windows_count():
    months = list(range(20))
    windows = build_rolling_windows(months, train_months=6, val_months=4, test_months=2, step_months=2)
    assert len(windows) == 5
    assert windows[0].train_months == [0, 1, 2, 3, 4, 5]
    assert windows[0].test_months == [10, 11]
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

