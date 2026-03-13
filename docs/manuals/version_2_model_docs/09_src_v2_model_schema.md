# schema.py

## Purpose
Documents `/model/src/v2_model/schema.py`. Source: `/model/src/v2_model/schema.py`.

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

