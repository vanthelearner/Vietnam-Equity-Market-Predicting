# run_process.py

## Purpose
This note documents `/process/run_process.py`, the command-line entrypoint for the active process pipeline.

## Where it sits in the pipeline
It is the outermost executable wrapper for `/process`. It resolves the Python path, reads the YAML config, parses the requested stages, and hands control to the runner.

## Inputs
- `/process/run_process.py`
- config path passed with `--config`
- optional stage list from `--stages`

## Outputs / side effects
This file itself does not create data artifacts. It triggers the pipeline that writes into `/process/outputs/...` and prints the final output root to stdout.

## How the code works
The script does four things:
1. resolve `ROOT` and `SRC`
2. prepend `src` to `sys.path`
3. parse CLI arguments
4. call `load_config(...)` and `run_pipeline(...)`

## Core Code
Core entrypoint logic.

```python
ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))      # make /process/src importable

parser.add_argument('--config', required=True)
parser.add_argument('--stages', nargs='*', default=['all'])
args = parser.parse_args(argv)

config = load_config(args.config)     # build typed config object
stages = None if args.stages == ['all'] else args.stages
manifest, paths = run_pipeline(config, config_path=args.config, stages=stages)
print(f'Process outputs saved under: {paths.root}')
```

## Math / logic
No model math lives here. The important logic is argument handling:

$$
\text{stages} =
\begin{cases}
\text{all default stages}, & \text{if } \texttt{--stages all} \\
\text{user-specified subset}, & \text{otherwise}
\end{cases}
$$

## Worked Example
Example command from the active project:

```bash
cd /process
PYTHONPATH=src python run_process.py --config configs/default.yaml --stages all
```

This launches the full active stage sequence:
`transform -> validate -> process_stock -> process_macro -> build_model`.

## Visual Flow
```mermaid
flowchart LR
    A[CLI arguments] --> B[/process/run_process.py/]
    B --> C[/process/src/v2_process/config.py/]
    C --> D[/process/src/v2_process/runner.py/]
    D --> E[/process/outputs/.../]
```

## What depends on it
Operators and notebooks depend on this file when they want a scripted run of the process pipeline.

## Important caveats / assumptions
- This script assumes `src` exists exactly under `/process`.
- It expects the config path to be valid; there is no fallback search logic.

## Linked Notes
- [Pipeline map](00_version_2_process_pipeline_map.md)
- [Process config](03_configs_default_yaml.md)
- [Config loader](05_src_v2_process_config.md)
- [Runner](09_src_v2_process_runner.md)
- [Process notebook](17_notebooks_00_run_and_review_process.md)
