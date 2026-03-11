# Version 2 Data

This folder contains the local input files used by the active `process` and `model` pipelines.

## Required Files

- `raw_stock_data.csv`: upstream stock-level daily panel used by `process`
- `raw_macro_data.csv`: upstream macro panel used by `process`
- `risk-free.csv`: daily risk-free series used by `model`

## How They Are Used

- `process/configs/default.yaml` reads `raw_stock_data.csv` and `raw_macro_data.csv`
- `model/configs/*.yaml` read `risk-free.csv`
- `model` then consumes the processed handoff written by `../process/outputs/03_model_data/daily_model_data.csv`

These files are treated as working inputs for the current project so the v2 pipelines can run without depending on the older project tree.
