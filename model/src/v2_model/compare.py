from __future__ import annotations

import collections
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import t
from sklearn.utils.validation import check_array


def dm_test(e1, e2, alternative: str = "two_sided", h: int = 1, power: int = 2):
    alternatives = ["two_sided", "less", "greater"]
    if alternative not in alternatives:
        raise ValueError(f"alternative must be one of {alternatives}")
    e1 = check_array(e1, ensure_2d=False)
    e2 = check_array(e2, ensure_2d=False)
    d = np.abs(e1) ** power - np.abs(e2) ** power
    n = d.shape[0]
    d_cov = sm.tsa.acovf(d, fft=True, nlag=h - 1)
    d_var = (d_cov[0] + 2 * d_cov[1:].sum()) / n
    if d_var > 0:
        dm_stat = np.mean(d) / np.sqrt(d_var)
    elif h == 1:
        raise ValueError("Variance of DM statistic is zero")
    else:
        warnings.warn("Variance is negative, using horizon h=1", RuntimeWarning)
        return dm_test(e1, e2, alternative=alternative, h=1, power=power)
    k = ((n + 1 - 2 * h + h / n * (h - 1)) / n) ** 0.5
    dm_stat *= k
    if alternative == "two_sided":
        p_value = 2 * t.cdf(-abs(dm_stat), df=n - 1)
    else:
        p_value = t.cdf(dm_stat, df=n - 1)
        if alternative == "greater":
            p_value = 1 - p_value
    out = collections.namedtuple("dm_test_result", ["dm_stat", "p_value"])
    return out(dm_stat=dm_stat, p_value=p_value)


def build_dm_table(predictions_by_model: dict[str, pd.DataFrame]) -> pd.DataFrame:
    model_names = list(predictions_by_model.keys())
    merged = None
    for m in model_names:
        p = predictions_by_model[m][["eom", "id", "yhat", "y_true"]].copy().rename(columns={"yhat": m, "y_true": "y_true_ref"})
        merged = p if merged is None else merged.merge(p[["eom", "id", m]], on=["eom", "id"], how="inner")
    if merged is None or len(merged) == 0:
        return pd.DataFrame(index=model_names, columns=model_names)
    y_true = merged["y_true_ref"].to_numpy(dtype=float)
    dm_table = pd.DataFrame(index=model_names, columns=model_names, dtype=object)
    for i, m1 in enumerate(model_names):
        for j, m2 in enumerate(model_names):
            if i == j:
                dm_table.loc[m1, m2] = 0.0
                continue
            e1 = y_true - merged[m1].to_numpy(dtype=float)
            e2 = y_true - merged[m2].to_numpy(dtype=float)
            if np.allclose(e1, e2):
                dm_table.loc[m1, m2] = 0.0
                continue
            try:
                stat, pval = dm_test(e1, e2, alternative="two_sided", h=1, power=2)
                tag = ""
                if pval <= 0.10:
                    tag = "*"
                if pval <= 0.05:
                    tag = "**"
                if pval <= 0.01:
                    tag = "***"
                dm_table.loc[m1, m2] = f"{float(stat):.6f}{tag}"
            except Exception:
                dm_table.loc[m1, m2] = np.nan
    return dm_table.reset_index().rename(columns={"index": "model"})


def merge_variable_importance(importance_by_model: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = None
    for model_name, df_imp in importance_by_model.items():
        if df_imp is None or len(df_imp) == 0:
            continue
        d = df_imp[["Feature", "var_imp"]].copy().rename(columns={"var_imp": model_name})
        merged = d if merged is None else merged.merge(d, on="Feature", how="outer")
    if merged is None:
        return pd.DataFrame(), pd.DataFrame()
    merged = merged.sort_values("Feature").reset_index(drop=True)
    rank_df = merged.copy()
    for c in rank_df.columns:
        if c == "Feature":
            continue
        rank_df[c + "_rank"] = rank_df[c].rank(ascending=False, method="min")
    return merged, rank_df


def build_cumulative_tables(top_bottom_by_model: dict[str, pd.DataFrame], benchmark_monthly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    bench = benchmark_monthly[["eom", "benchmark_ret"]].copy().sort_values("eom").set_index("eom")
    ew = bench.rename(columns={"benchmark_ret": "benchmark_ret"}).copy()
    vw = bench.rename(columns={"benchmark_ret": "benchmark_ret"}).copy()
    for m, tb in top_bottom_by_model.items():
        t = tb.copy()
        t["eom"] = pd.to_datetime(t["eom"])
        t = t.sort_values("eom").set_index("eom")
        ew[f"{m}_long"] = t["long_ret_ew"]
        ew[f"{m}_short"] = t["short_ret_ew"]
        vw[f"{m}_long"] = t["long_ret_vw"]
        vw[f"{m}_short"] = t["short_ret_vw"]
    ew = ew.dropna(how="all")
    vw = vw.dropna(how="all")
    ew_cum = (1.0 + ew).cumprod().reset_index()
    vw_cum = (1.0 + vw).cumprod().reset_index()
    return ew_cum, vw_cum
