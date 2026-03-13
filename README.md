# Vietnam Equity Market Predicting

This repository contains the current `version_2` research pipeline for studying whether stock-level characteristics and macro signals can rank Vietnamese equities well enough to build useful monthly portfolios.

The workflow is split into two stages:

- `process`: build a broad daily stock and macro panel
- `model`: convert that panel into a monthly cross-section, apply the final investability filter, run rolling models, and review portfolio outputs

## Results Snapshot

The main review notebook is [`model/notebooks/00_run_and_review_model.ipynb`](model/notebooks/00_run_and_review_model.ipynb). The saved notebook outputs currently reflect runs completed on March 10-11, 2026.

- Latest fully labeled month scored in the notebook: `2026-02-28`
- Raw monthly panel before final model filtering: `108,605` stock-month rows, `699` assets, `270` months
- Investable training sample after price, size, and `broad_liquid_top50` filtering: `15,871` rows across `170` assets
- Rolling evaluation design: `15` windows with `60` train months, `24` validation months, and `12` test months per window
- Combined out-of-sample test span in the saved review: `2010-10-31` to `2025-09-30`

One important takeaway from the notebook is that out-of-sample `R2` is still slightly negative across models, so this project should be read primarily as a cross-sectional ranking exercise rather than a calibrated point-forecasting system. Despite that, several ranking portfolios are economically strong in the saved backtests.

### Selected Backtest Results From The Notebook

| Model / feature profile | Full-sample OOS `R2` | Long-short EW gross ann. return | Long-short EW net ann. return @ 30 bps | Gross Sharpe | Max drawdown |
| --- | ---: | ---: | ---: | ---: | ---: |
| `ENET` / `max_v3` | -0.0119 | 62.1% | 53.8% | 2.14 | -20.0% |
| `PLS` / `max_v3` | -0.0054 | 58.6% | 50.3% | 2.02 | -26.9% |
| `NN` / `careful_v3` | -0.0068 | 54.9% | 45.6% | 1.79 | -27.8% |
| `OLS` / `careful_v3` | -0.0249 | 54.5% | 44.4% | 2.02 | -19.7% |
| `ENET` / `careful_v3` | -0.0135 | 53.7% | 46.1% | 2.19 | -11.5% |

Additional interpretation from the saved notebook:

- `careful_v3` is usually the safer default. The wider `max_v3` profile helps `ENET`, `PLS`, and `PCR`, but it degrades `OLS`, `NN`, and `RF`.
- `OLS3` is the low-complexity baseline. It has one of the least-negative `R2` readings (`-0.0114`) but materially weaker long-short performance than the stronger ranking models.
- `GBRT` looks promising in the notebook, but its saved review only covers `36` out-of-sample months, so it is not directly comparable to the full `156`-month runs above.

### Latest Example Recommendations In The Notebook

The notebook also shows the latest scored names for the last fully labeled month (`2026-02-28`). Two examples from the saved outputs:

- `NN` with `careful_v3`: `BCG`, `BCE`, `DTG`, `ASP`, `TCD`
- `OLS` with `careful_v3`: `TDC`, `TCD`, `BCG`, `BAB`, `AAT`

These are notebook outputs, not live advice. They will change as the source data and model runs are refreshed.

## Pipeline Overview

1. Run `process` to transform daily stock and macro inputs into `process/outputs/03_model_data/daily_model_data.csv`.
2. Run `model` to build the monthly panel, train one or more rolling models, and save predictions, portfolio summaries, benchmark comparisons, and review artifacts.
3. Open the notebooks to inspect feature coverage, rolling window diagnostics, performance tables, and latest recommendation tables.

The design intentionally keeps `process` broad. The final liquidity screen is applied in `model`, which makes it easier to rerun experiments with different investability rules without rebuilding the daily upstream data each time.

## Project Layout

- [`FEATURE_DICTIONARY.md`](FEATURE_DICTIONARY.md): feature reference for every model input used by the `version_2` pipeline
- [`process/run_process.py`](process/run_process.py): CLI entrypoint for the daily pipeline
- [`process/notebooks/00_run_and_review_process.ipynb`](process/notebooks/00_run_and_review_process.ipynb): process review notebook
- [`model/run_model.py`](model/run_model.py): CLI entrypoint for the monthly modeling pipeline
- [`model/notebooks/00_run_and_review_model.ipynb`](model/notebooks/00_run_and_review_model.ipynb): main model review notebook
- [`model/notebooks/01_run_and_review_nn_architectures.ipynb`](model/notebooks/01_run_and_review_nn_architectures.ipynb): NN-focused review notebook

## Quick Start

Before running the pipeline, place the required local input files into [`data/`](data/):

- `raw_stock_data.csv`
- `raw_macro_data.csv`
- `risk-free.csv`

Run the daily `process` stage first:

```bash
cd process
pip install -r requirements.txt
python run_process.py --config configs/default.yaml --stages all
```

Then run the monthly `model` stage:

```bash
cd ../model
pip install -r requirements.txt
python run_model.py --config configs/default.yaml --models all --stages all
```

Useful model configs:

- [`model/configs/default.yaml`](model/configs/default.yaml): main config, currently aligned with `careful_v3`
- [`model/configs/careful_v3.yaml`](model/configs/careful_v3.yaml): explicit careful feature-profile preset
- [`model/configs/max_v3.yaml`](model/configs/max_v3.yaml): wider feature-profile preset

CLI notes:

- `process --stages` accepts `transform`, `validate`, `process_stock`, `process_macro`, `build_model`
- `model --stages` accepts `prepare`, `train`, `compare`
- `model --models` accepts `all` or a comma-separated list such as `OLS,ENET,RF`

## Google Colab

If the project is uploaded to `/content/version_2`, the notebooks are already written to use:

- `/content/version_2/process`
- `/content/version_2/model`

The notebooks install their local requirements, run the pipeline code, and display the saved outputs.

## Data Access And Licensing

The raw market datasets used by this project are Bloomberg-derived working files.

- `data/raw_stock_data.csv` and `data/raw_macro_data.csv` are expected to come from Bloomberg exports or equivalent Bloomberg-sourced workflows.
- Those Bloomberg-derived inputs are not open data. Reproducing this project requires your own valid Bloomberg license and compliance with Bloomberg's data terms.
- Bloomberg-sourced files should not be redistributed through this repository, mirrored into a public release, or shared outside the rights granted by Bloomberg.
- Generated outputs that materially contain Bloomberg-derived content may also remain subject to Bloomberg's terms, even when transformed by this pipeline.

The repository's source code is separate from the vendor data terms:

- The code in this repository is proprietary and is released under the terms in [`LICENSE`](LICENSE).
- Unless the copyright holder gives separate written permission, this repository should be treated as `All Rights Reserved`.
- This project is shared for private research review, not as open-source software.

## Research Use

This project is for research and educational review only. Nothing in this repository or its notebooks should be read as investment advice, a solicitation, or a promise of live performance.
