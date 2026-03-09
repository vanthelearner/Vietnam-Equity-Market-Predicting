from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RollingWindow:
    window_id: int
    train_months: list
    val_months: list
    test_months: list


def build_rolling_windows(months: list, train_months: int, val_months: int, test_months: int, step_months: int) -> list[RollingWindow]:
    months_sorted = sorted(months)
    windows: list[RollingWindow] = []
    i = 0
    wid = 1
    n = len(months_sorted)
    while i + train_months + val_months + test_months <= n:
        windows.append(
            RollingWindow(
                window_id=wid,
                train_months=months_sorted[i : i + train_months],
                val_months=months_sorted[i + train_months : i + train_months + val_months],
                test_months=months_sorted[i + train_months + val_months : i + train_months + val_months + test_months],
            )
        )
        i += step_months
        wid += 1
    return windows
