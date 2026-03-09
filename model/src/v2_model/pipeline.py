from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from .benchmark import build_benchmark_monthly, compare_vs_benchmark
from .compare import build_cumulative_tables, build_dm_table, merge_variable_importance
from .config import DEFAULT_MODELS, PipelineConfig
from .cv import RollingWindow, build_rolling_windows
from .io import ensure_dir, timestamped_run_dir, write_df, write_json
from .models.base import WindowFitResult, r2_oos_zero
from .models import enet, gbrt, nn, ols3_huber, ols_huber, pcr, pls, rf
from .portfolio import build_decile_monthly, build_decile_table, build_long_short_long_only, summarize_performance
from .prepare_inputs import build_monthly_inputs
from .preprocess import PreparedData, prepare_data


@dataclass
class SingleModelArtifacts:
    model_name: str
    r2_summary: pd.DataFrame
    windows_full: pd.DataFrame
    windows_large: pd.DataFrame
    windows_small: pd.DataFrame
    pred_full: pd.DataFrame
    pred_large: pd.DataFrame
    pred_small: pd.DataFrame
    complexity: pd.DataFrame
    feature_importance: pd.DataFrame
    decile_monthly: pd.DataFrame
    decile_table_ew: pd.DataFrame
    decile_table_vw: pd.DataFrame
    long_short: pd.DataFrame
    long_only: pd.DataFrame
    performance_summary: pd.DataFrame
    benchmark_compare: pd.DataFrame
    benchmark_monthly: pd.DataFrame
    top_bottom: pd.DataFrame


def _model_callable(model_name: str):
    key = model_name.upper()
    if key == "OLS":
        return ols_huber.run_window
    if key == "OLS3":
        return ols3_huber.run_window
    if key == "ENET":
        return enet.run_window
    if key == "PLS":
        return pls.run_window
    if key == "PCR":
        return pcr.run_window
    if key == "GBRT":
        return gbrt.run_window
    if key == "RF":
        return rf.run_window
    if key == "NN":
        return nn.run_window
    raise ValueError(f"Unsupported model: {model_name}")


def _model_kwargs(config: PipelineConfig, model_name: str) -> dict:
    key = model_name.upper()
    if key == "OLS":
        return dict(config.models.ols)
    if key == "OLS3":
        return {k: v for k, v in dict(config.models.ols3).items() if k != "fixed_features"}
    if key == "ENET":
        out = dict(config.models.enet)
        out["random_state"] = config.runtime.seed
        return out
    if key == "PLS":
        return dict(config.models.pls)
    if key == "PCR":
        return dict(config.models.pcr)
    if key == "GBRT":
        out = dict(config.models.gbrt)
        out["random_state"] = config.runtime.seed
        return out
    if key == "RF":
        out = dict(config.models.rf)
        out["random_state"] = config.runtime.seed
        out["n_jobs"] = config.runtime.n_jobs
        return out
    if key == "NN":
        out = dict(config.models.nn)
        out["random_state"] = config.runtime.seed
        return out
    raise ValueError(f"Unsupported model: {model_name}")


def _feature_set_for_model(config: PipelineConfig, model_name: str, feature_cols: list[str]) -> list[str]:
    key = model_name.upper()
    if key != "OLS3":
        return list(feature_cols)
    fixed = list(config.models.ols3.get("fixed_features", ["me", "be_me", "ret_12_1"]))
    missing = [c for c in fixed if c not in feature_cols]
    if missing:
        raise ValueError(f"OLS3 fixed features missing from dataset: {missing}")
    return fixed


def _window_table(windows: list[RollingWindow]) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "window_id": w.window_id,
            "train_start": w.train_months[0],
            "train_end": w.train_months[-1],
            "val_start": w.val_months[0],
            "val_end": w.val_months[-1],
            "test_start": w.test_months[0],
            "test_end": w.test_months[-1],
        }
        for w in windows
    ])


def _run_sample(df_sample: pd.DataFrame, sample_name: str, feature_cols: list[str], target_col: str, windows: list[RollingWindow], model_fn: Callable[..., WindowFitResult], model_kwargs: dict) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    pred_chunks = []
    win_rows = []
    for w in windows:
        tr = df_sample[df_sample["eom"].isin(w.train_months)].dropna(subset=feature_cols + [target_col]).copy()
        va = df_sample[df_sample["eom"].isin(w.val_months)].dropna(subset=feature_cols + [target_col]).copy()
        te = df_sample[df_sample["eom"].isin(w.test_months)].dropna(subset=feature_cols + [target_col]).copy()
        base_row = {
            "sample": sample_name,
            "window_id": w.window_id,
            "train_start": w.train_months[0],
            "train_end": w.train_months[-1],
            "val_start": w.val_months[0],
            "val_end": w.val_months[-1],
            "test_start": w.test_months[0],
            "test_end": w.test_months[-1],
            "n_train": int(len(tr)),
            "n_val": int(len(va)),
            "n_test": int(len(te)),
        }
        if len(tr) == 0 or len(va) == 0 or len(te) == 0:
            win_rows.append({**base_row, "r2_window": np.nan})
            continue
        fit = model_fn(
            tr[feature_cols].to_numpy(float),
            tr[target_col].to_numpy(float),
            va[feature_cols].to_numpy(float),
            va[target_col].to_numpy(float),
            te[feature_cols].to_numpy(float),
            **model_kwargs,
        )
        r2w = r2_oos_zero(te[target_col].to_numpy(float), fit.y_pred)
        row = {**base_row, "best_score": float(fit.best_score), "r2_window": float(r2w) if pd.notna(r2w) else np.nan}
        for k, v in fit.best_params.items():
            row[f"best_{k}"] = v
        for k, v in fit.complexity.items():
            row[k] = v
        win_rows.append(row)
        out = te[["eom", "id", "me2", "ret_lead1m", target_col]].copy().rename(columns={target_col: "y_true"})
        out["yhat"] = fit.y_pred
        out["sample"] = sample_name
        out["window_id"] = w.window_id
        pred_chunks.append(out)
    pred_df = pd.concat(pred_chunks, ignore_index=True) if pred_chunks else pd.DataFrame()
    win_df = pd.DataFrame(win_rows)
    r2_total = r2_oos_zero(pred_df["y_true"].to_numpy(float), pred_df["yhat"].to_numpy(float)) if len(pred_df) else np.nan
    return pred_df, win_df, float(r2_total) if pd.notna(r2_total) else np.nan


def _feature_importance_last_window(df_full: pd.DataFrame, feature_cols: list[str], target_col: str, windows: list[RollingWindow], model_fn: Callable[..., WindowFitResult], model_kwargs: dict, run_flag: bool) -> pd.DataFrame:
    if not run_flag or not windows:
        return pd.DataFrame()
    w = windows[-1]
    tr = df_full[df_full["eom"].isin(w.train_months)].dropna(subset=feature_cols + [target_col]).copy()
    va = df_full[df_full["eom"].isin(w.val_months)].dropna(subset=feature_cols + [target_col]).copy()
    base = pd.concat([tr, va], ignore_index=True)
    if len(tr) == 0 or len(va) == 0 or len(base) == 0:
        return pd.DataFrame()
    fit_base = model_fn(tr[feature_cols].to_numpy(float), tr[target_col].to_numpy(float), va[feature_cols].to_numpy(float), va[target_col].to_numpy(float), base[feature_cols].to_numpy(float), **model_kwargs)
    y_base = base[target_col].to_numpy(float)
    r2_base = r2_oos_zero(y_base, fit_base.y_pred)
    rows = []
    for f in feature_cols:
        tr0 = tr.copy(); va0 = va.copy(); base0 = base.copy()
        tr0[f] = 0.0; va0[f] = 0.0; base0[f] = 0.0
        fit_f = model_fn(tr0[feature_cols].to_numpy(float), tr0[target_col].to_numpy(float), va0[feature_cols].to_numpy(float), va0[target_col].to_numpy(float), base0[feature_cols].to_numpy(float), **model_kwargs)
        r2_f = r2_oos_zero(base0[target_col].to_numpy(float), fit_f.y_pred)
        rows.append({"Feature": f, "R2OOS": r2_f})
    imp = pd.DataFrame(rows)
    imp["red_R2OOS"] = float(r2_base) - imp["R2OOS"]
    denom = imp["red_R2OOS"].sum()
    imp["var_imp"] = imp["red_R2OOS"] / denom if denom != 0 else np.nan
    return imp.sort_values("var_imp", ascending=False).reset_index(drop=True)


def _run_single_model(prepared: PreparedData, config: PipelineConfig, model_name: str, windows: list[RollingWindow]) -> SingleModelArtifacts:
    model_fn = _model_callable(model_name)
    kwargs = _model_kwargs(config, model_name)
    feat_cols = _feature_set_for_model(config, model_name, prepared.feature_cols)
    target_col = "ret_exc_lead1m"
    pred_full, win_full, r2_full = _run_sample(prepared.full, "Full sample", feat_cols, target_col, windows, model_fn, kwargs)
    pred_large, win_large, r2_large = _run_sample(prepared.large, "Large firms", feat_cols, target_col, windows, model_fn, kwargs)
    pred_small, win_small, r2_small = _run_sample(prepared.small, "Small firms", feat_cols, target_col, windows, model_fn, kwargs)
    r2_summary = pd.DataFrame([
        {"sample": "Full sample", f"R2OOS_{model_name}": r2_full, "n_rows": int(len(pred_full)), "n_months": int(pred_full['eom'].nunique()) if len(pred_full) else 0},
        {"sample": "Large firms", f"R2OOS_{model_name}": r2_large, "n_rows": int(len(pred_large)), "n_months": int(pred_large['eom'].nunique()) if len(pred_large) else 0},
        {"sample": "Small firms", f"R2OOS_{model_name}": r2_small, "n_rows": int(len(pred_small)), "n_months": int(pred_small['eom'].nunique()) if len(pred_small) else 0},
    ])
    complexity_cols = {"window_id", "test_start", "test_end", "best_alpha", "n_nonzero_coef", "n_components", "best_max_depth", "best_max_features"}
    complexity = win_full[[c for c in win_full.columns if c in complexity_cols or c.startswith("best_")]].copy()
    if len(complexity) == 0:
        complexity = win_full[["window_id", "test_start", "test_end"]].copy()
    feature_importance = _feature_importance_last_window(prepared.full, feat_cols, target_col, windows, model_fn, kwargs, run_flag=config.runtime.run_variable_importance)
    port, decile_monthly = build_decile_monthly(pred_full, n_deciles=config.portfolio.n_deciles)
    decile_table_ew = build_decile_table(decile_monthly, "ew")
    decile_table_vw = build_decile_table(decile_monthly, "vw")
    long_short, long_only, top_bottom = build_long_short_long_only(port, decile_monthly, cost_bps_list=config.portfolio.cost_bps_list)
    performance_summary = summarize_performance(model_name=model_name, ls=long_short, long_only=long_only, cost_bps_list=config.portfolio.cost_bps_list)
    bench_monthly = build_benchmark_monthly(prepared.benchmark_monthly, prepared.rf_monthly)
    benchmark_compare = compare_vs_benchmark(long_short, bench_monthly, model_name=model_name, cost_bps=config.portfolio.benchmark_cost_bps)
    return SingleModelArtifacts(model_name, r2_summary, win_full, win_large, win_small, pred_full, pred_large, pred_small, complexity, feature_importance, decile_monthly, decile_table_ew, decile_table_vw, long_short, long_only, performance_summary, benchmark_compare, bench_monthly, top_bottom)


def _save_model_artifacts(run_dir: Path, art: SingleModelArtifacts) -> None:
    key = art.model_name.lower()
    write_df(art.r2_summary, run_dir / "r2" / f"{key}_r2_summary_full_large_small.csv")
    write_df(art.windows_full, run_dir / "windows" / f"{key}_window_summary_full.csv")
    write_df(art.windows_large, run_dir / "windows" / f"{key}_window_summary_large.csv")
    write_df(art.windows_small, run_dir / "windows" / f"{key}_window_summary_small.csv")
    write_df(art.pred_full, run_dir / "predictions" / f"{key}_predictions_full.csv")
    write_df(art.pred_large, run_dir / "predictions" / f"{key}_predictions_large.csv")
    write_df(art.pred_small, run_dir / "predictions" / f"{key}_predictions_small.csv")
    write_df(art.complexity, run_dir / "complexity" / f"{key}_complexity.csv")
    if len(art.feature_importance):
        write_df(art.feature_importance, run_dir / "importance" / f"{key}_feature_importance.csv")
    write_df(art.decile_monthly, run_dir / "portfolio" / f"{key}_decile_monthly.csv")
    write_df(art.decile_table_ew, run_dir / "portfolio" / f"{key}_decile_table_ew.csv")
    write_df(art.decile_table_vw, run_dir / "portfolio" / f"{key}_decile_table_vw.csv")
    write_df(art.long_short, run_dir / "portfolio" / f"{key}_long_short_cost_grid.csv")
    write_df(art.long_only, run_dir / "portfolio" / f"{key}_long_only_cost_grid.csv")
    write_df(art.performance_summary, run_dir / "portfolio" / f"{key}_performance_summary.csv")
    write_df(art.benchmark_monthly, run_dir / "benchmark" / f"{key}_benchmark_monthly.csv")
    write_df(art.benchmark_compare, run_dir / "benchmark" / f"{key}_vs_benchmark.csv")


def run_pipeline(config: PipelineConfig, selected_models: list[str], selected_stages: list[str], config_path: str) -> Path:
    stages = {s.lower() for s in selected_stages}
    if "all" in stages:
        stages = {"prepare", "train", "compare"}
    models = [m.upper() for m in selected_models]
    if len(models) == 1 and models[0] == "ALL":
        models = DEFAULT_MODELS

    prepared_outputs = None
    if stages.intersection({"prepare", "train", "compare"}):
        prepared_outputs = build_monthly_inputs(config)

    if stages == {"prepare"}:
        return Path(config.paths.output_dir)

    run_dir = timestamped_run_dir(config.paths.output_dir)
    ensure_dir(run_dir)
    prepared = prepare_data(config)
    write_df(prepared.preprocess_report, run_dir / "preprocess" / "preprocess_report.csv")
    write_df(pd.DataFrame({"feature": prepared.feature_cols}), run_dir / "preprocess" / "feature_list.csv")
    write_df(prepared.rf_monthly, run_dir / "preprocess" / "rf_monthly_inferred.csv")
    write_df(prepared.benchmark_monthly, run_dir / "preprocess" / "benchmark_monthly_input.csv")
    if prepared_outputs is not None:
        write_df(prepared_outputs["panel_summary"], run_dir / "preprocess" / "panel_prep_summary.csv")
        write_df(prepared_outputs["benchmark_summary"], run_dir / "preprocess" / "benchmark_prep_summary.csv")
        write_df(prepared_outputs["window_coverage"], run_dir / "preprocess" / "window_coverage_summary.csv")

    months = sorted(prepared.full["eom"].unique())
    windows = build_rolling_windows(months, config.cv.train_months, config.cv.val_months, config.cv.test_months, config.cv.step_months)
    if config.runtime.smoke_test:
        windows = windows[:2]
    if len(windows) == 0:
        raise RuntimeError("No rolling windows generated. Check dataset length and CV settings.")
    write_df(_window_table(windows), run_dir / "preprocess" / "window_map.csv")

    artifacts: dict[str, SingleModelArtifacts] = {}
    if stages.intersection({"train", "compare"}):
        for model_name in models:
            art = _run_single_model(prepared, config, model_name, windows)
            artifacts[model_name] = art
            _save_model_artifacts(run_dir, art)

    if "compare" in stages and artifacts:
        r2_all = None
        for m, art in artifacts.items():
            tmp = art.r2_summary[["sample", f"R2OOS_{m}"]].copy()
            r2_all = tmp if r2_all is None else r2_all.merge(tmp, on="sample", how="outer")
        if r2_all is not None:
            write_df(r2_all, run_dir / "compare" / "r2_summary_all_models.csv")
        preds_for_dm = {m: art.pred_full for m, art in artifacts.items() if len(art.pred_full)}
        if len(preds_for_dm) >= 2:
            write_df(build_dm_table(preds_for_dm), run_dir / "compare" / "dm_table.csv")
        imp_merged, imp_rank = merge_variable_importance({m: art.feature_importance for m, art in artifacts.items()})
        if len(imp_merged):
            write_df(imp_merged, run_dir / "compare" / "variable_importance_merged.csv")
            write_df(imp_rank, run_dir / "compare" / "variable_importance_ranked.csv")
        top_bottom_map = {m: art.top_bottom for m, art in artifacts.items() if len(art.top_bottom)}
        if top_bottom_map:
            benchmark_monthly = next(iter(artifacts.values())).benchmark_monthly
            cum_ew, cum_vw = build_cumulative_tables(top_bottom_map, benchmark_monthly)
            write_df(cum_ew, run_dir / "compare" / "cumulative_ew_all_models.csv")
            write_df(cum_vw, run_dir / "compare" / "cumulative_vw_all_models.csv")

    manifest = {
        "config_path": str(config_path),
        "selected_models": models,
        "selected_stages": sorted(stages),
        "run_dir": str(run_dir),
        "n_windows": len(windows),
        "n_features": len(prepared.feature_cols),
        "n_assets_full": int(prepared.full['id'].nunique()),
        "date_min": str(prepared.full['eom'].min().date()),
        "date_max": str(prepared.full['eom'].max().date()),
    }
    write_json(manifest, run_dir / "meta" / "run_manifest.json")
    return run_dir
