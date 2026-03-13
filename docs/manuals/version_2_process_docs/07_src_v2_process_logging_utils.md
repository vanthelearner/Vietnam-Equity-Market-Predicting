# logging_utils.py

## Purpose
This note documents `/process/src/v2_process/logging_utils.py`, the shared logger factory for the process pipeline.

## Where it sits in the pipeline
It sits below the runner and stage files. The active codebase mainly uses it from the runner to standardize console output.

## Inputs
- `/process/src/v2_process/logging_utils.py`

## Outputs / side effects
No data artifacts. It configures and returns a logger named `v2_process`.

## How the code works
The helper:
- creates a logger named `v2_process`
- attaches one stream handler if none exists
- uses a common message format
- sets log level to `INFO`

## Core Code
```python
def get_logger() -> logging.Logger:
    logger = logging.getLogger('v2_process')
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
```

## Math / logic
No numerical logic lives here.

## Worked Example
A runner message appears like:

```text
2026-03-11 10:15:31,123 | INFO | Running stage: process_stock
```

This format comes from the formatter defined here.

## Visual Flow
```mermaid
flowchart LR
    A[/logging_utils.py/] --> B[runner logger]
    B --> C[stage start/end messages]
```

## What depends on it
- [Runner](09_src_v2_process_runner.md)

## Important caveats / assumptions
- The helper assumes one simple console logger is enough. There is no file logging or structured JSON logging.

## Linked Notes
- [Runner](09_src_v2_process_runner.md)
