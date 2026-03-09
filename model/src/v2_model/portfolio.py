from __future__ import annotations

import numpy as np
import pandas as pd


def assign_deciles(s: pd.Series, n_deciles: int) -> pd.Series:
    if s.notna().sum() < n_deciles or s.nunique(dropna=True) < n_deciles:
        return pd.Series(np.nan, index=s.index)
    ranks = s.rank(method="first")
    return pd.qcut(ranks, q=n_deciles, labels=False, duplicates="drop")


def build_decile_monthly(pred_full: pd.DataFrame, n_deciles: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    port = pred_full.dropna(subset=["eom", "id", "yhat", "y_true", "me2", "ret_lead1m"]).copy()
    port["DecileRank"] = port.groupby("eom", sort=False)["yhat"].apply(lambda s: assign_deciles(s, n_deciles)).reset_index(level=0, drop=True)
    port = port.dropna(subset=["DecileRank"]).copy()
    port["DecileRank"] = port["DecileRank"].astype(int)
    port["eq_weights"] = 1.0 / port.groupby(["eom", "DecileRank"], sort=False)["id"].transform("size")
    port["me_weights"] = port["me2"] / port.groupby(["eom", "DecileRank"], sort=False)["me2"].transform("sum")
    port["excess_return_stock_ew"] = port["y_true"] * port["eq_weights"]
    port["excess_return_stock_vw"] = port["y_true"] * port["me_weights"]
    port["return_stock_ew"] = port["ret_lead1m"] * port["eq_weights"]
    port["return_stock_vw"] = port["ret_lead1m"] * port["me_weights"]
    port["pred_excess_stock_ew"] = port["yhat"] * port["eq_weights"]
    port["pred_excess_stock_vw"] = port["yhat"] * port["me_weights"]
    decile_monthly = (
        port.groupby(["eom", "DecileRank"], as_index=False)
        .agg(
            excess_return_portfolio_ew=("excess_return_stock_ew", "sum"),
            excess_return_portfolio_vw=("excess_return_stock_vw", "sum"),
            return_portfolio_ew=("return_stock_ew", "sum"),
            return_portfolio_vw=("return_stock_vw", "sum"),
            pred_excess_return_portfolio_ew=("pred_excess_stock_ew", "sum"),
            pred_excess_return_portfolio_vw=("pred_excess_stock_vw", "sum"),
            n_stocks=("id", "nunique"),
        )
        .sort_values(["eom", "DecileRank"]).reset_index(drop=True)
    )
    return port, decile_monthly


def build_decile_table(decile_monthly: pd.DataFrame, weighting: str) -> pd.DataFrame:
    pred_col = "pred_excess_return_portfolio_ew" if weighting == "ew" else "pred_excess_return_portfolio_vw"
    real_col = "excess_return_portfolio_ew" if weighting == "ew" else "excess_return_portfolio_vw"
    raw_col = "return_portfolio_ew" if weighting == "ew" else "return_portfolio_vw"
    rows = []
    for d in sorted(decile_monthly["DecileRank"].unique()):
        g = decile_monthly[decile_monthly["DecileRank"] == d]
        rows.append({
            "rank": int(d),
            "Pred": float(g[pred_col].mean()),
            "Real": float(g[real_col].mean()),
            "Std": float(g[real_col].std(ddof=1)) if len(g) > 1 else np.nan,
            "Sharpe": float((g[real_col].mean() / g[raw_col].std(ddof=1)) * np.sqrt(12)) if len(g) > 1 and g[raw_col].std(ddof=1) > 0 else np.nan,
        })
    top = decile_monthly[decile_monthly["DecileRank"] == decile_monthly["DecileRank"].max()].set_index("eom")
    bot = decile_monthly[decile_monthly["DecileRank"] == decile_monthly["DecileRank"].min()].set_index("eom")
    common = top.index.intersection(bot.index)
    if len(common):
        hml_pred = top.loc[common, pred_col] - bot.loc[common, pred_col]
        hml_real = top.loc[common, real_col] - bot.loc[common, real_col]
        hml_raw = top.loc[common, raw_col] - bot.loc[common, raw_col]
        rows.append({
            "rank": "H-L",
            "Pred": float(hml_pred.mean()),
            "Real": float(hml_real.mean()),
            "Std": float(hml_real.std(ddof=1)) if len(hml_real) > 1 else np.nan,
            "Sharpe": float((hml_real.mean() / hml_raw.std(ddof=1)) * np.sqrt(12)) if len(hml_real) > 1 and hml_raw.std(ddof=1) > 0 else np.nan,
        })
    tab = pd.DataFrame(rows)
    min_rank = int(decile_monthly["DecileRank"].min())
    max_rank = int(decile_monthly["DecileRank"].max())
    tab["rank_label"] = tab["rank"].map({min_rank: "Low (L)", max_rank: "High (H)"}).fillna(tab["rank"].astype(str))
    return tab[["rank_label", "Pred", "Real", "Std", "Sharpe"]]


def _perf_stats(ret: pd.Series, periods_per_year: int = 12) -> dict:
    s = pd.Series(ret).dropna()
    if len(s) == 0:
        return {"n_periods": 0, "mean_period": np.nan, "std_period": np.nan, "ann_ret": np.nan, "ann_vol": np.nan, "sharpe": np.nan, "cum_ret": np.nan, "max_dd": np.nan, "max_1m_loss": np.nan}
    wealth = (1.0 + s).cumprod()
    ann_ret = float(wealth.iloc[-1] ** (periods_per_year / len(s)) - 1.0)
    ann_vol = float(s.std(ddof=1) * np.sqrt(periods_per_year)) if len(s) > 1 else np.nan
    sharpe = float((s.mean() / s.std(ddof=1)) * np.sqrt(periods_per_year)) if len(s) > 1 and s.std(ddof=1) > 0 else np.nan
    cum_ret = float(wealth.iloc[-1] - 1.0)
    max_dd = float((wealth / wealth.cummax() - 1.0).min())
    return {"n_periods": int(len(s)), "mean_period": float(s.mean()), "std_period": float(s.std(ddof=1)) if len(s) > 1 else np.nan, "ann_ret": ann_ret, "ann_vol": ann_vol, "sharpe": sharpe, "cum_ret": cum_ret, "max_dd": max_dd, "max_1m_loss": float(s.min())}


def build_long_short_long_only(port: pd.DataFrame, decile_monthly: pd.DataFrame, cost_bps_list: list[int]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    top_rank = int(decile_monthly["DecileRank"].max())
    bot_rank = int(decile_monthly["DecileRank"].min())
    top = decile_monthly[decile_monthly["DecileRank"] == top_rank].set_index("eom").sort_index()
    bot = decile_monthly[decile_monthly["DecileRank"] == bot_rank].set_index("eom").sort_index()
    common = top.index.intersection(bot.index)
    ls = pd.DataFrame(index=common)
    ls["gross_excess_ew"] = top.loc[common, "excess_return_portfolio_ew"] - bot.loc[common, "excess_return_portfolio_ew"]
    ls["gross_excess_vw"] = top.loc[common, "excess_return_portfolio_vw"] - bot.loc[common, "excess_return_portfolio_vw"]
    ls["gross_raw_ew"] = top.loc[common, "return_portfolio_ew"] - bot.loc[common, "return_portfolio_ew"]
    ls["gross_raw_vw"] = top.loc[common, "return_portfolio_vw"] - bot.loc[common, "return_portfolio_vw"]
    long_only = pd.DataFrame(index=top.index)
    long_only["gross_excess_ew"] = top["excess_return_portfolio_ew"]
    long_only["gross_excess_vw"] = top["excess_return_portfolio_vw"]
    long_only["gross_raw_ew"] = top["return_portfolio_ew"]
    long_only["gross_raw_vw"] = top["return_portfolio_vw"]
    const_ls = port[port["DecileRank"].isin([bot_rank, top_rank])].copy()
    const_ls["w_ls_ew"] = np.where(const_ls["DecileRank"] == top_rank, const_ls["eq_weights"], -const_ls["eq_weights"])
    const_ls["w_ls_vw"] = np.where(const_ls["DecileRank"] == top_rank, const_ls["me_weights"], -const_ls["me_weights"])
    w_ls_ew = const_ls.pivot_table(index="eom", columns="id", values="w_ls_ew", fill_value=0.0).sort_index()
    w_ls_vw = const_ls.pivot_table(index="eom", columns="id", values="w_ls_vw", fill_value=0.0).sort_index()
    turn_ls_ew = w_ls_ew.diff().abs().sum(axis=1)
    turn_ls_vw = w_ls_vw.diff().abs().sum(axis=1)
    if len(turn_ls_ew):
        turn_ls_ew.iloc[0] = w_ls_ew.iloc[0].abs().sum()
    if len(turn_ls_vw):
        turn_ls_vw.iloc[0] = w_ls_vw.iloc[0].abs().sum()
    ls = ls.join(turn_ls_ew.rename("turnover_ew")).join(turn_ls_vw.rename("turnover_vw"))
    const_long = port[port["DecileRank"] == top_rank].copy()
    w_long_ew = const_long.pivot_table(index="eom", columns="id", values="eq_weights", fill_value=0.0).sort_index()
    w_long_vw = const_long.pivot_table(index="eom", columns="id", values="me_weights", fill_value=0.0).sort_index()
    turn_long_ew = w_long_ew.diff().abs().sum(axis=1)
    turn_long_vw = w_long_vw.diff().abs().sum(axis=1)
    if len(turn_long_ew):
        turn_long_ew.iloc[0] = w_long_ew.iloc[0].abs().sum()
    if len(turn_long_vw):
        turn_long_vw.iloc[0] = w_long_vw.iloc[0].abs().sum()
    long_only = long_only.join(turn_long_ew.rename("turnover_ew")).join(turn_long_vw.rename("turnover_vw"))
    for bps in cost_bps_list:
        c = bps / 10000.0
        ls[f"net_excess_ew_{bps}bps"] = ls["gross_excess_ew"] - ls["turnover_ew"] * c
        ls[f"net_excess_vw_{bps}bps"] = ls["gross_excess_vw"] - ls["turnover_vw"] * c
        long_only[f"net_excess_ew_{bps}bps"] = long_only["gross_excess_ew"] - long_only["turnover_ew"] * c
        long_only[f"net_excess_vw_{bps}bps"] = long_only["gross_excess_vw"] - long_only["turnover_vw"] * c
    top_bottom = top[["return_portfolio_ew", "return_portfolio_vw"]].rename(columns={"return_portfolio_ew": "long_ret_ew", "return_portfolio_vw": "long_ret_vw"}).join(
        bot[["return_portfolio_ew", "return_portfolio_vw"]].rename(columns={"return_portfolio_ew": "short_ret_ew", "return_portfolio_vw": "short_ret_vw"}), how="inner")
    return ls.reset_index(), long_only.reset_index(), top_bottom.reset_index()


def summarize_performance(model_name: str, ls: pd.DataFrame, long_only: pd.DataFrame, cost_bps_list: list[int]) -> pd.DataFrame:
    rows = []
    for strategy_name, df_ser in [(f"{model_name}_LS", ls), (f"{model_name}_LONG", long_only)]:
        for w in ["ew", "vw"]:
            gross = f"gross_excess_{w}"
            rows.append({"strategy": f"{strategy_name}_{w.upper()}_gross", "mean_turnover": float(df_ser[f'turnover_{w}'].mean()), "cost_bps": 0, **_perf_stats(df_ser[gross])})
            for bps in cost_bps_list:
                col = f"net_excess_{w}_{bps}bps"
                rows.append({"strategy": f"{strategy_name}_{w.upper()}_net_{bps}bps", "mean_turnover": float(df_ser[f'turnover_{w}'].mean()), "cost_bps": int(bps), **_perf_stats(df_ser[col])})
    return pd.DataFrame(rows)
