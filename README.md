# Version 2

This tree splits the workflow into three folders:

- `data`: raw stock, raw macro, and risk-free inputs
- `process`: broad daily data preparation only
- `model`: monthly panel preparation, liquidity control, benchmark construction, model runs, and output review

The v2 design removes liquidity cuts from `process` and applies them only in `model`.

Quick entrypoints:
- `process/run_process.py`
- `process/notebooks/00_run_and_review_process.ipynb`
- `model/run_model.py`
- `model/notebooks/00_run_and_review_model.ipynb`

## Google Colab
The current notebooks are using Google Collab to execuate the code, you can upload the folder to `/content/version_2`, both notebooks are already written to use:
- `/content/version_2/process`
- `/content/version_2/model`

The notebooks install requirements with `pip`, run the pipeline, and then display the outputs.
