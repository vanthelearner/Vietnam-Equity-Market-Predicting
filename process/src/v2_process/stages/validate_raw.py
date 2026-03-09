from __future__ import annotations

import pandas as pd

from ..contracts import PipelineConfig
from ..paths import OutputPaths


def run(config: PipelineConfig, paths: OutputPaths, context: dict) -> dict:
    stock = pd.read_csv(context.get('stock_transformed_csv', config.inputs.stock_raw_csv), parse_dates=['Date'])
    stock = stock.sort_values(['Ticker', 'Date']).reset_index(drop=True)
    ret = stock.groupby('Ticker', sort=False)['Price'].pct_change() if 'Price' in stock.columns else pd.Series(dtype=float)
    pd.DataFrame([
        {'metric': 'n_rows', 'value': float(len(stock))},
        {'metric': 'n_tickers', 'value': float(stock['Ticker'].nunique())},
        {'metric': 'dup_ticker_date_rows', 'value': float(stock.duplicated(['Ticker', 'Date']).sum())},
        {'metric': 'zero_return_share', 'value': float((ret == 0).mean()) if len(ret) else 0.0},
    ]).to_csv(paths.raw_stock_summary, index=False)
    (stock.isna().mean().sort_values(ascending=False).rename('missing_share').reset_index().rename(columns={'index': 'column'})).to_csv(paths.raw_stock_missing_share, index=False)
    macro = pd.read_csv(config.inputs.macro_raw_csv)
    (macro.isna().mean().sort_values(ascending=False).rename('missing_share').reset_index().rename(columns={'index': 'column'})).to_csv(paths.raw_macro_missing_share, index=False)
    return {'outputs': {'raw_stock_summary': str(paths.raw_stock_summary), 'raw_stock_missing_share': str(paths.raw_stock_missing_share), 'raw_macro_missing_share': str(paths.raw_macro_missing_share)}, 'metrics': {'n_rows': int(len(stock)), 'n_tickers': int(stock['Ticker'].nunique())}, 'warnings': []}
