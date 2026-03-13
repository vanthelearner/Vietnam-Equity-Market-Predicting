from __future__ import annotations

import numpy as np
import pandas as pd

from .config import PipelineConfig
from .cv import build_rolling_windows
from .feature_profiles import MAX_PANEL_FEATURES, REQUIRED_PANEL_COLS
from .io import write_df


def month_end(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s).dt.to_period('M').dt.to_timestamp('M')


def compound_return(x: pd.Series) -> float:
    x = pd.Series(x).dropna()
    if len(x) == 0:
        return np.nan
    return float(np.prod(1.0 + x.to_numpy(dtype=float)) - 1.0)


def _safe_div(a, b) -> pd.Series:
    a = pd.to_numeric(a, errors='coerce')
    b = pd.to_numeric(b, errors='coerce')
    out = a / b
    out = out.where(b.notna() & (b != 0))
    return out.replace([np.inf, -np.inf], np.nan)


def _pct_change_by_id(df: pd.DataFrame, col: str, periods: int) -> pd.Series:
    out = df.groupby('id', sort=False)[col].pct_change(periods)
    return out.replace([np.inf, -np.inf], np.nan)


def _build_monthly_market_microstructure(observed: pd.DataFrame) -> pd.DataFrame:
    work = observed.copy()
    if {'High', 'Low', 'Price'}.issubset(work.columns):
        work['intraday_range'] = _safe_div(work['High'] - work['Low'], work['Price'])
        work['close_loc'] = _safe_div(work['Price'] - work['Low'], work['High'] - work['Low'])
    else:
        work['intraday_range'] = np.nan
        work['close_loc'] = np.nan

    def _agg(group: pd.DataFrame) -> pd.Series:
        open_first = group['Open'].dropna().iloc[0] if 'Open' in group.columns and group['Open'].dropna().size else np.nan
        close_last = group['Price'].dropna().iloc[-1] if group['Price'].dropna().size else np.nan
        return pd.Series({
            'oc_ret_1m': float(close_last / open_first - 1.0) if pd.notna(open_first) and open_first != 0 and pd.notna(close_last) else np.nan,
            'hl_range_avg_1m': float(group['intraday_range'].mean()) if 'intraday_range' in group.columns else np.nan,
            'close_loc_avg_1m': float(group['close_loc'].mean()) if 'close_loc' in group.columns else np.nan,
            'intraday_range_vol_1m': float(group['intraday_range'].std()) if 'intraday_range' in group.columns else np.nan,
        })

    out = work.groupby(['Ticker', 'eom'], as_index=False).apply(_agg)
    out = out.reset_index(drop=True)
    return out


def _build_macro_changes(panel: pd.DataFrame) -> pd.DataFrame:
    # Collapse the shared macro panel to one row per month and add simple recent-change features.
    series_cols = [
        'VN_Market_Index', 'US_Market_SP500', 'Hong_Kong_Index', 'Indonesia_Index', 'Philippines_Index', 'Thailand_Index',
        'China_Shanghai_Index', 'VN_DIAMOND_INDEX', 'Comm_Brent_Oil', 'Comm_Copper', 'USD_VND_FX', 'US_Bond_10Y',
        'US_Volatility_VIX',
    ]
    macro = panel[['eom'] + [c for c in series_cols if c in panel.columns]].drop_duplicates('eom').sort_values('eom').copy()
    for col in [c for c in series_cols if c in macro.columns]:
        macro[f'{col}_chg1m'] = macro[col].pct_change(1).replace([np.inf, -np.inf], np.nan)
        macro[f'{col}_chg3m'] = macro[col].pct_change(3).replace([np.inf, -np.inf], np.nan)
    return macro


def build_monthly_inputs(config: PipelineConfig) -> dict[str, pd.DataFrame]:
    daily = pd.read_csv(config.paths.input_daily_model_csv, parse_dates=['Date'])
    daily = daily.sort_values(['Ticker', 'Date']).reset_index(drop=True).copy()
    daily['eom'] = month_end(daily['Date'])

    # The model consumes month-level returns even though the upstream handoff is daily.
    ret_1m = daily.groupby(['Ticker', 'eom'], as_index=False).agg(ret=('ret_1d', compound_return))
    observed = daily.loc[daily['is_observed_price'] == 1].copy() if 'is_observed_price' in daily.columns else daily.copy()
    observed = observed.sort_values(['Ticker', 'Date']).reset_index(drop=True)
    monthly_last = observed.groupby(['Ticker', 'eom'], as_index=False).last().copy()

    micro = _build_monthly_market_microstructure(observed)
    monthly_last = monthly_last.merge(micro, on=['Ticker', 'eom'], how='left')

    rf_daily = pd.read_csv(config.paths.input_risk_free_csv, parse_dates=[config.prepare.rf_date_col])
    rf_daily = rf_daily.rename(columns={config.prepare.rf_date_col: 'Date', config.prepare.rf_value_col: 'RF_src'})
    rf_daily['RF_src'] = pd.to_numeric(rf_daily['RF_src'], errors='coerce')
    rf_daily = rf_daily.dropna(subset=['Date', 'RF_src']).sort_values('Date')
    rf_daily['rf_daily'] = rf_daily['RF_src'] / 100.0 / 252.0
    rf_daily['eom'] = month_end(rf_daily['Date'])
    rf_1m = rf_daily.groupby('eom', as_index=False).agg(rf_1m=('rf_daily', compound_return))

    # Build the core monthly schema first; the wider feature set is added on top of it.
    panel = monthly_last.merge(ret_1m, on=['Ticker', 'eom'], how='inner')
    panel = panel.merge(rf_1m, on='eom', how='left')
    panel = panel.sort_values(['Ticker', 'eom']).reset_index(drop=True)

    panel['id'] = panel['Ticker']
    panel['prc'] = panel['Price']
    panel['me'] = panel['Market_Cap']
    panel['be_me'] = panel['bm']
    panel['ret_12_1'] = panel['mom12m']
    panel['ret_exc'] = panel['ret'] - panel['rf_1m']
    panel['ret_exc_lead1m'] = panel.groupby('id', sort=False)['ret_exc'].shift(-1)

    if 'TRI_Gross' in panel.columns:
        panel['tri_mom1m'] = _pct_change_by_id(panel, 'TRI_Gross', 1)
        panel['tri_mom6m'] = _pct_change_by_id(panel, 'TRI_Gross', 6)
        panel['tri_mom36m'] = _pct_change_by_id(panel, 'TRI_Gross', 36)
        panel['tri_ret_12_1'] = _pct_change_by_id(panel, 'TRI_Gross', 12)
    else:
        for col in ['tri_mom1m', 'tri_mom6m', 'tri_mom36m', 'tri_ret_12_1']:
            panel[col] = np.nan

    macro_changes = _build_macro_changes(panel)
    panel = panel.merge(macro_changes, on='eom', how='left', suffixes=('', '_macrochg'))

    # Add the superset of optional features once so the narrower profiles can be
    # selected later without rebuilding the monthly panel.
    ratio_specs = {
        'debt_assets_raw': ('Debt', 'Assets'),
        'cash_assets_raw': ('Cash', 'Assets'),
        'receivables_assets': ('Receivables', 'Assets'),
        'inventory_assets': ('Inventory_BS', 'Assets'),
        'ppe_assets': ('PPE', 'Assets'),
        'cur_assets_assets': ('Cur_Assets', 'Assets'),
        'cur_liab_assets': ('Cur_Liab', 'Assets'),
        'sales_assets': ('Sales', 'Assets'),
        'sales_equity': ('Sales', 'Equity'),
        'ni_assets_raw': ('Net_Income', 'Assets'),
        'ni_sales_raw': ('Net_Income', 'Sales'),
        'opercf_assets_raw': ('Oper_CF', 'Assets'),
        'opercf_sales_raw': ('Oper_CF', 'Sales'),
        'grossprofit_assets_raw': ('Gross_Profit', 'Assets'),
        'grossprofit_sales_raw': ('Gross_Profit', 'Sales'),
        'capex_assets_raw': ('Capex', 'Assets'),
        'ebitda_assets_raw': ('EBITDA', 'Assets'),
        'ev_sales_raw': ('EV', 'Sales'),
        'ev_ebitda_raw': ('EV', 'EBITDA'),
        'debt_equity_raw': ('Debt', 'Equity'),
    }
    for out_col, (num_col, den_col) in ratio_specs.items():
        if num_col in panel.columns and den_col in panel.columns:
            panel[out_col] = _safe_div(panel[num_col], panel[den_col])
        else:
            panel[out_col] = np.nan

    growth_cols = {
        'assets_growth_12m': 'Assets',
        'equity_growth_12m': 'Equity',
        'cash_growth_12m': 'Cash',
        'debt_growth_12m': 'Debt',
        'receivables_growth_12m': 'Receivables',
        'inventory_growth_12m': 'Inventory_BS',
        'cur_assets_growth_12m': 'Cur_Assets',
        'cur_liab_growth_12m': 'Cur_Liab',
        'ppe_growth_12m': 'PPE',
        'sales_growth_12m_raw': 'Sales',
        'net_income_growth_12m_raw': 'Net_Income',
        'oper_cf_growth_12m_raw': 'Oper_CF',
        'gross_profit_growth_12m_raw': 'Gross_Profit',
        'ebitda_growth_12m_raw': 'EBITDA',
        'capex_growth_12m_raw': 'Capex',
    }
    for out_col, src_col in growth_cols.items():
        if src_col in panel.columns:
            panel[out_col] = _pct_change_by_id(panel, src_col, 12)
        else:
            panel[out_col] = np.nan

    interaction_specs = {
        'mom1m_x_turn': ('mom1m', 'turn'),
        'mom6m_x_turn': ('mom6m', 'turn'),
        'mom36m_x_turn': ('mom36m', 'turn'),
        'mom1m_x_idiovol': ('mom1m', 'idiovol'),
        'mom6m_x_idiovol': ('mom6m', 'idiovol'),
        'mom36m_x_idiovol': ('mom36m', 'idiovol'),
        'cfp_x_lev': ('cfp', 'lev'),
        'ep_x_roeq': ('ep', 'roeq'),
        'be_me_x_roeq': ('be_me', 'roeq'),
        'dy_x_lev': ('dy', 'lev'),
        'ret_12_1_x_vn_mkt_chg1m': ('ret_12_1', 'VN_Market_Index_chg1m'),
        'ret_12_1_x_us_mkt_chg1m': ('ret_12_1', 'US_Market_SP500_chg1m'),
        'turn_x_vix_chg1m': ('turn', 'US_Volatility_VIX_chg1m'),
    }
    for out_col, (a, b) in interaction_specs.items():
        if a in panel.columns and b in panel.columns:
            panel[out_col] = panel[a] * panel[b]
        else:
            panel[out_col] = np.nan

    keep_optional = [c for c in MAX_PANEL_FEATURES if c in panel.columns]
    panel_out = panel[REQUIRED_PANEL_COLS + keep_optional].copy().sort_values(['id', 'eom']).reset_index(drop=True)

    # Benchmark returns are built on the same month-end grid as the stock panel.
    bench_daily = daily[['Date', 'VN_Market_Index']].dropna().drop_duplicates('Date', keep='last').sort_values('Date').copy()
    bench_daily['benchmark_ret_daily'] = bench_daily['VN_Market_Index'].pct_change()
    bench_daily['eom'] = month_end(bench_daily['Date'])
    benchmark_monthly = bench_daily.groupby('eom', as_index=False).agg(benchmark_ret=('benchmark_ret_daily', compound_return)).sort_values('eom').reset_index(drop=True)

    panel_summary = pd.DataFrame([
        {'metric': 'n_rows', 'value': int(len(panel_out))},
        {'metric': 'n_assets', 'value': int(panel_out['id'].nunique())},
        {'metric': 'n_months', 'value': int(panel_out['eom'].nunique())},
        {'metric': 'n_optional_features', 'value': int(len(keep_optional))},
        {'metric': 'date_min', 'value': str(panel_out['eom'].min())},
        {'metric': 'date_max', 'value': str(panel_out['eom'].max())},
    ])
    benchmark_summary = pd.DataFrame([
        {'metric': 'n_rows', 'value': int(len(benchmark_monthly))},
        {'metric': 'date_min', 'value': str(benchmark_monthly['eom'].min())},
        {'metric': 'date_max', 'value': str(benchmark_monthly['eom'].max())},
    ])

    # Window coverage is written alongside the prepared panel so model runs can
    # confirm the rolling design before training starts.
    months = sorted(pd.to_datetime(panel_out.loc[panel_out['ret_exc_lead1m'].notna(), 'eom']).unique())
    windows = build_rolling_windows(months, config.cv.train_months, config.cv.val_months, config.cv.test_months, config.cv.step_months)
    if windows:
        coverage = pd.DataFrame([
            {'metric': 'n_windows', 'value': int(len(windows))},
            {'metric': 'first_train_range', 'value': f"{windows[0].train_months[0]} -> {windows[0].train_months[-1]}"},
            {'metric': 'first_val_range', 'value': f"{windows[0].val_months[0]} -> {windows[0].val_months[-1]}"},
            {'metric': 'first_test_range', 'value': f"{windows[0].test_months[0]} -> {windows[0].test_months[-1]}"},
            {'metric': 'test_union_range', 'value': f"{windows[0].test_months[0]} -> {windows[-1].test_months[-1]}"},
        ])
    else:
        coverage = pd.DataFrame([{'metric': 'n_windows', 'value': 0}])

    write_df(panel_out, config.paths.prepared_panel_csv)
    write_df(benchmark_monthly, config.paths.prepared_benchmark_csv)
    write_df(panel_summary, config.paths.prepared_panel_summary_csv)
    write_df(benchmark_summary, config.paths.prepared_benchmark_summary_csv)
    write_df(coverage, config.paths.window_coverage_summary_csv)

    return {
        'panel': panel_out,
        'benchmark': benchmark_monthly,
        'panel_summary': panel_summary,
        'benchmark_summary': benchmark_summary,
        'window_coverage': coverage,
    }
