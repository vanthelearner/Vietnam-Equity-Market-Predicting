from __future__ import annotations

import pandas as pd

from ..contracts import PipelineConfig
from ..paths import OutputPaths


KEEP_MACRO_COLS = [
    'Date', 'Textile_Cotton_Price', 'Comm_Brent_Oil', 'Comm_Copper', 'Comm_Gold_Spot', 'Comm_Natural_Gas',
    'Global_Baltic_Dry', 'USD_CNY_FX', 'USD_VND_FX', 'US_Bond_10Y', 'US_CPI_YoY', 'US_Dollar_Index',
    'US_FedFunds_Rate', 'US_GDP_QoQ', 'US_Market_SP500', 'US_RiskFree_3M', 'US_Volatility_VIX',
    'VN_CPI_YoY', 'VN_Market_Index', 'VN_MoneySupply_M2',
    'Hong_Kong_Index', 'Indonesia_Index', 'Philippines_Index', 'Thailand_Index', 'China_Shanghai_Index', 'VN_DIAMOND_INDEX',
]
MARKET_LIKE = [
    'Textile_Cotton_Price', 'Comm_Brent_Oil', 'Comm_Copper', 'Comm_Gold_Spot', 'Comm_Natural_Gas', 'Global_Baltic_Dry',
    'USD_CNY_FX', 'USD_VND_FX', 'US_Bond_10Y', 'US_Dollar_Index', 'US_FedFunds_Rate', 'US_Market_SP500', 'US_RiskFree_3M',
    'US_Volatility_VIX', 'VN_Market_Index', 'Hong_Kong_Index', 'Indonesia_Index', 'Philippines_Index',
    'Thailand_Index', 'China_Shanghai_Index', 'VN_DIAMOND_INDEX'
]


def run(config: PipelineConfig, paths: OutputPaths, context: dict) -> dict:
    macro = pd.read_csv(config.inputs.macro_raw_csv, parse_dates=['Date']).sort_values('Date').drop_duplicates('Date', keep='last')
    keep = [c for c in KEEP_MACRO_COLS if c in macro.columns]
    macro = macro[keep].copy()
    missing = macro.isna().mean().sort_values(ascending=False).rename('missing_share').reset_index().rename(columns={'index': 'column'})
    missing.to_csv(paths.macro_missing_share, index=False)
    # Drop only the series that are effectively empty; the remaining daily series
    # form the broad macro panel that will be time-aligned later.
    drop_cols = missing.loc[(missing['missing_share'] > config.macro.max_missing_share) & (missing['column'] != 'Date'), 'column'].tolist()
    macro = macro.drop(columns=drop_cols)
    macro = macro.set_index('Date').sort_index()
    ffill_cols = [c for c in MARKET_LIKE if c in macro.columns]
    # Market-like series can be carried forward on the daily grid before release lags are applied.
    macro[ffill_cols] = macro[ffill_cols].ffill()
    macro.to_csv(paths.macro_base, index_label='Date')
    context['macro_base_csv'] = str(paths.macro_base)
    return {
        'outputs': {'macro_base': str(paths.macro_base), 'macro_missing_share': str(paths.macro_missing_share)},
        'metrics': {'n_columns_kept': int(macro.shape[1])},
        'warnings': [],
    }
