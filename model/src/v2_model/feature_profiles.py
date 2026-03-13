from __future__ import annotations

REQUIRED_PANEL_COLS = [
    'id', 'eom', 'prc', 'me', 'ret', 'ret_exc', 'ret_exc_lead1m', 'be_me', 'ret_12_1'
]

BATCH2_BASE_FEATURES = [
    'Bid_Ask', 'Free_Float_Pct', 'Shares_Out', 'age', 'adv_med', 'dollar_vol', 'turn', 'std_turn', 'maxret', 'idiovol',
    'FCF', 'cfp', 'dy', 'ep', 'gma', 'lev', 'cash_ratio', 'roeq', 'agr', 'chcsho', 'chinv', 'pchsale_pchinvt', 'mom1m', 'mom6m', 'mom36m',
    'Textile_Cotton_Price', 'Comm_Brent_Oil', 'Comm_Copper', 'Comm_Gold_Spot', 'Comm_Natural_Gas', 'Global_Baltic_Dry',
    'USD_CNY_FX', 'USD_VND_FX', 'US_Bond_10Y', 'US_CPI_YoY', 'US_Dollar_Index', 'US_FedFunds_Rate', 'US_GDP_QoQ', 'US_Market_SP500', 'US_Volatility_VIX',
    'VN_CPI_YoY', 'VN_Market_Index', 'VN_MoneySupply_M2',
]

CAREFUL_V3_ADDITIONS = [
    'Hong_Kong_Index', 'Indonesia_Index', 'Philippines_Index', 'Thailand_Index', 'China_Shanghai_Index', 'VN_DIAMOND_INDEX',
    'Vol_30D', 'Vol_90D', 'tri_ret_12_1',
]

MAX_V3_ONLY_ADDITIONS = [
    'VN_Market_Index_chg1m', 'VN_Market_Index_chg3m',
    'US_Market_SP500_chg1m', 'US_Market_SP500_chg3m',
    'Hong_Kong_Index_chg1m', 'Hong_Kong_Index_chg3m',
    'Indonesia_Index_chg1m', 'Indonesia_Index_chg3m',
    'Philippines_Index_chg1m', 'Philippines_Index_chg3m',
    'Thailand_Index_chg1m', 'Thailand_Index_chg3m',
    'China_Shanghai_Index_chg1m', 'China_Shanghai_Index_chg3m',
    'VN_DIAMOND_INDEX_chg1m', 'VN_DIAMOND_INDEX_chg3m',
    'Comm_Brent_Oil_chg1m', 'Comm_Brent_Oil_chg3m',
    'Comm_Copper_chg1m', 'Comm_Copper_chg3m',
    'USD_VND_FX_chg1m', 'USD_VND_FX_chg3m',
    'US_Bond_10Y_chg1m', 'US_Bond_10Y_chg3m',
    'oc_ret_1m', 'hl_range_avg_1m', 'close_loc_avg_1m', 'intraday_range_vol_1m', 'tri_mom1m', 'tri_mom6m', 'tri_mom36m',
    'debt_assets_raw', 'cash_assets_raw', 'receivables_assets', 'inventory_assets', 'ppe_assets', 'cur_assets_assets', 'cur_liab_assets',
    'sales_assets', 'sales_equity', 'ni_assets_raw', 'ni_sales_raw', 'opercf_assets_raw', 'opercf_sales_raw', 'grossprofit_assets_raw',
    'grossprofit_sales_raw', 'capex_assets_raw', 'ebitda_assets_raw', 'ev_sales_raw', 'ev_ebitda_raw', 'debt_equity_raw',
    'assets_growth_12m', 'equity_growth_12m', 'cash_growth_12m', 'debt_growth_12m', 'receivables_growth_12m', 'inventory_growth_12m',
    'cur_assets_growth_12m', 'cur_liab_growth_12m', 'ppe_growth_12m', 'sales_growth_12m_raw', 'net_income_growth_12m_raw',
    'oper_cf_growth_12m_raw', 'gross_profit_growth_12m_raw', 'ebitda_growth_12m_raw', 'capex_growth_12m_raw',
    'mom1m_x_turn', 'mom6m_x_turn', 'mom36m_x_turn', 'mom1m_x_idiovol', 'mom6m_x_idiovol', 'mom36m_x_idiovol',
    'cfp_x_lev', 'ep_x_roeq', 'be_me_x_roeq', 'dy_x_lev', 'ret_12_1_x_vn_mkt_chg1m', 'ret_12_1_x_us_mkt_chg1m', 'turn_x_vix_chg1m',
]

FEATURE_PROFILES = {
    'careful_v3': list(BATCH2_BASE_FEATURES) + list(CAREFUL_V3_ADDITIONS),
    'max_v3': list(BATCH2_BASE_FEATURES) + list(CAREFUL_V3_ADDITIONS) + list(MAX_V3_ONLY_ADDITIONS),
}

MAX_PANEL_FEATURES = FEATURE_PROFILES['max_v3']


def feature_profile_columns(profile: str) -> list[str]:
    if profile not in FEATURE_PROFILES:
        raise KeyError(f'Unknown feature profile: {profile}')
    return list(FEATURE_PROFILES[profile])


def validate_feature_profiles() -> None:
    for name, cols in FEATURE_PROFILES.items():
        if len(cols) != len(set(cols)):
            raise ValueError(f'Duplicate columns found in feature profile: {name}')


validate_feature_profiles()
