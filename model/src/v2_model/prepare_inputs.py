from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import PipelineConfig
from .cv import build_rolling_windows
from .io import write_df

OPTIONAL_KEEP_COLS = [
    "Bid_Ask", "Free_Float_Pct", "Shares_Out", "age", "adv_med", "dollar_vol", "turn", "std_turn", "maxret", "idiovol",
    "FCF", "cfp", "dy", "ep", "gma", "lev", "cash_ratio", "roeq", "agr", "chcsho", "chinv", "pchsale_pchinvt", "mom1m", "mom6m", "mom36m",
    "Textile_Cotton_Price", "Comm_Brent_Oil", "Comm_Copper", "Comm_Gold_Spot", "Comm_Natural_Gas", "Global_Baltic_Dry",
    "USD_CNY_FX", "USD_VND_FX", "US_Bond_10Y", "US_CPI_YoY", "US_Dollar_Index", "US_FedFunds_Rate", "US_GDP_QoQ", "US_Market_SP500", "US_Volatility_VIX",
    "VN_CPI_YoY", "VN_Market_Index", "VN_MoneySupply_M2",
]


def month_end(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s).dt.to_period("M").dt.to_timestamp("M")


def compound_return(x: pd.Series) -> float:
    x = pd.Series(x).dropna()
    if len(x) == 0:
        return np.nan
    return float(np.prod(1.0 + x.to_numpy(dtype=float)) - 1.0)


def build_monthly_inputs(config: PipelineConfig) -> dict[str, pd.DataFrame]:
    daily = pd.read_csv(config.paths.input_daily_model_csv, parse_dates=["Date"])
    daily = daily.sort_values(["Ticker", "Date"]).reset_index(drop=True).copy()
    daily["eom"] = month_end(daily["Date"])

    ret_1m = (
        daily.groupby(["Ticker", "eom"], as_index=False)
        .agg(ret=("ret_1d", compound_return))
    )

    observed = daily.loc[daily["is_observed_price"] == 1].copy() if "is_observed_price" in daily.columns else daily.copy()
    monthly_last = (
        observed.sort_values(["Ticker", "Date"])
        .groupby(["Ticker", "eom"], as_index=False)
        .last()
        .copy()
    )

    rf_daily = pd.read_csv(config.paths.input_risk_free_csv, parse_dates=[config.prepare.rf_date_col])
    rf_daily = rf_daily.rename(columns={config.prepare.rf_date_col: "Date", config.prepare.rf_value_col: "RF_src"})
    rf_daily["RF_src"] = pd.to_numeric(rf_daily["RF_src"], errors="coerce")
    rf_daily = rf_daily.dropna(subset=["Date", "RF_src"]).sort_values("Date")
    rf_daily["rf_daily"] = rf_daily["RF_src"] / 100.0 / 252.0
    rf_daily["eom"] = month_end(rf_daily["Date"])
    rf_1m = rf_daily.groupby("eom", as_index=False).agg(rf_1m=("rf_daily", compound_return))

    panel = monthly_last.merge(ret_1m, on=["Ticker", "eom"], how="inner")
    panel = panel.merge(rf_1m, on="eom", how="left")
    panel = panel.sort_values(["Ticker", "eom"]).reset_index(drop=True)

    panel["id"] = panel["Ticker"]
    panel["prc"] = panel["Price"]
    panel["me"] = panel["Market_Cap"]
    panel["be_me"] = panel["bm"]
    panel["ret_12_1"] = panel["mom12m"]
    panel["ret_exc"] = panel["ret"] - panel["rf_1m"]
    panel["ret_exc_lead1m"] = panel.groupby("id", sort=False)["ret_exc"].shift(-1)

    required_cols = ["id", "eom", "prc", "me", "ret", "ret_exc", "ret_exc_lead1m", "be_me", "ret_12_1"]
    keep_optional = [c for c in OPTIONAL_KEEP_COLS if c in panel.columns]
    panel_out = panel[required_cols + keep_optional].copy().sort_values(["id", "eom"]).reset_index(drop=True)

    bench_daily = daily[["Date", "VN_Market_Index"]].dropna().drop_duplicates("Date", keep="last").sort_values("Date").copy()
    bench_daily["benchmark_ret_daily"] = bench_daily["VN_Market_Index"].pct_change()
    bench_daily["eom"] = month_end(bench_daily["Date"])
    benchmark_monthly = (
        bench_daily.groupby("eom", as_index=False)
        .agg(benchmark_ret=("benchmark_ret_daily", compound_return))
        .sort_values("eom")
        .reset_index(drop=True)
    )

    panel_summary = pd.DataFrame([
        {"metric": "n_rows", "value": int(len(panel_out))},
        {"metric": "n_assets", "value": int(panel_out['id'].nunique())},
        {"metric": "n_months", "value": int(panel_out['eom'].nunique())},
        {"metric": "n_optional_features", "value": int(len(keep_optional))},
        {"metric": "date_min", "value": str(panel_out['eom'].min())},
        {"metric": "date_max", "value": str(panel_out['eom'].max())},
    ])
    benchmark_summary = pd.DataFrame([
        {"metric": "n_rows", "value": int(len(benchmark_monthly))},
        {"metric": "date_min", "value": str(benchmark_monthly['eom'].min())},
        {"metric": "date_max", "value": str(benchmark_monthly['eom'].max())},
    ])

    months = sorted(pd.to_datetime(panel_out.loc[panel_out['ret_exc_lead1m'].notna(), 'eom']).unique())
    windows = build_rolling_windows(months, config.cv.train_months, config.cv.val_months, config.cv.test_months, config.cv.step_months)
    if windows:
        coverage = pd.DataFrame([
            {"metric": "n_windows", "value": int(len(windows))},
            {"metric": "first_train_range", "value": f"{windows[0].train_months[0]} -> {windows[0].train_months[-1]}"},
            {"metric": "first_val_range", "value": f"{windows[0].val_months[0]} -> {windows[0].val_months[-1]}"},
            {"metric": "first_test_range", "value": f"{windows[0].test_months[0]} -> {windows[0].test_months[-1]}"},
            {"metric": "test_union_range", "value": f"{windows[0].test_months[0]} -> {windows[-1].test_months[-1]}"},
        ])
    else:
        coverage = pd.DataFrame([{"metric": "n_windows", "value": 0}])

    write_df(panel_out, config.paths.prepared_panel_csv)
    write_df(benchmark_monthly, config.paths.prepared_benchmark_csv)
    write_df(panel_summary, config.paths.prepared_panel_summary_csv)
    write_df(benchmark_summary, config.paths.prepared_benchmark_summary_csv)
    write_df(coverage, config.paths.window_coverage_summary_csv)

    return {
        "panel": panel_out,
        "benchmark": benchmark_monthly,
        "panel_summary": panel_summary,
        "benchmark_summary": benchmark_summary,
        "window_coverage": coverage,
    }
