from __future__ import annotations

import numpy as np
from sklearn.linear_model import HuberRegressor

from .base import WindowFitResult, rmse



def run_window(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    *,
    max_iter: int = 1000,
) -> WindowFitResult:
    # Validation score for reporting.
    m_val = HuberRegressor(max_iter=max_iter)
    m_val.fit(X_train, y_train)
    val_pred = m_val.predict(X_val)
    val_rmse = rmse(y_val, val_pred)

    # Refit on train + val, then predict test.
    X_tv = np.vstack([X_train, X_val])
    y_tv = np.concatenate([y_train, y_val])
    model = HuberRegressor(max_iter=max_iter)
    model.fit(X_tv, y_tv)

    y_pred = model.predict(X_test)
    n_nonzero = int(np.count_nonzero(np.abs(model.coef_) > 0))

    return WindowFitResult(
        y_pred=y_pred,
        best_params={"max_iter": int(max_iter)},
        best_score=float(val_rmse),
        complexity={"n_nonzero_coef": n_nonzero},
        fitted_model=model,
    )
