from __future__ import annotations

import numpy as np
import pandas as pd

from ..contracts import PipelineConfig
from ..paths import OutputPaths

KEEP_COLS = [
    'Date', 'Ticker', 'Price', 'Market_Cap', 'Volume', 'Shares_Out', 'Bid_Ask', 'Free_Float_Pct', 'FCF',
    'bm', 'ep', 'cfp', 'dy', 'lev', 'cash_ratio', 'roeq', 'gma', 'agr', 'chcsho', 'chinv', 'pchsale_pchinvt',
    'age', 'turn', 'std_turn', 'maxret', 'idiovol', 'mom1m', 'mom6m', 'mom12m', 'mom36m'
]


def _safe_div(a, b) -> np.ndarray:
    a_arr = np.asarray(a)
    b_arr = np.asarray(b)
    out = np.full(a_arr.shape, np.nan, dtype=float)
    np.divide(a_arr, b_arr, out=out, where=(b_arr != 0) & np.isfinite(b_arr))
    return out


def _to_numeric_if_possible(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if col in {'Ticker', 'Date'}:
            continue
        if df[col].dtype == object:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def _g_rolling(series: pd.Series, ticker: pd.Series, window: int, min_periods: int, op: str) -> pd.Series:
    g = series.groupby(ticker, sort=False)
    if op == 'max':
        return g.transform(lambda s: s.rolling(window=window, min_periods=min_periods).max())
    if op == 'std':
        return g.transform(lambda s: s.rolling(window=window, min_periods=min_periods).std())
    raise ValueError(op)


def run(config: PipelineConfig, paths: OutputPaths, context: dict) -> dict:
    df = pd.read_csv(config.inputs.stock_raw_csv)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Ticker', 'Date']).copy()
    df = df.sort_values(['Ticker', 'Date']).reset_index(drop=True)
    df = _to_numeric_if_possible(df)

    assets = df.get('Assets', np.nan)
    equity = df.get('Equity', np.nan)
    cash = df.get('Cash', np.nan)
    debt = df.get('Debt', np.nan)
    sales = df.get('Sales', np.nan)
    ni = df.get('Net_Income', np.nan)
    cfo = df.get('Oper_CF', np.nan)
    gp = df.get('Gross_Profit', np.nan)
    mcap = df.get('Market_Cap', np.nan)
    shares_out = df.get('Shares_Out', np.nan)
    volume = df.get('Volume', np.nan)
    price = df.get('Price', np.nan)
    inv_bs = df.get('Inventory_BS', np.nan)

    df['bm'] = _safe_div(equity, mcap)
    df['ep'] = _safe_div(ni, mcap)
    df['cfp'] = _safe_div(cfo, mcap)
    df['dy'] = pd.to_numeric(df['Div_Yield'], errors='coerce') / 100.0 if 'Div_Yield' in df.columns else np.nan
    df['lev'] = _safe_div(debt, assets)
    df['cash_ratio'] = _safe_div(cash, assets)
    df['roeq'] = _safe_div(ni, equity)
    df['gma'] = _safe_div(gp, assets)

    g = df.groupby('Ticker', sort=False)
    ret_1d = g['Price'].pct_change()
    df['mom1m'] = g['Price'].pct_change(21)
    df['mom6m'] = g['Price'].pct_change(126)
    df['mom12m'] = g['Price'].pct_change(252)
    df['mom36m'] = g['Price'].pct_change(756)
    df['agr'] = g['Assets'].pct_change(252) if 'Assets' in df.columns else np.nan
    df['chcsho'] = g['Shares_Out'].pct_change(252) if 'Shares_Out' in df.columns else np.nan
    df['chinv'] = g['Inventory_BS'].pct_change(252) if 'Inventory_BS' in df.columns else np.nan
    sales_growth = g['Sales'].pct_change(252) if 'Sales' in df.columns else np.nan
    df['pchsale_pchinvt'] = sales_growth - df['chinv']
    df['age'] = g.cumcount() / 252.0
    df['turn'] = _safe_div(volume, shares_out)
    df['std_turn'] = _g_rolling(df['turn'], df['Ticker'], window=252, min_periods=252, op='std')
    df['maxret'] = _g_rolling(ret_1d, df['Ticker'], window=21, min_periods=21, op='max')
    df['idiovol'] = _g_rolling(ret_1d, df['Ticker'], window=21, min_periods=21, op='std')

    out = df[[c for c in KEEP_COLS if c in df.columns]].copy()
    out = out.replace([np.inf, -np.inf], np.nan)
    out.to_csv(paths.transformed_stock, index=False)
    return {'outputs': {'stock_transformed_csv': str(paths.transformed_stock)}, 'metrics': {'n_rows': int(len(out)), 'n_tickers': int(out['Ticker'].nunique()), 'n_columns': int(out.shape[1])}, 'warnings': []}
