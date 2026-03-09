from v2_model.cv import build_rolling_windows


def test_build_rolling_windows_count():
    months = list(range(20))
    windows = build_rolling_windows(months, train_months=6, val_months=4, test_months=2, step_months=2)
    assert len(windows) == 5
    assert windows[0].train_months == [0, 1, 2, 3, 4, 5]
    assert windows[0].test_months == [10, 11]
