# Version 2 Model Pipeline

This pipeline reads the broad daily output from `../process`, builds the monthly model panel, applies the model-side liquidity filter, runs rolling models, and writes comparison and portfolio outputs.

## Inputs

- `../process/outputs/03_model_data/daily_model_data.csv`
- `../data/risk-free.csv`

## Prepared Data Outputs

- `data/panel_input.csv`
- `data/benchmark_monthly.csv`
- `data/panel_prep_summary.csv`
- `data/benchmark_prep_summary.csv`
- `data/window_coverage_summary.csv`

## Run Outputs

Each model run writes a timestamped folder under `outputs/run_*`, including:

- preprocess reports and feature lists
- rolling-window summaries
- prediction files
- portfolio and benchmark outputs
- cross-model comparison tables when `compare` is enabled
- `meta/run_manifest.json`

## Config Presets

- `configs/default.yaml`: main preset, currently using `careful_v3`
- `configs/careful_v3.yaml`: explicit careful-profile preset
- `configs/max_v3.yaml`: wider feature-profile preset

## CLI

Run all stages for all models:

```bash
cd model
pip install -r requirements.txt
python run_model.py --config configs/default.yaml --models all --stages all
```

Run one model:

```bash
python run_model.py --config configs/default.yaml --models ENET --stages all
```

Run only panel preparation:

```bash
python run_model.py --config configs/default.yaml --models all --stages prepare
```

`--models` and `--stages` both take comma-separated values.

Available stages:

- `prepare`
- `train`
- `compare`

Available models:

- `OLS`
- `OLS3`
- `ENET`
- `PLS`
- `PCR`
- `GBRT`
- `RF`
- `NN`

## Recommendation Workflow

The active recommendation helper is:

- `src/v2_model/recommend.py`

The notebooks use `build_latest_recommendations(...)` after a run to score the latest transformed month and save readable ranked outputs.

Archived experimental code in `not_working/` is not part of the active pipeline.

## Notebooks

- `notebooks/00_run_and_review_model.ipynb`
- `notebooks/01_run_and_review_nn_architectures.ipynb`
- `notebooks/get data.ipynb`

The main notebook runs one model at a time and reviews the saved artifacts from the run directory.

## Google Colab

If the project lives at `/content/version_2`, open:

- `model/notebooks/00_run_and_review_model.ipynb`

The notebooks are written to use `/content/version_2/model`.
