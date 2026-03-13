from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import LIQUIDITY_KEEP_SHARE, PipelineConfig
from .feature_profiles import REQUIRED_PANEL_COLS, feature_profile_columns
from .schema import validate_benchmark_schema, validate_panel_schema


@dataclass
class PreparedData:
    full: pd.DataFrame
    large: pd.DataFrame
    small: pd.DataFrame
    feature_cols: list[str]
    rf_monthly: pd.DataFrame
    benchmark_monthly: pd.DataFrame
    preprocess_report: pd.DataFrame


@dataclass
class PreparedScoringData:
    transformed_all: pd.DataFrame
    training_sample: pd.DataFrame
    latest_sample: pd.DataFrame
    latest_raw: pd.DataFrame
    feature_cols: list[str]
    preprocess_report: pd.DataFrame


RESERVED_EXCLUDE_FEATURES = {'id', 'eom', 'prc', 'ret', 'ret_exc', 'ret_exc_lead1m', 'ret_lead1m', 'me2', 'liq_rank_pct', 'is_liquid'}


def _compound_return(x: pd.Series) -> float:
    x = x.dropna()
    if len(x) == 0:
        return np.nan
    return float(np.prod(1.0 + x.to_numpy(dtype=float)) - 1.0)


def _winsorize_by_month(df: pd.DataFrame, cols: list[str], date_col: str, lower: float, upper: float) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c not in out.columns or pd.api.types.is_bool_dtype(out[c]):
            continue
        s = pd.to_numeric(out[c], errors='coerce').replace([np.inf, -np.inf], np.nan)
        if s.notna().sum() == 0 or s.nunique(dropna=True) <= 2:
            out[c] = s
            continue
        ql = s.groupby(out[date_col], sort=False).transform(lambda x: x.quantile(lower))
        qh = s.groupby(out[date_col], sort=False).transform(lambda x: x.quantile(upper))
        out[c] = s.clip(lower=ql, upper=qh)
    return out


def _rank_scale_minus1_to_1(df: pd.DataFrame, cols: list[str], date_col: str) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        out[c] = out.groupby(date_col, sort=False)[c].rank(pct=True)
        out[c] = 2.0 * out[c] - 1.0
    return out


def _build_size_subsamples(df: pd.DataFrame, pct: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    tops, bottoms = [], []
    for _, g in df.groupby('eom', sort=True):
        n = len(g)
        k = max(1, int(np.floor(n * pct)))
        gs = g.sort_values('me')
        bottoms.append(gs.head(k))
        tops.append(gs.tail(k))
    return pd.concat(tops, ignore_index=True), pd.concat(bottoms, ignore_index=True)


def _load_inputs(config: PipelineConfig) -> tuple[pd.DataFrame, pd.DataFrame, object, object]:
    panel = pd.read_csv(config.paths.prepared_panel_csv)
    benchmark = pd.read_csv(config.paths.prepared_benchmark_csv)
    panel_report = validate_panel_schema(panel)
    benchmark_report = validate_benchmark_schema(benchmark)
    panel['eom'] = pd.to_datetime(panel['eom']).dt.to_period('M').dt.to_timestamp('M')
    panel = panel.sort_values(['eom', 'id']).reset_index(drop=True)
    benchmark['eom'] = pd.to_datetime(benchmark['eom']).dt.to_period('M').dt.to_timestamp('M')
    benchmark = benchmark.sort_values('eom').reset_index(drop=True)
    return panel, benchmark, panel_report, benchmark_report


def _prepare_transformed_panel(config: PipelineConfig) -> tuple[pd.DataFrame, list[str], pd.DataFrame, object, object]:
    panel, benchmark, panel_report, benchmark_report = _load_inputs(config)
    report_rows: list[dict] = [{'step': 'initial_rows', 'value': int(len(panel))}]

    # Apply broad investability filters before any feature engineering or scaling.
    panel = panel.loc[(panel['prc'] >= config.preprocess.min_price) & (panel['me'] >= config.preprocess.min_me)].copy()
    report_rows.append({'step': 'after_price_size_filter', 'value': int(len(panel))})

    # Liquidity is enforced cross-sectionally within each month, not upstream in the daily pipeline.
    keep_share = LIQUIDITY_KEEP_SHARE[config.preprocess.liquidity_category]
    panel['liq_rank_pct'] = panel.groupby('eom', sort=False)['adv_med'].rank(pct=True)
    panel['is_liquid'] = panel['liq_rank_pct'] >= (1.0 - keep_share)
    panel = panel.loc[panel['is_liquid']].copy()
    report_rows.append({'step': 'after_liquidity_filter', 'value': int(len(panel))})

    labeled = panel.loc[panel['ret_exc_lead1m'].notna()].copy()
    report_rows.append({'step': 'rows_with_known_target', 'value': int(len(labeled))})

    if config.preprocess.date_start:
        dt0 = pd.to_datetime(config.preprocess.date_start)
        panel = panel.loc[panel['eom'] >= dt0].copy()
        labeled = labeled.loc[labeled['eom'] >= dt0].copy()
        report_rows.append({'step': 'after_date_start', 'value': int(len(panel))})

    requested_optional = feature_profile_columns(config.preprocess.feature_profile)
    requested_model_features = requested_optional + ['me', 'be_me', 'ret_12_1']
    keep_cols = [c for c in panel.columns if c in REQUIRED_PANEL_COLS or c in requested_model_features]
    panel = panel[keep_cols].copy()
    report_rows.append({'step': 'columns_kept_for_profile', 'value': int(len(panel.columns))})

    # Coverage is measured on rows with a known future label because those rows
    # define the actual training surface.
    coverage = labeled[keep_cols].notna().mean().rename('coverage').reset_index().rename(columns={'index': 'column'})
    low_cov = coverage.loc[(coverage['coverage'] < config.preprocess.min_col_coverage) & (coverage['column'].isin(requested_optional))]
    report_rows.append({'step': 'requested_optional_low_coverage', 'value': int(len(low_cov))})

    # Fill within each month first so cross-sectional scaling later is not dominated by NaNs.
    num_cols = [c for c in panel.columns if pd.api.types.is_numeric_dtype(panel[c])]
    panel[num_cols] = panel[num_cols].replace([np.inf, -np.inf], np.nan)
    panel[num_cols] = panel.groupby('eom', sort=False)[num_cols].transform(lambda g: g.fillna(g.median()))

    # Some newly added wide-profile features only start later in the sample.
    # After the monthly cross-sectional fill, backstop remaining gaps with the
    # feature's full-panel median so early windows are still runnable.
    for c in requested_model_features:
        if c not in panel.columns or not pd.api.types.is_numeric_dtype(panel[c]):
            continue
        med = pd.to_numeric(panel[c], errors='coerce').median()
        if pd.notna(med):
            panel[c] = pd.to_numeric(panel[c], errors='coerce').fillna(med)

    panel = panel.dropna(subset=[c for c in REQUIRED_PANEL_COLS if c in panel.columns]).copy()
    report_rows.append({'step': 'after_monthly_median_fill_dropna', 'value': int(len(panel))})

    panel = panel.sort_values(['id', 'eom']).reset_index(drop=True)
    panel['ret_lead1m'] = panel.groupby('id', sort=False)['ret'].shift(-1)
    panel['me2'] = panel['me']

    training_sample = panel.dropna(subset=['ret_lead1m', 'ret_exc_lead1m', 'me', 'be_me', 'ret_12_1']).copy()
    report_rows.append({'step': 'training_rows', 'value': int(len(training_sample))})

    missing_profile = [c for c in requested_optional if c not in training_sample.columns]
    if missing_profile:
        raise ValueError(f'Missing requested profile columns: {missing_profile}')

    feature_cols = [c for c in requested_optional if c in training_sample.columns]
    for must in ['me', 'be_me', 'ret_12_1']:
        if must in training_sample.columns and must not in feature_cols:
            feature_cols.append(must)
    report_rows.append({'step': 'n_features', 'value': int(len(feature_cols))})
    report_rows.append({'step': 'feature_profile', 'value': config.preprocess.feature_profile})

    # Winsorize first, then rank-scale, so each month lands on a comparable feature range.
    transformed_all = _winsorize_by_month(panel, feature_cols, 'eom', config.preprocess.winsor_lower, config.preprocess.winsor_upper)
    transformed_all = _rank_scale_minus1_to_1(transformed_all, feature_cols, 'eom')

    # Keep a separate latest-month slice for the recommendation workflow.
    latest_eom = transformed_all['eom'].max()
    latest_sample = transformed_all.loc[transformed_all['eom'] == latest_eom].copy()

    report_rows.extend([
        {'step': 'latest_month', 'value': str(latest_eom.date())},
        {'step': 'latest_rows', 'value': int(len(latest_sample))},
        {'step': 'panel_input_rows', 'value': panel_report.n_rows},
        {'step': 'panel_input_assets', 'value': panel_report.n_assets},
        {'step': 'benchmark_input_rows', 'value': benchmark_report.n_rows},
    ])

    return transformed_all, sorted(set(feature_cols)), pd.DataFrame(report_rows), panel_report, benchmark_report


def prepare_data(config: PipelineConfig) -> PreparedData:
    transformed_all, feature_cols, preprocess_report, panel_report, benchmark_report = _prepare_transformed_panel(config)
    # The training/evaluation sample requires both the current row and the one-month lead return.
    full = transformed_all.dropna(subset=['ret_lead1m', 'ret_exc_lead1m', 'me', 'be_me', 'ret_12_1']).copy()
    full['rf_1m'] = full['ret'] - full['ret_exc']
    rf_monthly = full.groupby('eom', as_index=False).agg(rf_1m=('rf_1m', 'mean'))
    large, small = _build_size_subsamples(full, config.sampling.large_small_pct)

    benchmark = pd.read_csv(config.paths.prepared_benchmark_csv)
    benchmark['eom'] = pd.to_datetime(benchmark['eom']).dt.to_period('M').dt.to_timestamp('M')
    benchmark_monthly = benchmark.sort_values('eom').reset_index(drop=True)

    extra_rows = pd.DataFrame([
        {'step': 'full_rows', 'value': int(len(full))},
        {'step': 'large_rows', 'value': int(len(large))},
        {'step': 'small_rows', 'value': int(len(small))},
        {'step': 'full_assets', 'value': int(full['id'].nunique())},
        {'step': 'benchmark_months', 'value': int(benchmark_monthly['eom'].nunique())},
        {'step': 'panel_input_rows', 'value': panel_report.n_rows},
        {'step': 'panel_input_assets', 'value': panel_report.n_assets},
        {'step': 'benchmark_input_rows', 'value': benchmark_report.n_rows},
    ])
    preprocess_report = pd.concat([preprocess_report, extra_rows], ignore_index=True)

    return PreparedData(
        full=full,
        large=large,
        small=small,
        feature_cols=sorted(set(feature_cols)),
        rf_monthly=rf_monthly.sort_values('eom').reset_index(drop=True),
        benchmark_monthly=benchmark_monthly,
        preprocess_report=preprocess_report,
    )


def prepare_scoring_data(config: PipelineConfig) -> PreparedScoringData:
    transformed_all, feature_cols, preprocess_report, _, _ = _prepare_transformed_panel(config)
    training_sample = transformed_all.dropna(subset=['ret_lead1m', 'ret_exc_lead1m', 'me', 'be_me', 'ret_12_1']).copy()
    latest_eom = transformed_all['eom'].max()
    # Scoring keeps the latest transformed month even though that month may not yet have a realized future return.
    latest_sample = transformed_all.loc[transformed_all['eom'] == latest_eom].dropna(subset=['me', 'be_me', 'ret_12_1']).copy()
    latest_raw = _load_inputs(config)[0]
    latest_raw = latest_raw.loc[pd.to_datetime(latest_raw['eom']).dt.to_period('M').dt.to_timestamp('M') == latest_eom].copy()
    return PreparedScoringData(
        transformed_all=transformed_all,
        training_sample=training_sample,
        latest_sample=latest_sample,
        latest_raw=latest_raw,
        feature_cols=sorted(set(feature_cols)),
        preprocess_report=preprocess_report,
    )
