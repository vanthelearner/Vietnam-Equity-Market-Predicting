# Version 2 Glossary and Notation

## Core Dataset Terms
| Term | Meaning |
| --- | --- |
| `ret_1d` | daily stock return built on the valid market calendar |
| `y_next_1d` | clipped next-day daily target in `/process` |
| `ret` | monthly raw return in `/model` |
| `ret_exc` | monthly excess return over the monthly risk-free rate |
| `ret_exc_lead1m` | next-month excess return target |
| `prc` | month-end price |
| `me` | month-end market equity / market cap |
| `be_me` | book-to-market style signal carried into the monthly panel |
| `ret_12_1` | 12-month momentum-style signal carried into the monthly panel |
| `adv_med` | rolling median dollar volume |
| `me2` | raw `me`, preserved for portfolio weighting |

## Portfolio / Benchmark Terms
| Term | Meaning |
| --- | --- |
| EW | equal weight |
| VW | value weight |
| H-L | top decile minus bottom decile |
| turnover | change in portfolio weights from one month to the next |
| net return | gross return minus turnover cost |
| benchmark excess return | benchmark return minus monthly risk-free |
| IR | information ratio of active returns |

## Model Metrics
$$
R^2_{OOS} = 1 - \frac{\sum_i (y_i - \hat y_i)^2}{\sum_i y_i^2}
$$

$$
RMSE = \sqrt{\frac{1}{n}\sum_i (y_i - \hat y_i)^2}
$$

$$
IC_t = \operatorname{corr}(\hat y_t, y_t)
$$

## Cross-Section and Time Indexing
- $i$ indexes stocks
- $t$ indexes months unless a daily series is stated explicitly
- $d$ indexes trading days within a month

## Linked Notes
- [Worked example](03_version_2_end_to_end_worked_example.md)
- [Process stock stage](version_2_process_docs/13_src_v2_process_stages_process_stock.md)
- [Monthly input preparation](version_2_model_docs/11_src_v2_model_prepare_inputs.md)
- [Monthly preprocessing](version_2_model_docs/12_src_v2_model_preprocess.md)
- [Portfolio construction](version_2_model_docs/14_src_v2_model_portfolio.md)
