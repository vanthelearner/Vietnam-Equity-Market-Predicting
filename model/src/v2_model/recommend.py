from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import PipelineConfig
from .cv import build_rolling_windows
from .pipeline import _feature_set_for_model, _model_callable, _model_kwargs
from .preprocess import prepare_scoring_data


@dataclass
class RecommendationResult:
    model_name: str
    latest_eom: pd.Timestamp
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    val_start: pd.Timestamp
    val_end: pd.Timestamp
    recommendations: pd.DataFrame


def build_latest_recommendations(config: PipelineConfig, model_name: str, top_k: int = 10) -> RecommendationResult:
    prepared = prepare_scoring_data(config)
    feature_cols = _feature_set_for_model(config, model_name, prepared.feature_cols)
    model_fn = _model_callable(model_name)
    model_kwargs = _model_kwargs(config, model_name)

    months = sorted(prepared.training_sample["eom"].unique())
    windows = build_rolling_windows(months, config.cv.train_months, config.cv.val_months, config.cv.test_months, config.cv.step_months)
    if not windows:
        raise RuntimeError("No rolling windows available for recommendations.")
    last_window = windows[-1]

    tr = prepared.training_sample[prepared.training_sample["eom"].isin(last_window.train_months)].dropna(subset=feature_cols + ["ret_exc_lead1m"]).copy()
    va = prepared.training_sample[prepared.training_sample["eom"].isin(last_window.val_months)].dropna(subset=feature_cols + ["ret_exc_lead1m"]).copy()
    latest = prepared.latest_sample.dropna(subset=feature_cols).copy()
    if len(latest) == 0:
        raise RuntimeError("No latest-month rows available after preprocessing.")

    fit = model_fn(
        tr[feature_cols].to_numpy(float),
        tr["ret_exc_lead1m"].to_numpy(float),
        va[feature_cols].to_numpy(float),
        va["ret_exc_lead1m"].to_numpy(float),
        latest[feature_cols].to_numpy(float),
        **model_kwargs,
    )

    raw_latest = prepared.latest_raw.copy()
    raw_latest["eom"] = pd.to_datetime(raw_latest["eom"]).dt.to_period("M").dt.to_timestamp("M")
    raw_latest["id"] = raw_latest["id"].astype(str)
    raw_keep = ["id", "eom", "prc", "me", "adv_med", "turn", "mom1m", "mom6m", "ret_12_1", "be_me"]
    raw_keep = [c for c in raw_keep if c in raw_latest.columns]

    out = latest[["id", "eom"]].copy()
    out = out.merge(raw_latest[raw_keep].drop_duplicates(["id", "eom"]), on=["id", "eom"], how="left")
    out["yhat_next_period"] = fit.y_pred
    out = out.sort_values("yhat_next_period", ascending=False).reset_index(drop=True)
    out["rank"] = range(1, len(out) + 1)
    out = out.head(int(top_k)).copy()

    return RecommendationResult(
        model_name=model_name.upper(),
        latest_eom=pd.Timestamp(latest["eom"].max()),
        train_start=pd.Timestamp(last_window.train_months[0]),
        train_end=pd.Timestamp(last_window.train_months[-1]),
        val_start=pd.Timestamp(last_window.val_months[0]),
        val_end=pd.Timestamp(last_window.val_months[-1]),
        recommendations=out[["rank", "id", "eom", "yhat_next_period"] + [c for c in ["prc", "me", "adv_med", "turn", "mom1m", "mom6m", "ret_12_1", "be_me"] if c in out.columns]],
    )
