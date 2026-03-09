import pandas as pd

from v2_model.benchmark import compare_vs_benchmark


def test_benchmark_label_uses_target_bps():
    ls = pd.DataFrame({
        'eom': ['2020-01-31', '2020-02-29'],
        'net_excess_ew_20bps': [0.01, 0.02],
        'net_excess_vw_20bps': [0.01, 0.02],
    })
    bench = pd.DataFrame({
        'eom': ['2020-01-31', '2020-02-29'],
        'benchmark_exc': [0.0, 0.0],
    })
    out = compare_vs_benchmark(ls, bench, model_name='ENET', target_bps=20, strategy_ew_col='net_excess_ew_20bps', strategy_vw_col='net_excess_vw_20bps')
    assert out['strategy'].str.contains('20bps').all()
