import pandas as pd

from v2_model.compare import build_cumulative_tables


def test_cumulative_tables_are_wealth_not_log_sum():
    tb = {
        'ENET': pd.DataFrame({
            'eom': ['2020-01-31', '2020-02-29'],
            'long_ret_ew': [0.10, 0.10],
            'short_ret_ew': [0.0, 0.0],
            'long_ret_vw': [0.10, 0.10],
            'short_ret_vw': [0.0, 0.0],
        })
    }
    bench = pd.DataFrame({'eom': ['2020-01-31', '2020-02-29'], 'benchmark_ret': [0.0, 0.0]})
    ew, _ = build_cumulative_tables(tb, bench)
    final = ew['ENET_long'].iloc[-1]
    assert abs(final - 1.21) < 1e-9
