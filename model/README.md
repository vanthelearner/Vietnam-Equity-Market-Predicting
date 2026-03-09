# Version 2 Model Pipeline

This pipeline reads the broad daily output from `../process`, prepares the monthly model panel, applies liquidity control, and runs the full model set.

## Inputs
- `../process/outputs/03_model_data/daily_model_data.csv`
- `../data/risk-free.csv`

## Outputs
- `data/panel_input.csv`
- `data/benchmark_monthly.csv`
- `data/panel_prep_summary.csv`
- `data/benchmark_prep_summary.csv`
- `data/window_coverage_summary.csv`
- `outputs/run_*/...`

## Run
```bash
cd model
pip install -r requirements.txt
python run_model.py --config configs/default.yaml --models all --stages all
```

Run one model:
```bash
python run_model.py --config configs/default.yaml --models ENET --stages all
```

Available models:
- `OLS`
- `OLS3`
- `ENET`
- `PLS`
- `PCR`
- `GBRT`
- `RF`
- `NN`

## Notebook
- `notebooks/00_run_and_review_model.ipynb`

## Google Colab
If the project lives at `/content/version_2`, open:
- `model/notebooks/00_run_and_review_model.ipynb`

The notebook will:
- point itself to `/content/version_2/model`
- install `requirements.txt`
- let you run one model at a time
- show quick performance tables
- show and save the model's latest recommended stocks
