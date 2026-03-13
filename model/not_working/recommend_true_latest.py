from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import LIQUIDITY_KEEP_SHARE, PipelineConfig
from .pipeline import _feature_set_for_model, _model_callable, _model_kwargs
from .feature_profiles import REQUIRED_PANEL_COLS
from .preprocess import (
    RESERVED_EXCLUDE_FEATURES,
    _load_inputs,
    _rank_scale_minus1_to_1,
    _winsorize_by_month,
)


@dataclass
class TrueLatestRecommendationResult:
    model_name: str
    score_eom: pd.Timestamp
    latest_labeled_eom: pd.Timestamp
    train_start: pd.Timestamp
    train_end: pd.Timestamp
    val_start: pd.Timestamp
    val_end: pd.Timestamp
    universe_rows: int
    scored_rows: int
    recommendations: pd.DataFrame


def _build_latest_calibration_months(months: list[pd.Timestamp], train_months: int, val_months: int) -> tuple[list[pd.Timestamp], list[pd.Timestamp]]:
    months = sorted(pd.Timestamp(m) for m in months)
    need = train_months + val_months
    if len(months) < need:
        raise RuntimeError(f"Not enough labeled months for live recommendation calibration: need {need}, have {len(months)}")
    val = months[-val_months:]
    train = months[-need:-val_months]
    return train, val


def _prepare_true_latest_scoring_panel(config: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str], pd.Timestamp]:
    panel, _, _, _ = _load_inputs(config)
    score_eom = pd.Timestamp(panel["eom"].max())

    panel = panel.loc[(panel["prc"] >= config.preprocess.min_price) & (panel["me"] >= config.preprocess.min_me)].copy()

    keep_share = LIQUIDITY_KEEP_SHARE[config.preprocess.liquidity_category]
    panel["liq_rank_pct"] = panel.groupby("eom", sort=False)["adv_med"].rank(pct=True)
    panel["is_liquid"] = panel["liq_rank_pct"] >= (1.0 - keep_share)
    panel = panel.loc[panel["is_liquid"]].copy()

    if config.preprocess.date_start:
        dt0 = pd.to_datetime(config.preprocess.date_start)
        panel = panel.loc[panel["eom"] >= dt0].copy()

    latest_raw = panel.loc[panel["eom"] == score_eom].copy()

    labeled = panel.loc[(panel["eom"] < score_eom) & panel["ret_exc_lead1m"].notna()].copy()
    if len(labeled) == 0:
        raise RuntimeError("No labeled rows are available before the true latest scoring month.")

    coverage = labeled.notna().mean()
    keep_cols = [
        c for c in panel.columns
        if (coverage.get(c, 0.0) >= config.preprocess.min_col_coverage) or (c in REQUIRED_PANEL_COLS)
    ]
    panel = panel[keep_cols].copy()

    required_no_lead = [c for c in REQUIRED_PANEL_COLS if c != "ret_exc_lead1m" and c in panel.columns]
    num_cols = [c for c in panel.columns if pd.api.types.is_numeric_dtype(panel[c]) and not pd.api.types.is_bool_dtype(panel[c])]
    panel[num_cols] = panel[num_cols].replace([float('inf'), float('-inf')], np.nan)
    panel[num_cols] = panel.groupby("eom", sort=False)[num_cols].transform(lambda g: g.fillna(g.median()))
    panel = panel.dropna(subset=required_no_lead).copy()

    panel = panel.sort_values(["id", "eom"]).reset_index(drop=True)
    panel["ret_lead1m"] = panel.groupby("id", sort=False)["ret"].shift(-1)
    panel["me2"] = panel["me"]

    training_sample = panel.loc[panel["eom"] < score_eom].dropna(subset=["ret_lead1m", "ret_exc_lead1m", "me", "be_me", "ret_12_1"]).copy()
    if len(training_sample) == 0:
        raise RuntimeError("No training rows remain after building the true latest recommendation sample.")

    feature_cols = [
        c for c in training_sample.columns
        if pd.api.types.is_numeric_dtype(training_sample[c])
        and not pd.api.types.is_bool_dtype(training_sample[c])
        and c not in RESERVED_EXCLUDE_FEATURES
    ]
    for must in ["me", "be_me", "ret_12_1"]:
        if must in training_sample.columns and must not in feature_cols:
            feature_cols.append(must)

    transformed_all = _winsorize_by_month(
        panel,
        [c for c in feature_cols if c in panel.columns],
        "eom",
        config.preprocess.winsor_lower,
        config.preprocess.winsor_upper,
    )
    transformed_all = _rank_scale_minus1_to_1(
        transformed_all,
        [c for c in feature_cols if c in transformed_all.columns],
        "eom",
    )

    latest_sample = transformed_all.loc[transformed_all["eom"] == score_eom].copy()
    return training_sample, latest_sample, latest_raw, sorted(set(feature_cols)), score_eom


def build_true_latest_recommendations(config: PipelineConfig, model_name: str, top_k: int = 10) -> TrueLatestRecommendationResult:
    training_sample, latest_sample, latest_raw, feature_cols, score_eom = _prepare_true_latest_scoring_panel(config)
    feature_cols = _feature_set_for_model(config, model_name, feature_cols)
    model_fn = _model_callable(model_name)
    model_kwargs = _model_kwargs(config, model_name)

    labeled_months = sorted(training_sample["eom"].unique())
    train_months, val_months = _build_latest_calibration_months(labeled_months, config.cv.train_months, config.cv.val_months)
    latest_labeled_eom = pd.Timestamp(labeled_months[-1])

    tr = training_sample.loc[training_sample["eom"].isin(train_months)].copy()
    va = training_sample.loc[training_sample["eom"].isin(val_months)].copy()
    latest = latest_sample.copy()

    for frame in (tr, va, latest):
        frame[feature_cols] = frame[feature_cols].replace([float('inf'), float('-inf')], np.nan)

    tr = tr.dropna(subset=feature_cols + ["ret_exc_lead1m"]).copy()
    va = va.dropna(subset=feature_cols + ["ret_exc_lead1m"]).copy()
    latest = latest.dropna(subset=feature_cols).copy()

    bad_cols = [c for c in feature_cols if (not pd.api.types.is_numeric_dtype(tr[c])) or (not pd.Series(tr[c]).replace([float('inf'), float('-inf')], np.nan).dropna().empty and not np.isfinite(pd.to_numeric(tr[c], errors='coerce').dropna()).all())]
    if bad_cols:
        raise RuntimeError(f"Selected feature columns still contain non-finite values after cleanup: {bad_cols}")
    if len(latest) == 0:
        raise RuntimeError("No true-latest rows remain after feature availability checks.")

    fit = model_fn(
        tr[feature_cols].to_numpy(float),
        tr["ret_exc_lead1m"].to_numpy(float),
        va[feature_cols].to_numpy(float),
        va["ret_exc_lead1m"].to_numpy(float),
        latest[feature_cols].to_numpy(float),
        **model_kwargs,
    )

    latest_raw = latest_raw.copy()
    latest_raw["eom"] = pd.to_datetime(latest_raw["eom"]).dt.to_period("M").dt.to_timestamp("M")
    latest_raw["id"] = latest_raw["id"].astype(str)
    raw_keep = ["id", "eom", "prc", "me", "adv_med", "turn", "mom1m", "mom6m", "ret_12_1", "be_me"]
    raw_keep = [c for c in raw_keep if c in latest_raw.columns]

    out = latest[["id", "eom"]].copy()
    out = out.merge(latest_raw[raw_keep].drop_duplicates(["id", "eom"]), on=["id", "eom"], how="left")
    out["yhat_next_period"] = fit.y_pred
    out = out.sort_values("yhat_next_period", ascending=False).reset_index(drop=True)
    out["rank"] = range(1, len(out) + 1)
    out = out.head(int(top_k)).copy()

    return TrueLatestRecommendationResult(
        model_name=model_name.upper(),
        score_eom=pd.Timestamp(score_eom),
        latest_labeled_eom=latest_labeled_eom,
        train_start=pd.Timestamp(train_months[0]),
        train_end=pd.Timestamp(train_months[-1]),
        val_start=pd.Timestamp(val_months[0]),
        val_end=pd.Timestamp(val_months[-1]),
        universe_rows=int(len(latest_raw)),
        scored_rows=int(len(latest)),
        recommendations=out[["rank", "id", "eom", "yhat_next_period"] + [c for c in ["prc", "me", "adv_med", "turn", "mom1m", "mom6m", "ret_12_1", "be_me"] if c in out.columns]],
    )
