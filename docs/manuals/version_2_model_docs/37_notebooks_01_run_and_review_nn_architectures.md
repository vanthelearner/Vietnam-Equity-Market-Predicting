# 01_run_and_review_nn_architectures.ipynb

## Purpose
Dedicated notebook for comparing four feed-forward NN depth choices under the `max_v3` feature profile. Source: `/model/notebooks/01_run_and_review_nn_architectures.ipynb`.

## Where it sits in the pipeline
This notebook is a focused wrapper around the active NN implementation in `/model/src/v2_model/models/nn.py` and the CLI runner. It is designed for architecture comparison, not general multi-model execution.

## Inputs
- Project root resolved the same way as the main notebook: `/content/drive/MyDrive/version_2/model`, then `/content/version_2/model`, then local fallback
- base config `/model/configs/max_v3.yaml`
- active NN model implementation
- generated output runs under `/model/outputs/`

## Outputs / side effects
- Creates temporary YAML configs that override only `models.nn.hidden_layer_grid`
- runs `run_model.py --models NN`
- reads summary outputs for each architecture
- writes latest recommendation CSVs for each architecture label

## How the code works
The notebook fixes the feature profile to `max_v3`, then defines four architectures: `NN_1L`, `NN_2L`, `NN_3L`, `NN_4L`. For each one it writes a temporary config with a single hidden-layer grid choice, runs the CLI once, then displays summary tables and latest fully labeled recommendations. This isolates the architecture-depth comparison while keeping the rest of the NN tuning grid unchanged.

## Core Code
```python
try:
    from google.colab import drive
    drive.mount('/content/drive')
except ModuleNotFoundError:
    pass

from pathlib import Path
import subprocess, sys, json, copy
import pandas as pd
from IPython.display import display

root_candidates = [
    Path('/content/drive/MyDrive/version_2/model'),
    Path('/content/version_2/model'),
    Path.cwd().resolve().parents[0],
]
ROOT = next(path for path in root_candidates if path.exists())
BASE_CONFIG = ROOT / 'configs' / 'max_v3.yaml'
print({'ROOT': str(ROOT), 'BASE_CONFIG': str(BASE_CONFIG)})
ROOT

subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', str(ROOT / 'requirements.txt')], check=True)
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))

import yaml
from v2_model.config import load_config
from v2_model.recommend import build_latest_recommendations

ARCHITECTURES = {
    'NN_1L': [64],
    'NN_2L': [64, 32],
    'NN_3L': [64, 32, 16],
    'NN_4L': [64, 32, 16, 8],
}

LAST_RUN_DIRS = {}
LAST_CONFIG_PATHS = {}

def _parse_run_dir(stdout_text: str):
    marker = 'Pipeline completed. Outputs saved to:'
    for line in reversed(stdout_text.splitlines()):
        if marker in line:
            return Path(line.split(marker, 1)[1].strip())
    return None

def _manifest_architecture(run_dir: Path):
    manifest = run_dir / 'meta' / 'run_manifest.json'
    if not manifest.exists():
        return None
    try:
        payload = json.loads(manifest.read_text())
        nn_cfg = payload.get('config', {}).get('models', {}).get('nn', {})
        return tuple(nn_cfg.get('hidden_layer_grid', [[None]])[0])
    except Exception:
        return None

def _architecture_label(hidden_layers):
    hidden_layers = tuple(hidden_layers)
    for label, arch in ARCHITECTURES.items():
        if tuple(arch) == hidden_layers:
            return label
    raise KeyError(f'Unknown architecture: {hidden_layers}')

def _make_nn_config(label: str):
    hidden_layers = ARCHITECTURES[label]
    raw = yaml.safe_load(BASE_CONFIG.read_text())
    raw.setdefault('models', {})
    raw['models'].setdefault('nn', {})
    raw['models']['nn']['hidden_layer_grid'] = [hidden_layers]
    out_path = Path('/tmp') / f'{label.lower()}_max_v3.yaml'
    out_path.write_text(yaml.safe_dump(raw, sort_keys=False))
    LAST_CONFIG_PATHS[label] = out_path
    return out_path

def run_nn_architecture(label: str, stages: str = 'all'):
    config_path = _make_nn_config(label)
    cmd = [sys.executable, str(ROOT / 'run_model.py'), '--config', str(config_path), '--models', 'NN', '--stages', stages]
    print('Running:', ' '.join(map(str, cmd)))
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    lines = []
    for line in proc.stdout:
        print(line, end='')
        lines.append(line.rstrip(''))
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f'NN run failed with code {rc}')
    run_dir = _parse_run_dir('
'.join(lines))
    if run_dir is None:
        raise RuntimeError('Could not parse run directory from command output.')
    LAST_RUN_DIRS[label] = run_dir
    return run_dir

def get_run_dir(label: str):
    if label in LAST_RUN_DIRS:
        return LAST_RUN_DIRS[label]
    candidates = sorted((ROOT / 'outputs').glob('run_*'))
    target_arch = tuple(ARCHITECTURES[label])
    for run_dir in reversed(candidates):
        if not (run_dir / 'r2' / 'nn_r2_summary_full_large_small.csv').exists():
            continue
        if _manifest_architecture(run_dir) != target_arch:
            continue
        LAST_RUN_DIRS[label] = run_dir
        return run_dir
    raise FileNotFoundError(f'No saved NN run found for {label}. Run the architecture first.')

def show_nn_summary(label: str):
    run_dir = get_run_dir(label)
    print('Architecture:', label, ARCHITECTURES[label])
    print('Run dir:', run_dir)
    display(pd.read_csv(run_dir / 'preprocess' / 'panel_prep_summary.csv'))
    display(pd.read_csv(run_dir / 'preprocess' / 'window_coverage_summary.csv'))
    display(pd.read_csv(run_dir / 'preprocess' / 'preprocess_report.csv'))
    display(pd.read_csv(run_dir / 'r2' / 'nn_r2_summary_full_large_small.csv'))
    display(pd.read_csv(run_dir / 'portfolio' / 'nn_performance_summary.csv'))
    display(pd.read_csv(run_dir / 'benchmark' / 'nn_vs_benchmark.csv'))
    imp_path = run_dir / 'importance' / 'nn_feature_importance.csv'
    if imp_path.exists():
        display(pd.read_csv(imp_path).head(15))
    comp_path = run_dir / 'complexity' / 'nn_complexity.csv'
    if comp_path.exists():
        display(pd.read_csv(comp_path).head(15))

def show_latest_nn_recommendations(label: str, top_k: int = 10, save_to_run_dir: bool = True):
    config_path = LAST_CONFIG_PATHS.get(label) or _make_nn_config(label)
    cfg = load_config(config_path)
    result = build_latest_recommendations(cfg, 'NN', top_k=top_k)
    print('Architecture:', label, ARCHITECTURES[label])
    print('Feature profile: max_v3')
    print('Latest fully labeled month scored:', result.latest_eom.date())
        print('Calibration window train:', result.train_start.date(), '->', result.train_end.date())
    print('Calibration window val  :', result.val_start.date(), '->', result.val_end.date())
            display(result.recommendations)
    if save_to_run_dir:
        run_dir = get_run_dir(label)
        out_path = run_dir / 'recommendations' / f"{label.lower()}_latest_recommendations.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        result.recommendations.to_csv(out_path, index=False)
        print('Saved:', out_path)

RUN_DIR_NN_1L = run_nn_architecture('NN_1L')
RUN_DIR_NN_1L

show_nn_summary('NN_1L')
```

## Math / logic
$$h^{{(1)}} = \phi(W_1 x + b_1),\quad \hat y = W_L h^{{(L-1)}} + b_L$$

The notebook changes only the hidden-layer structure, so the architecture comparison is about network depth and width, not about changing the optimizer, loss, or feature profile.

## Worked Example
In the `NN_2L` section the notebook creates a temporary config that sets `hidden_layer_grid = [[64, 32]]`, runs `NN` on `max_v3`, then shows the same core metrics as the all-model notebook plus a recommendation table for the latest fully labeled month.

## Visual Flow
```mermaid
flowchart TD
    A[max_v3 base config] --> B[_make_nn_config(label)]
    B --> C[temp yaml]
    C --> D[run_model.py --models NN]
    D --> E[/outputs/run_*/]
    E --> F[summary tables]
    E --> G[latest recommendations]
```

## What depends on it
- `/model/src/v2_model/models/nn.py`
- `/model/run_model.py`
- `/model/configs/max_v3.yaml`
- `/model/src/v2_model/recommend.py`

## Important caveats / assumptions
- This notebook only compares architecture depth on `max_v3`.
- It does not compare `careful_v3` vs `max_v3` for NN.

## Linked Notes
- [Pipeline map](00_version_2_model_pipeline_map.md)
- [NN model implementation](27_src_v2_model_models_nn.md)
- [max_v3 config](36_configs_max_v3_yaml.md)
- [Main model notebook](05_notebooks_00_run_and_review_model.md)

