# Version 2 Process Pipeline

This pipeline turns the raw stock and macro CSVs into a broad daily model dataset. It does not do train/val/test splitting, FF factor reconstruction, benchmark construction, or liquidity cuts.

## Inputs
- `../data/raw_stock_data.csv`
- `../data/raw_macro_data.csv`

## Outputs
- `outputs/00_validation/*`
- `outputs/01_stock/clean_stock_daily.csv`
- `outputs/02_macro/clean_macro_daily.csv`
- `outputs/03_model_data/daily_model_data.csv`
- `outputs/_meta/*`

## Run
```bash
cd process
pip install -r requirements.txt
python run_process.py --config configs/default.yaml --stages all
```

## Notebook
- `notebooks/00_run_and_review_process.ipynb`

## Google Colab
If the project lives at `/content/version_2`, open:
- `process/notebooks/00_run_and_review_process.ipynb`

The notebook will:
- point itself to `/content/version_2/process`
- install `requirements.txt`
- run the full process pipeline
- display the main summaries and the top of `daily_model_data.csv`
