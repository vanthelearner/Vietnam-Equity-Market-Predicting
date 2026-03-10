from __future__ import annotations

from pathlib import Path

import pandas as pd

from v2_model.config import load_config
from v2_model.recommend_true_latest import build_true_latest_recommendations


def test_true_latest_recommendations_use_true_last_month(tmp_path: Path):
    panel = pd.DataFrame(
        [
            # 2020-01
            {"id": "A", "eom": "2020-01-31", "prc": 1200.0, "me": 200000.0, "ret": 0.01, "ret_exc": 0.009, "ret_exc_lead1m": 0.010, "be_me": 0.8, "ret_12_1": 0.10, "adv_med": 100.0},
            {"id": "B", "eom": "2020-01-31", "prc": 1200.0, "me": 200000.0, "ret": 0.00, "ret_exc": -0.001, "ret_exc_lead1m": -0.002, "be_me": 0.5, "ret_12_1": 0.02, "adv_med": 50.0},
            # 2020-02
            {"id": "A", "eom": "2020-02-29", "prc": 1200.0, "me": 200000.0, "ret": 0.02, "ret_exc": 0.010, "ret_exc_lead1m": 0.020, "be_me": 0.8, "ret_12_1": 0.10, "adv_med": 100.0},
            {"id": "B", "eom": "2020-02-29", "prc": 1200.0, "me": 200000.0, "ret": -0.01, "ret_exc": -0.002, "ret_exc_lead1m": -0.010, "be_me": 0.5, "ret_12_1": 0.02, "adv_med": 50.0},
            # 2020-03
            {"id": "A", "eom": "2020-03-31", "prc": 1200.0, "me": 200000.0, "ret": 0.03, "ret_exc": 0.020, "ret_exc_lead1m": 0.030, "be_me": 0.8, "ret_12_1": 0.10, "adv_med": 100.0},
            {"id": "B", "eom": "2020-03-31", "prc": 1200.0, "me": 200000.0, "ret": -0.02, "ret_exc": -0.010, "ret_exc_lead1m": -0.020, "be_me": 0.5, "ret_12_1": 0.02, "adv_med": 50.0},
            # 2020-04
            {"id": "A", "eom": "2020-04-30", "prc": 1200.0, "me": 200000.0, "ret": 0.04, "ret_exc": 0.030, "ret_exc_lead1m": 0.020, "be_me": 0.8, "ret_12_1": 0.10, "adv_med": 100.0},
            {"id": "B", "eom": "2020-04-30", "prc": 1200.0, "me": 200000.0, "ret": -0.01, "ret_exc": -0.020, "ret_exc_lead1m": -0.010, "be_me": 0.5, "ret_12_1": 0.02, "adv_med": 50.0},
            # 2020-05
            {"id": "A", "eom": "2020-05-31", "prc": 1200.0, "me": 200000.0, "ret": 0.03, "ret_exc": 0.020, "ret_exc_lead1m": 0.010, "be_me": 0.8, "ret_12_1": 0.10, "adv_med": 100.0},
            {"id": "B", "eom": "2020-05-31", "prc": 1200.0, "me": 200000.0, "ret": -0.01, "ret_exc": -0.010, "ret_exc_lead1m": -0.005, "be_me": 0.5, "ret_12_1": 0.02, "adv_med": 50.0},
            # 2020-06 = true latest month, unlabeled
            {"id": "A", "eom": "2020-06-30", "prc": 1200.0, "me": 200000.0, "ret": 0.02, "ret_exc": 0.010, "ret_exc_lead1m": None, "be_me": 0.8, "ret_12_1": 0.10, "adv_med": 100.0},
            {"id": "B", "eom": "2020-06-30", "prc": 1200.0, "me": 200000.0, "ret": -0.01, "ret_exc": -0.005, "ret_exc_lead1m": None, "be_me": 0.5, "ret_12_1": 0.02, "adv_med": 50.0},
        ]
    )
    bench = pd.DataFrame({"eom": pd.date_range("2020-01-31", periods=6, freq="ME"), "benchmark_ret": [0.0] * 6})
    dummy_daily = tmp_path / "dummy_daily.csv"
    dummy_rf = tmp_path / "dummy_rf.csv"
    panel_path = tmp_path / "panel.csv"
    bench_path = tmp_path / "bench.csv"
    out_dir = tmp_path / "outputs"
    dummy_daily.write_text("Date,Ticker\n")
    dummy_rf.write_text("observation_date,DGS3MO\n")
    panel.to_csv(panel_path, index=False)
    bench.to_csv(bench_path, index=False)

    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        f"""
paths:
  input_daily_model_csv: {dummy_daily}
  input_risk_free_csv: {dummy_rf}
  prepared_panel_csv: {panel_path}
  prepared_benchmark_csv: {bench_path}
  prepared_panel_summary_csv: {tmp_path / 'panel_summary.csv'}
  prepared_benchmark_summary_csv: {tmp_path / 'bench_summary.csv'}
  window_coverage_summary_csv: {tmp_path / 'window_summary.csv'}
  output_dir: {out_dir}
preprocess:
  min_price: 1000.0
  min_me: 100000.0
  liquidity_category: core_liquid_top50
  min_col_coverage: 0.75
  winsor_lower: 0.01
  winsor_upper: 0.99
cv:
  train_months: 3
  val_months: 2
  test_months: 1
  step_months: 1
runtime:
  run_variable_importance: false
""",
        encoding="utf-8",
    )

    cfg = load_config(cfg_path)
    result = build_true_latest_recommendations(cfg, "OLS", top_k=10)

    assert pd.Timestamp(result.score_eom) == pd.Timestamp("2020-06-30")
    assert pd.Timestamp(result.latest_labeled_eom) == pd.Timestamp("2020-05-31")
    assert pd.Timestamp(result.train_start) == pd.Timestamp("2020-01-31")
    assert pd.Timestamp(result.train_end) == pd.Timestamp("2020-03-31")
    assert pd.Timestamp(result.val_start) == pd.Timestamp("2020-04-30")
    assert pd.Timestamp(result.val_end) == pd.Timestamp("2020-05-31")
    assert result.universe_rows == 2
    assert result.scored_rows == 2
    assert len(result.recommendations) == 2
    assert result.recommendations.iloc[0]["id"] == "A"
    assert pd.Timestamp(result.recommendations.iloc[0]["eom"]) == pd.Timestamp("2020-06-30")
