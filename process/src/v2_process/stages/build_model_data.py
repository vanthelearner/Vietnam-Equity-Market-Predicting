from __future__ import annotations

import pandas as pd

from ..contracts import PipelineConfig
from ..paths import OutputPaths


MACRO_KEEP = [
    'Textile_Cotton_Price', 'Comm_Brent_Oil', 'Comm_Copper', 'Comm_Gold_Spot', 'Comm_Natural_Gas',
    'Global_Baltic_Dry', 'USD_CNY_FX', 'USD_VND_FX', 'US_Bond_10Y', 'US_CPI_YoY', 'US_Dollar_Index',
    'US_FedFunds_Rate', 'US_GDP_QoQ', 'US_Market_SP500', 'US_RiskFree_3M', 'US_Volatility_VIX',
    'VN_CPI_YoY', 'VN_Market_Index', 'VN_MoneySupply_M2',
]


def _next_business_day(ts: pd.Timestamp) -> pd.Timestamp:
    while ts.weekday() >= 5:
        ts += pd.Timedelta(days=1)
    return ts


def _shift_events_to_release_dates(series: pd.Series, lag_days: int) -> pd.Series:
    change_mask = series.ne(series.shift()) & series.notna()
    events = series[change_mask]
    release_dates = events.index + pd.to_timedelta(lag_days, unit='D')
    release_dates = pd.DatetimeIndex([_next_business_day(pd.Timestamp(d)) for d in release_dates])
    shifted = pd.Series(events.values, index=release_dates, name=series.name).sort_index()
    return shifted[~shifted.index.duplicated(keep='last')]


def _apply_release_lags_once(macro_df: pd.DataFrame, lag_rules: dict[str, int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    full_index = pd.DatetimeIndex(macro_df.index)
    shifted_events = {}
    diag_rows = []
    for col in macro_df.columns:
        if col in lag_rules:
            ev = _shift_events_to_release_dates(macro_df[col], int(lag_rules[col]))
            shifted_events[col] = ev
            full_index = full_index.union(ev.index)
            diag_rows.append({'column': col, 'lag_days': int(lag_rules[col]), 'changes_after': int(len(ev))})
    full_index = pd.DatetimeIndex(full_index).sort_values().unique()
    out = pd.DataFrame(index=full_index)
    for col in macro_df.columns:
        if col in shifted_events:
            out[col] = shifted_events[col].reindex(full_index).ffill()
        else:
            out[col] = macro_df[col].reindex(full_index).ffill()
    return out, pd.DataFrame(diag_rows)


def run(config: PipelineConfig, paths: OutputPaths, context: dict) -> dict:
    stocks = pd.read_csv(context.get('stock_clean_csv', paths.clean_stock), parse_dates=['Date']).sort_values(['Ticker', 'Date']).reset_index(drop=True)
    macro = pd.read_csv(context.get('macro_base_csv', paths.macro_base), parse_dates=['Date']).set_index('Date').sort_index()
    macro = macro[[c for c in MACRO_KEEP if c in macro.columns]].copy()
    macro_lagged, lag_diag = _apply_release_lags_once(macro, config.macro.release_lags)
    macro_lagged.to_csv(paths.macro_lagged, index_label='Date')
    lag_diag.to_csv(paths.macro_lag_diag, index=False)

    stocks_merge = stocks.sort_values('Date').copy()
    macro_merge = macro_lagged.reset_index().rename(columns={'index': 'Date'}).sort_values('Date')
    model_data = pd.merge_asof(stocks_merge, macro_merge, on='Date', direction='backward')
    model_data = model_data[model_data['Date'] >= macro_lagged.index.min()].copy()
    model_data = model_data.sort_values(['Ticker', 'Date']).reset_index(drop=True)
    model_data.to_csv(paths.model_data, index=False)
    context['model_data_csv'] = str(paths.model_data)
    return {'outputs': {'macro_lagged': str(paths.macro_lagged), 'macro_lag_diag': str(paths.macro_lag_diag), 'model_data': str(paths.model_data)}, 'metrics': {'model_rows': int(len(model_data)), 'model_tickers': int(model_data['Ticker'].nunique())}, 'warnings': []}
