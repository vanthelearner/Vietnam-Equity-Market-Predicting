# max_v3.yaml

## Purpose
Profile-specific override that switches the model pipeline to the widest active feature profile, `max_v3`. Source: `/model/configs/max_v3.yaml`.

## Where it sits in the pipeline
Used by notebooks or CLI runs when you want the widest active Batch 3 feature set.

## Inputs
- No runtime input besides the YAML itself.
- Merged into the base config by `/model/src/v2_model/config.py`.

## Outputs / side effects
No direct outputs. It widens the set of optional predictors selected during preprocessing.

## How the code works
Like `careful_v3.yaml`, it includes `default.yaml` and overrides only `preprocess.feature_profile`.

## Core Code
```yaml
paths:
  input_daily_model_csv: ../process/outputs/03_model_data/daily_model_data.csv
  input_risk_free_csv: ../data/risk-free.csv
  prepared_panel_csv: ./data/panel_input.csv
  prepared_benchmark_csv: ./data/benchmark_monthly.csv
  prepared_panel_summary_csv: ./data/panel_prep_summary.csv
  prepared_benchmark_summary_csv: ./data/benchmark_prep_summary.csv
  window_coverage_summary_csv: ./data/window_coverage_summary.csv
  output_dir: ./outputs

prepare:
  rf_date_col: observation_date
  rf_value_col: DGS3MO

preprocess:
  min_price: 1000.0
  min_me: 100000.0
  liquidity_category: broad_liquid_top50
  feature_profile: max_v3
  min_col_coverage: 0.75
  winsor_lower: 0.01
  winsor_upper: 0.99
  date_start: null

cv:
  train_months: 60
  val_months: 24
  test_months: 12
  step_months: 12

sampling:
  large_small_pct: 0.30

portfolio:
  n_deciles: 10
  cost_bps_list: [0, 10, 20, 30]
  benchmark_cost_bps: 30

runtime:
  seed: 42
  n_jobs: -1
  smoke_test: false
  run_variable_importance: true

models:
  ols:
    max_iter: 1000
  ols3:
    max_iter: 1000
    fixed_features: [me, be_me, ret_12_1]
  enet:
    alpha_start: 0.00001
    alpha_stop: 0.004
    alpha_num: 20
    l1_ratio: 0.5
    max_iter: 10000
  pls:
    components: [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19]
  pcr:
    components: [1,2,3,5,7,9,11,15,17,22,25,29,33,40,45,49]
  gbrt:
    max_depth: [1,2,3,4,5,6,7,8]
    n_estimators: [100]
    learning_rate: [0.01, 0.1]
    max_features: [sqrt]
    min_samples_split: [5000, 8000, 10000]
    min_samples_leaf: [50, 100, 200]
    huber_delta: 1.35
  rf:
    max_depth: [1,2,3,4,5,6]
    max_features: [3, 6, 12, 24, 46, 49]
    n_estimators: 100
  nn:
    hidden_layer_grid:
      - [64]
      - [64, 32]
      - [64, 32, 16]
      - [64, 32, 16, 8]
    dropout_grid: [0.0, 0.1]
    learning_rate_grid: [0.001]
    weight_decay_grid: [0.00001, 0.0001]
    batch_size: 1024
    epochs: 80
    patience: 8
    device: cuda
```

## Math / logic
$$X_{{max}} = X[\text{{FEATURE\_PROFILES["max\_v3"]}}]$$

## Worked Example
If the monthly panel contains both base and engineered expansion columns, this config activates the widest optional set without changing the underlying monthly panel file.

## Visual Flow
```mermaid
flowchart LR
    A[max_v3.yaml] --> B[config.py merge]
    B --> C[PipelineConfig]
    C --> D[preprocess feature_profile = max_v3]
```

## What depends on it
- `/model/notebooks/00_run_and_review_model.ipynb`
- `/model/notebooks/01_run_and_review_nn_architectures.ipynb` via max_v3 base config
- `/model/run_model.py` when called with this config path

## Important caveats / assumptions
- `max_v3` increases feature breadth and missingness pressure.
- It does not change the monthly sample rules by itself.

## Linked Notes
- [Default config](03_configs_default_yaml.md)
- [careful_v3 config](35_configs_careful_v3_yaml.md)
- [Feature profiles](34_src_v2_model_feature_profiles.md)

