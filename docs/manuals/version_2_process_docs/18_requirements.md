# requirements.txt

## Purpose
This note documents `/process/requirements.txt`, the dependency list for the active process pipeline and its notebook wrapper.

## Where it sits in the pipeline
It sits outside the runtime logic but defines the Python packages the process pipeline needs.

## Inputs
- `/process/requirements.txt`

## Outputs / side effects
No data outputs. Installing the requirements makes the process pipeline executable.

## How the code works
The file keeps the dependency set intentionally small:
- `numpy`
- `pandas`
- `PyYAML`
- `matplotlib`
- `seaborn`
- `jupyter`

This covers:
- data manipulation
- YAML loading
- notebook operation
- lightweight visualization

## Core Code
```text
numpy
pandas
PyYAML
matplotlib
seaborn
jupyter
```

## Math / logic
No numerical logic lives here; this is an environment specification.

## Worked Example
The process notebook installs these requirements with:

```bash
python -m pip install -q -r /process/requirements.txt
```

That is enough to run the full process pipeline and review notebook locally or in Colab.

## Visual Flow
```mermaid
flowchart LR
    A[/process/requirements.txt/] --> B[pip install]
    B --> C[/process/run_process.py/]
    B --> D[/process/notebooks/00_run_and_review_process.ipynb/]
```

## What depends on it
- [Process notebook](17_notebooks_00_run_and_review_process.md)
- any CLI execution of `/process`

## Important caveats / assumptions
- This file is minimal by design; heavier modeling libraries belong in `/model`, not `/process`.

## Linked Notes
- [Process README](01_README.md)
- [Process notebook](17_notebooks_00_run_and_review_process.md)
