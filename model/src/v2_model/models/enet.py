from __future__ import annotations

import warnings

import numpy as np
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import ElasticNet

from .base import WindowFitResult, rmse



def _alpha_grid(alpha_start: float, alpha_stop: float, alpha_num: int) -> np.ndarray:
    return np.linspace(float(alpha_start), float(alpha_stop), int(alpha_num))



def run_window(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    *,
    alpha_start: float = 0.00001,
    alpha_stop: float = 0.004,
    alpha_num: int = 20,
    l1_ratio: float = 0.5,
    max_iter: int = 10000,
    random_state: int = 42,
) -> WindowFitResult:
    alphas = _alpha_grid(alpha_start, alpha_stop, alpha_num)

    best_alpha = None
    best_rmse = np.inf

    for alpha in alphas:
        model = ElasticNet(
            alpha=float(alpha),
            l1_ratio=float(l1_ratio),
            fit_intercept=True,
            max_iter=int(max_iter),
            random_state=int(random_state),
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ConvergenceWarning)
            model.fit(X_train, y_train)

        y_val_pred = model.predict(X_val)
        cur_rmse = rmse(y_val, y_val_pred)
        if cur_rmse < best_rmse:
            best_rmse = cur_rmse
            best_alpha = float(alpha)

    X_tv = np.vstack([X_train, X_val])
    y_tv = np.concatenate([y_train, y_val])

    model = ElasticNet(
        alpha=float(best_alpha),
        l1_ratio=float(l1_ratio),
        fit_intercept=True,
        max_iter=int(max_iter),
        random_state=int(random_state),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=ConvergenceWarning)
        model.fit(X_tv, y_tv)

    y_pred = model.predict(X_test)
    n_nonzero = int(np.count_nonzero(np.abs(model.coef_) > 0))

    return WindowFitResult(
        y_pred=y_pred,
        best_params={"alpha": float(best_alpha), "l1_ratio": float(l1_ratio), "max_iter": int(max_iter)},
        best_score=float(best_rmse),
        complexity={"n_nonzero_coef": n_nonzero},
        fitted_model=model,
    )
