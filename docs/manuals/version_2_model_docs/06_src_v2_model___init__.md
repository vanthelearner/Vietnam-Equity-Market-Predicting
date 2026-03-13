# __init__.py

## Purpose
Documents `/model/src/v2_model/__init__.py`. Source: `/model/src/v2_model/__init__.py`.

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
from .config import DEFAULT_MODELS, load_config
from .pipeline import run_pipeline

__all__ = ["DEFAULT_MODELS", "load_config", "run_pipeline"]
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

