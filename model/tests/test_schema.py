import pandas as pd

from v2_model.schema import validate_benchmark_schema, validate_panel_schema


def test_validate_panel_schema_ok():
    panel = pd.DataFrame({
        'id': ['A', 'A'],
        'eom': ['2020-01-31', '2020-02-29'],
        'prc': [10.0, 11.0],
        'me': [100000.0, 120000.0],
        'ret': [0.02, 0.01],
        'ret_exc': [0.018, 0.009],
        'ret_exc_lead1m': [0.009, 0.005],
        'be_me': [0.8, 0.85],
        'ret_12_1': [0.10, 0.12],
    })
    report = validate_panel_schema(panel)
    assert report.n_rows == 2
    assert report.n_assets == 1


def test_validate_benchmark_schema_ok():
    bench = pd.DataFrame({'eom': ['2020-01-31', '2020-02-29'], 'benchmark_ret': [0.01, 0.02]})
    report = validate_benchmark_schema(bench)
    assert report.n_rows == 2
