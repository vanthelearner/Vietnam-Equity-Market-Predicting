from __future__ import annotations

import numpy as np
import pandas as pd


def build_benchmark_monthly(benchmark_monthly: pd.DataFrame, rf_monthly: pd.DataFrame) -> pd.DataFrame:
    out = benchmark_monthly.copy()
    out["eom"] = pd.to_datetime(out["eom"]).dt.to_period("M").dt.to_timestamp("M")
    out = out.merge(rf_monthly[["eom", "rf_1m"]], on="eom", how="left")
    out["benchmark_exc"] = out["benchmark_ret"] - out["rf_1m"]
    return out.sort_values("eom").reset_index(drop=True)


def compare_vs_benchmark(ls_cost_df: pd.DataFrame, benchmark_df: pd.DataFrame, *, model_name: str, cost_bps: int) -> pd.DataFrame:
    ls = ls_cost_df.copy()
    ls["eom"] = pd.to_datetime(ls["eom"]).dt.to_period("M").dt.to_timestamp("M")
    rows = []
    for label, strat_col in [("equal", f"net_excess_ew_{cost_bps}bps"), ("value", f"net_excess_vw_{cost_bps}bps")]:
        aligned = ls[["eom", strat_col]].merge(benchmark_df[["eom", "benchmark_exc"]], on="eom", how="inner")
        active = aligned[strat_col] - aligned["benchmark_exc"]
        ir = float(active.mean() / active.std(ddof=1)) if len(active) > 1 and active.std(ddof=1) > 0 else np.nan
        rows.append({
            "weighting": label,
            "strategy": f"{model_name}_LS_{'EW' if label == 'equal' else 'VW'}_net_{cost_bps}bps",
            "benchmark": f"benchmark_{label}_excess",
            "n_months": int(len(aligned)),
            "mean_active_return": float(active.mean()) if len(active) else np.nan,
            "information_ratio": ir,
            "corr_strategy_benchmark": float(aligned[strat_col].corr(aligned['benchmark_exc'])) if len(aligned) else np.nan,
        })
    return pd.DataFrame(rows)
