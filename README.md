# Version 2

`version_2` is a two-stage research pipeline for stock prediction.

- `data`: local input files used by the pipeline
- `process`: daily stock and macro preparation
- `model`: monthly panel build, liquidity filtering, rolling model runs, portfolio outputs, and recommendation review

The design intentionally keeps the upstream `process` stage broad and applies the final liquidity screen in `model`.

## Workflow

1. Run `process` to build `process/outputs/03_model_data/daily_model_data.csv`.
2. Run `model` to build the monthly panel and train one or more rolling models.
3. Use the notebooks for review, charts, and recommendation tables.

## Project Layout

- `process/run_process.py`: CLI entrypoint for the daily pipeline
- `process/notebooks/00_run_and_review_process.ipynb`: process review notebook
- `model/run_model.py`: CLI entrypoint for the monthly modeling pipeline
- `model/notebooks/00_run_and_review_model.ipynb`: main model review notebook
- `model/notebooks/01_run_and_review_nn_architectures.ipynb`: NN-focused review notebook

## Quick Start

Run the process stage first:

```bash
cd process
pip install -r requirements.txt
python run_process.py --config configs/default.yaml --stages all
```

Then run the model stage:

```bash
cd ../model
pip install -r requirements.txt
python run_model.py --config configs/default.yaml --models all --stages all
```

## Configs

- `process/configs/default.yaml`: daily pipeline config
- `model/configs/default.yaml`: main model config, currently using the `careful_v3` feature profile
- `model/configs/careful_v3.yaml`: explicit careful-profile preset
- `model/configs/max_v3.yaml`: wider feature-profile preset

## Notes

- Both CLIs accept comma-separated stage selections.
- `process` stages: `transform`, `validate`, `process_stock`, `process_macro`, `build_model`
- `model` stages: `prepare`, `train`, `compare`
- `model --models` accepts `all` or a comma-separated list such as `OLS,ENET,RF`

## Google Colab

If the project is uploaded to `/content/version_2`, the notebooks are already written to use:

- `/content/version_2/process`
- `/content/version_2/model`

The notebooks install their local requirements, run the pipeline code, and display the saved outputs.
