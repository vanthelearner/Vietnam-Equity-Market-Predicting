from __future__ import annotations

import numpy as np
import pandas as pd

from ..contracts import PipelineConfig
from ..paths import OutputPaths


SLOW_FEATURES = [
    'FCF', 'bm', 'cfp', 'dy', 'ep', 'gma', 'lev', 'cash_ratio', 'roeq', 'agr', 'chcsho', 'chinv', 'pchsale_pchinvt'
]
PROTECTED_COLS = {'Ticker', 'Date', 'Price', 'Volume', 'Market_Cap', 'Shares_Out', 'Bid_Ask', 'Free_Float_Pct', 'mom1m', 'mom6m', 'mom12m', 'mom36m', 'turn', 'std_turn', 'maxret', 'idiovol', 'age'}


def _build_ticker_calendar(g: pd.DataFrame, valid_dates: pd.DatetimeIndex, stale_limit: int) -> pd.DataFrame:
    cal = valid_dates[(valid_dates >= g['Date'].min()) & (valid_dates <= g['Date'].max())]
    full = pd.DataFrame({'Date': cal})
    full = full.merge(g, on='Date', how='left')
    full['Ticker'] = g['Ticker'].iloc[0]
    full['is_observed_price'] = full['Price'].notna().astype(int)
    full['price_ffill'] = full['Price'].ffill()
    full['ret_1d'] = full['price_ffill'].pct_change()
    full['y_next_1d_raw'] = full['ret_1d'].shift(-1)
    full['calendar_gap_flag'] = ((full['is_observed_price'] == 1) & (full['is_observed_price'].shift(1).fillna(1) == 0)).astype(int)

    for col in [c for c in SLOW_FEATURES if c in full.columns]:
        full[f'{col}_missing_flag'] = full[col].isna().astype(int)
        full[col] = full[col].ffill(limit=stale_limit)

    observed = full.loc[full['is_observed_price'] == 1].copy()
    observed['ret_outlier_flag'] = observed['ret_1d'].abs() > 1.0
    observed['y_clip_flag'] = observed['y_next_1d_raw'].abs() > 0.50
    observed['y_next_1d'] = observed['y_next_1d_raw'].clip(-0.50, 0.50)
    return observed


def run(config: PipelineConfig, paths: OutputPaths, context: dict) -> dict:
    df = pd.read_csv(context.get('stock_transformed_csv', paths.transformed_stock), parse_dates=['Date'])
    df = df.dropna(subset=['Ticker', 'Date']).copy()
    df = df[df['Date'] >= pd.Timestamp(config.cleaning.start_date)].copy()
    df = df.sort_values(['Ticker', 'Date']).drop_duplicates(['Ticker', 'Date'], keep='last').reset_index(drop=True)

    count_t = df.dropna(subset=['Price']).groupby('Date')['Ticker'].nunique().sort_index()
    baseline = count_t.rolling(config.cleaning.roll_days, min_periods=config.cleaning.min_base_days).median()
    valid_mask = (baseline.isna() & (count_t >= config.cleaning.min_stocks_early)) | (count_t >= config.cleaning.min_rel * baseline)
    valid_dates = pd.DatetimeIndex(count_t.index[valid_mask])
    df = df[df['Date'].isin(valid_dates)].copy()

    daily = df.groupby(['Ticker', 'Date'], as_index=False).last().sort_values(['Ticker', 'Date']).reset_index(drop=True)
    daily['dollar_vol'] = daily['Price'] * daily['Volume']
    daily['adv_med'] = daily.groupby('Ticker', sort=False)['dollar_vol'].transform(lambda s: s.rolling(config.cleaning.liq_win, min_periods=config.cleaning.liq_minp).median())

    parts = []
    for _, g in daily.groupby('Ticker', sort=False):
        parts.append(_build_ticker_calendar(g.reset_index(drop=True), valid_dates, config.cleaning.stale_limit_days))
    clean = pd.concat(parts, ignore_index=True).sort_values(['Ticker', 'Date']).reset_index(drop=True)

    clean.to_csv(paths.clean_stock, index=False)
    pd.DataFrame([
        {'metric': 'n_rows', 'value': int(len(clean))},
        {'metric': 'n_tickers', 'value': int(clean['Ticker'].nunique())},
        {'metric': 'start_date', 'value': str(clean['Date'].min())},
        {'metric': 'end_date', 'value': str(clean['Date'].max())},
        {'metric': 'target_clip', 'value': float(config.cleaning.target_clip)},
        {'metric': 'clip_share', 'value': float(clean['y_clip_flag'].mean())},
        {'metric': 'zero_ret_share', 'value': float((clean['ret_1d'] == 0).mean())},
        {'metric': 'calendar_gap_flag_share', 'value': float(clean['calendar_gap_flag'].mean())},
        {'metric': 'ret_outlier_share', 'value': float(clean['ret_outlier_flag'].mean())},
        {'metric': 'dropped_hole_dates', 'value': int((~valid_mask).sum())},
    ]).to_csv(paths.clean_summary, index=False)
    context['stock_clean_csv'] = str(paths.clean_stock)
    return {'outputs': {'clean_stock': str(paths.clean_stock), 'clean_summary': str(paths.clean_summary)}, 'metrics': {'n_rows': int(len(clean)), 'n_tickers': int(clean['Ticker'].nunique())}, 'warnings': []}
