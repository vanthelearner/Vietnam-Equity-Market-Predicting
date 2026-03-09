from __future__ import annotations

import numpy as np

from .ols_huber import run_window as run_window_ols_huber
from .base import WindowFitResult



def run_window(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    *,
    max_iter: int = 1000,
) -> WindowFitResult:
    return run_window_ols_huber(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        X_test=X_test,
        max_iter=max_iter,
    )
