# Feature Dictionary

This document lists every feature that can be used by the `version_2` model pipeline.

## How The Model Uses Features

- `OLS3` always uses only `me`, `be_me`, and `ret_12_1`.
- `OLS`, `ENET`, `PLS`, `PCR`, `GBRT`, `RF`, and `NN` use the feature profile selected in the model config (`careful_v3` or `max_v3`) plus the same three core anchors.
- `careful_v3` contains `55` total model inputs (`52` profile features + `3` core anchors).
- `max_v3` contains `134` total model inputs (`131` profile features + `3` core anchors).
- In preprocessing, numeric features are filled within month using the monthly median, backfilled with the full-sample median if needed, winsorized cross-sectionally by month, and rank-scaled to `[-1, 1]`.

## Source Files

- `model/src/v2_model/feature_profiles.py`: declares profile membership.
- `model/src/v2_model/prepare_inputs.py`: engineers monthly, macro-change, ratio, growth, and interaction features.
- `process/src/v2_process/stages/transform_stock.py`: creates the upstream stock-level factors and ratios.
- `process/src/v2_process/stages/process_stock.py`: computes liquidity proxies such as `dollar_vol` and `adv_med`.

## Core anchors

| Feature | Profiles | Definition |
| --- | --- | --- |
| `me` | `all models` | Month-end market capitalization (`Market_Cap`); always included and one of the fixed `OLS3` features. |
| `be_me` | `all models` | Book-to-market ratio carried through as `bm` in the daily stage and always included in the model set. |
| `ret_12_1` | `all models` | Trailing 12-month price return (`mom12m`) used as the main medium-horizon momentum anchor; always included and part of `OLS3`. |

## Liquidity and tradability

| Feature | Profiles | Definition |
| --- | --- | --- |
| `Bid_Ask` | `careful_v3, max_v3` | Month-end bid-ask spread proxy from the upstream stock file. |
| `Free_Float_Pct` | `careful_v3, max_v3` | Percent of shares that are free-float and therefore more tradable. |
| `Shares_Out` | `careful_v3, max_v3` | Month-end shares outstanding. |
| `age` | `careful_v3, max_v3` | Ticker age in years of observed history in the processed daily panel (`cumcount / 252`). |
| `adv_med` | `careful_v3, max_v3` | Rolling median daily dollar volume used for the final liquidity screen and as a feature. |
| `dollar_vol` | `careful_v3, max_v3` | Daily dollar volume (`Price * Volume`) carried into the month-end panel. |
| `turn` | `careful_v3, max_v3` | Turnover ratio (`Volume / Shares_Out`) at the month-end observation. |
| `std_turn` | `careful_v3, max_v3` | 252-trading-day rolling standard deviation of turnover. |
| `maxret` | `careful_v3, max_v3` | Maximum daily return observed over the trailing 21 trading days. |
| `idiovol` | `careful_v3, max_v3` | 21-trading-day rolling standard deviation of daily returns, used as an idiosyncratic volatility proxy. |
| `Vol_30D` | `careful_v3, max_v3` | Vendor-supplied 30-day volatility measure carried from the stock input. |
| `Vol_90D` | `careful_v3, max_v3` | Vendor-supplied 90-day volatility measure carried from the stock input. |

## Fundamentals and valuation

| Feature | Profiles | Definition |
| --- | --- | --- |
| `FCF` | `careful_v3, max_v3` | Free cash flow level from the upstream stock fundamentals file. |
| `cfp` | `careful_v3, max_v3` | Cash-flow-to-price ratio (`Oper_CF / Market_Cap`). |
| `dy` | `careful_v3, max_v3` | Dividend yield converted to decimal form from `Div_Yield`. |
| `ep` | `careful_v3, max_v3` | Earnings-to-price ratio (`Net_Income / Market_Cap`). |
| `gma` | `careful_v3, max_v3` | Gross-profit-to-assets profitability ratio (`Gross_Profit / Assets`). |
| `lev` | `careful_v3, max_v3` | Leverage ratio (`Debt / Assets`). |
| `cash_ratio` | `careful_v3, max_v3` | Cash-to-assets ratio (`Cash / Assets`). |
| `roeq` | `careful_v3, max_v3` | Return-on-equity proxy (`Net_Income / Equity`). |
| `debt_assets_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Debt / Assets` before winsorization and rank scaling. |
| `cash_assets_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Cash / Assets` before winsorization and rank scaling. |
| `receivables_assets` | `max_v3 only` | Raw ratio built in monthly preparation as `Receivables / Assets` before winsorization and rank scaling. |
| `inventory_assets` | `max_v3 only` | Raw ratio built in monthly preparation as `Inventory_BS / Assets` before winsorization and rank scaling. |
| `ppe_assets` | `max_v3 only` | Raw ratio built in monthly preparation as `PPE / Assets` before winsorization and rank scaling. |
| `cur_assets_assets` | `max_v3 only` | Raw ratio built in monthly preparation as `Cur_Assets / Assets` before winsorization and rank scaling. |
| `cur_liab_assets` | `max_v3 only` | Raw ratio built in monthly preparation as `Cur_Liab / Assets` before winsorization and rank scaling. |
| `sales_assets` | `max_v3 only` | Raw ratio built in monthly preparation as `Sales / Assets` before winsorization and rank scaling. |
| `sales_equity` | `max_v3 only` | Raw ratio built in monthly preparation as `Sales / Equity` before winsorization and rank scaling. |
| `ni_assets_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Net_Income / Assets` before winsorization and rank scaling. |
| `ni_sales_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Net_Income / Sales` before winsorization and rank scaling. |
| `opercf_assets_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Oper_CF / Assets` before winsorization and rank scaling. |
| `opercf_sales_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Oper_CF / Sales` before winsorization and rank scaling. |
| `grossprofit_assets_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Gross_Profit / Assets` before winsorization and rank scaling. |
| `grossprofit_sales_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Gross_Profit / Sales` before winsorization and rank scaling. |
| `capex_assets_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Capex / Assets` before winsorization and rank scaling. |
| `ebitda_assets_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `EBITDA / Assets` before winsorization and rank scaling. |
| `ev_sales_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `EV / Sales` before winsorization and rank scaling. |
| `ev_ebitda_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `EV / EBITDA` before winsorization and rank scaling. |
| `debt_equity_raw` | `max_v3 only` | Raw ratio built in monthly preparation as `Debt / Equity` before winsorization and rank scaling. |

## Growth and balance-sheet change

| Feature | Profiles | Definition |
| --- | --- | --- |
| `agr` | `careful_v3, max_v3` | 12-month asset growth rate from the daily stock panel. |
| `chcsho` | `careful_v3, max_v3` | 12-month change in shares outstanding. |
| `chinv` | `careful_v3, max_v3` | 12-month change in balance-sheet inventory. |
| `pchsale_pchinvt` | `careful_v3, max_v3` | Sales growth minus inventory growth over 12 months. |
| `assets_growth_12m` | `max_v3 only` | 12-month percentage change in `Assets` computed by ticker during monthly preparation. |
| `equity_growth_12m` | `max_v3 only` | 12-month percentage change in `Equity` computed by ticker during monthly preparation. |
| `cash_growth_12m` | `max_v3 only` | 12-month percentage change in `Cash` computed by ticker during monthly preparation. |
| `debt_growth_12m` | `max_v3 only` | 12-month percentage change in `Debt` computed by ticker during monthly preparation. |
| `receivables_growth_12m` | `max_v3 only` | 12-month percentage change in `Receivables` computed by ticker during monthly preparation. |
| `inventory_growth_12m` | `max_v3 only` | 12-month percentage change in `Inventory_BS` computed by ticker during monthly preparation. |
| `cur_assets_growth_12m` | `max_v3 only` | 12-month percentage change in `Cur_Assets` computed by ticker during monthly preparation. |
| `cur_liab_growth_12m` | `max_v3 only` | 12-month percentage change in `Cur_Liab` computed by ticker during monthly preparation. |
| `ppe_growth_12m` | `max_v3 only` | 12-month percentage change in `PPE` computed by ticker during monthly preparation. |
| `sales_growth_12m_raw` | `max_v3 only` | 12-month percentage change in `Sales` computed by ticker during monthly preparation. |
| `net_income_growth_12m_raw` | `max_v3 only` | 12-month percentage change in `Net_Income` computed by ticker during monthly preparation. |
| `oper_cf_growth_12m_raw` | `max_v3 only` | 12-month percentage change in `Oper_CF` computed by ticker during monthly preparation. |
| `gross_profit_growth_12m_raw` | `max_v3 only` | 12-month percentage change in `Gross_Profit` computed by ticker during monthly preparation. |
| `ebitda_growth_12m_raw` | `max_v3 only` | 12-month percentage change in `EBITDA` computed by ticker during monthly preparation. |
| `capex_growth_12m_raw` | `max_v3 only` | 12-month percentage change in `Capex` computed by ticker during monthly preparation. |

## Momentum and return trend

| Feature | Profiles | Definition |
| --- | --- | --- |
| `mom1m` | `careful_v3, max_v3` | Trailing 1-month price momentum using a 21-trading-day percentage change. |
| `mom6m` | `careful_v3, max_v3` | Trailing 6-month price momentum using a 126-trading-day percentage change. |
| `mom36m` | `careful_v3, max_v3` | Trailing 36-month price momentum using a 756-trading-day percentage change. |
| `tri_ret_12_1` | `careful_v3, max_v3` | 12-month total-return momentum built from `TRI_Gross`; added as the total-return analogue of `ret_12_1`. |
| `tri_mom1m` | `max_v3 only` | Trailing 1-month total-return momentum from `TRI_Gross`. |
| `tri_mom6m` | `max_v3 only` | Trailing 6-month total-return momentum from `TRI_Gross`. |
| `tri_mom36m` | `max_v3 only` | Trailing 36-month total-return momentum from `TRI_Gross`. |

## Macro and benchmark state

| Feature | Profiles | Definition |
| --- | --- | --- |
| `Textile_Cotton_Price` | `careful_v3, max_v3` | Month-end macro state for the textile cotton price benchmark, merged to stocks with release-lag handling. |
| `Comm_Brent_Oil` | `careful_v3, max_v3` | Month-end macro state for the Brent crude oil price, merged to stocks with release-lag handling. |
| `Comm_Copper` | `careful_v3, max_v3` | Month-end macro state for the copper price, merged to stocks with release-lag handling. |
| `Comm_Gold_Spot` | `careful_v3, max_v3` | Month-end macro state for the spot gold price, merged to stocks with release-lag handling. |
| `Comm_Natural_Gas` | `careful_v3, max_v3` | Month-end macro state for the natural gas price, merged to stocks with release-lag handling. |
| `Global_Baltic_Dry` | `careful_v3, max_v3` | Month-end macro state for the Baltic Dry shipping index, merged to stocks with release-lag handling. |
| `USD_CNY_FX` | `careful_v3, max_v3` | Month-end macro state for the USD/CNY exchange rate, merged to stocks with release-lag handling. |
| `USD_VND_FX` | `careful_v3, max_v3` | Month-end macro state for the USD/VND exchange rate, merged to stocks with release-lag handling. |
| `US_Bond_10Y` | `careful_v3, max_v3` | Month-end macro state for the US 10-year government bond yield, merged to stocks with release-lag handling. |
| `US_CPI_YoY` | `careful_v3, max_v3` | Month-end macro state for the US CPI year-over-year inflation, merged to stocks with release-lag handling. |
| `US_Dollar_Index` | `careful_v3, max_v3` | Month-end macro state for the US dollar index, merged to stocks with release-lag handling. |
| `US_FedFunds_Rate` | `careful_v3, max_v3` | Month-end macro state for the US Fed funds policy rate, merged to stocks with release-lag handling. |
| `US_GDP_QoQ` | `careful_v3, max_v3` | Month-end macro state for the US GDP quarter-over-quarter growth, merged to stocks with release-lag handling. |
| `US_Market_SP500` | `careful_v3, max_v3` | Month-end macro state for the S&P 500 index level, merged to stocks with release-lag handling. |
| `US_Volatility_VIX` | `careful_v3, max_v3` | Month-end macro state for the VIX equity volatility index, merged to stocks with release-lag handling. |
| `VN_CPI_YoY` | `careful_v3, max_v3` | Month-end macro state for the Vietnam CPI year-over-year inflation, merged to stocks with release-lag handling. |
| `VN_Market_Index` | `careful_v3, max_v3` | Month-end macro state for the Vietnam market index level, merged to stocks with release-lag handling. |
| `VN_MoneySupply_M2` | `careful_v3, max_v3` | Month-end macro state for the Vietnam M2 money supply, merged to stocks with release-lag handling. |
| `Hong_Kong_Index` | `careful_v3, max_v3` | Month-end macro state for the Hong Kong equity index level, merged to stocks with release-lag handling. |
| `Indonesia_Index` | `careful_v3, max_v3` | Month-end macro state for the Indonesia equity index level, merged to stocks with release-lag handling. |
| `Philippines_Index` | `careful_v3, max_v3` | Month-end macro state for the Philippines equity index level, merged to stocks with release-lag handling. |
| `Thailand_Index` | `careful_v3, max_v3` | Month-end macro state for the Thailand equity index level, merged to stocks with release-lag handling. |
| `China_Shanghai_Index` | `careful_v3, max_v3` | Month-end macro state for the Shanghai equity index level, merged to stocks with release-lag handling. |
| `VN_DIAMOND_INDEX` | `careful_v3, max_v3` | Month-end macro state for the VN Diamond index level, merged to stocks with release-lag handling. |

## Macro and benchmark change

| Feature | Profiles | Definition |
| --- | --- | --- |
| `VN_Market_Index_chg1m` | `max_v3 only` | 1-month percentage change in the monthly Vietnam market index level series. |
| `VN_Market_Index_chg3m` | `max_v3 only` | 3-month percentage change in the monthly Vietnam market index level series. |
| `US_Market_SP500_chg1m` | `max_v3 only` | 1-month percentage change in the monthly S&P 500 index level series. |
| `US_Market_SP500_chg3m` | `max_v3 only` | 3-month percentage change in the monthly S&P 500 index level series. |
| `Hong_Kong_Index_chg1m` | `max_v3 only` | 1-month percentage change in the monthly Hong Kong equity index level series. |
| `Hong_Kong_Index_chg3m` | `max_v3 only` | 3-month percentage change in the monthly Hong Kong equity index level series. |
| `Indonesia_Index_chg1m` | `max_v3 only` | 1-month percentage change in the monthly Indonesia equity index level series. |
| `Indonesia_Index_chg3m` | `max_v3 only` | 3-month percentage change in the monthly Indonesia equity index level series. |
| `Philippines_Index_chg1m` | `max_v3 only` | 1-month percentage change in the monthly Philippines equity index level series. |
| `Philippines_Index_chg3m` | `max_v3 only` | 3-month percentage change in the monthly Philippines equity index level series. |
| `Thailand_Index_chg1m` | `max_v3 only` | 1-month percentage change in the monthly Thailand equity index level series. |
| `Thailand_Index_chg3m` | `max_v3 only` | 3-month percentage change in the monthly Thailand equity index level series. |
| `China_Shanghai_Index_chg1m` | `max_v3 only` | 1-month percentage change in the monthly Shanghai equity index level series. |
| `China_Shanghai_Index_chg3m` | `max_v3 only` | 3-month percentage change in the monthly Shanghai equity index level series. |
| `VN_DIAMOND_INDEX_chg1m` | `max_v3 only` | 1-month percentage change in the monthly VN Diamond index level series. |
| `VN_DIAMOND_INDEX_chg3m` | `max_v3 only` | 3-month percentage change in the monthly VN Diamond index level series. |
| `Comm_Brent_Oil_chg1m` | `max_v3 only` | 1-month percentage change in the monthly Brent crude oil price series. |
| `Comm_Brent_Oil_chg3m` | `max_v3 only` | 3-month percentage change in the monthly Brent crude oil price series. |
| `Comm_Copper_chg1m` | `max_v3 only` | 1-month percentage change in the monthly copper price series. |
| `Comm_Copper_chg3m` | `max_v3 only` | 3-month percentage change in the monthly copper price series. |
| `USD_VND_FX_chg1m` | `max_v3 only` | 1-month percentage change in the monthly USD/VND exchange rate series. |
| `USD_VND_FX_chg3m` | `max_v3 only` | 3-month percentage change in the monthly USD/VND exchange rate series. |
| `US_Bond_10Y_chg1m` | `max_v3 only` | 1-month percentage change in the monthly US 10-year government bond yield series. |
| `US_Bond_10Y_chg3m` | `max_v3 only` | 3-month percentage change in the monthly US 10-year government bond yield series. |

## Market microstructure (max_v3 only)

| Feature | Profiles | Definition |
| --- | --- | --- |
| `oc_ret_1m` | `max_v3 only` | One-month open-to-close return using the first open and last close observed within the month. |
| `hl_range_avg_1m` | `max_v3 only` | Average daily intraday range over the month, computed as `(High - Low) / Price`. |
| `close_loc_avg_1m` | `max_v3 only` | Average location of the close within the day range, `(Price - Low) / (High - Low)`. |
| `intraday_range_vol_1m` | `max_v3 only` | Within-month standard deviation of the daily intraday range proxy. |

## Interaction features

| Feature | Profiles | Definition |
| --- | --- | --- |
| `mom1m_x_turn` | `max_v3 only` | Feature interaction defined as `mom1m * turn` in monthly preparation. |
| `mom6m_x_turn` | `max_v3 only` | Feature interaction defined as `mom6m * turn` in monthly preparation. |
| `mom36m_x_turn` | `max_v3 only` | Feature interaction defined as `mom36m * turn` in monthly preparation. |
| `mom1m_x_idiovol` | `max_v3 only` | Feature interaction defined as `mom1m * idiovol` in monthly preparation. |
| `mom6m_x_idiovol` | `max_v3 only` | Feature interaction defined as `mom6m * idiovol` in monthly preparation. |
| `mom36m_x_idiovol` | `max_v3 only` | Feature interaction defined as `mom36m * idiovol` in monthly preparation. |
| `cfp_x_lev` | `max_v3 only` | Feature interaction defined as `cfp * lev` in monthly preparation. |
| `ep_x_roeq` | `max_v3 only` | Feature interaction defined as `ep * roeq` in monthly preparation. |
| `be_me_x_roeq` | `max_v3 only` | Feature interaction defined as `be_me * roeq` in monthly preparation. |
| `dy_x_lev` | `max_v3 only` | Feature interaction defined as `dy * lev` in monthly preparation. |
| `ret_12_1_x_vn_mkt_chg1m` | `max_v3 only` | Feature interaction defined as `ret_12_1 * VN_Market_Index_chg1m` in monthly preparation. |
| `ret_12_1_x_us_mkt_chg1m` | `max_v3 only` | Feature interaction defined as `ret_12_1 * US_Market_SP500_chg1m` in monthly preparation. |
| `turn_x_vix_chg1m` | `max_v3 only` | Feature interaction defined as `turn * US_Volatility_VIX_chg1m` in monthly preparation. |
