# Version 2 Process Pipeline

This pipeline converts the raw stock and macro CSVs in `../data` into a broad daily handoff file for the model stage.

It is responsible for:

- stock feature engineering
- raw-file validation summaries
- daily stock cleaning and calendar rebuilding
- macro cleaning and release-lag handling
- the final stock-macro merge into `daily_model_data.csv`

It does not do model-side liquidity selection, monthly panel preparation, rolling windows, or portfolio evaluation.

## Inputs

- `../data/raw_stock_data.csv`
- `../data/raw_macro_data.csv`

## Main Outputs

- `outputs/00_validation/raw_stock_summary.csv`
- `outputs/00_validation/raw_stock_missing_share.csv`
- `outputs/00_validation/raw_macro_missing_share.csv`
- `outputs/01_stock/clean_stock_daily.csv`
- `outputs/01_stock/clean_stock_summary.csv`
- `outputs/02_macro/clean_macro_daily.csv`
- `outputs/02_macro/macro_missing_share.csv`
- `outputs/03_model_data/macro_lagged_daily.csv`
- `outputs/03_model_data/macro_release_lag_diagnostics.csv`
- `outputs/03_model_data/daily_model_data.csv`
- `outputs/_meta/run_manifest.json`

## CLI

```bash
cd process
pip install -r requirements.txt
python run_process.py --config configs/default.yaml --stages all
```

Stage selection is comma-separated:

```bash
python run_process.py --config configs/default.yaml --stages transform,validate,process_stock
```

Available stages:

- `transform`
- `validate`
- `process_stock`
- `process_macro`
- `build_model`

## Notebook

- `notebooks/00_run_and_review_process.ipynb`

The notebook installs local requirements, runs the process pipeline, and reviews the key output files.

## Handoff to Model

The main downstream contract is:

- `outputs/03_model_data/daily_model_data.csv`

That file is the input consumed by `../model`.

## Google Colab

If the project lives at `/content/version_2`, open:

- `process/notebooks/00_run_and_review_process.ipynb`

The notebook is already written to use `/content/version_2/process`.
