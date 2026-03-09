from __future__ import annotations

import numpy as np
from sklearn.cross_decomposition import PLSRegression

from .base import WindowFitResult, rmse



def _valid_components(components: list[int], n_features: int, n_rows: int) -> list[int]:
    cap = max(1, min(int(n_features), int(n_rows)))
    vals = sorted({int(c) for c in components if int(c) >= 1 and int(c) <= cap})
    return vals or [1]



def run_window(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    *,
    components: list[int],
) -> WindowFitResult:
    comps = _valid_components(components, n_features=X_train.shape[1], n_rows=X_train.shape[0])

    best_k = None
    best_rmse = np.inf

    for k in comps:
        model = PLSRegression(n_components=int(k), scale=False)
        model.fit(X_train, y_train)
        y_val_pred = model.predict(X_val).ravel()
        cur_rmse = rmse(y_val, y_val_pred)
        if cur_rmse < best_rmse:
            best_rmse = cur_rmse
            best_k = int(k)

    X_tv = np.vstack([X_train, X_val])
    y_tv = np.concatenate([y_train, y_val])
    model = PLSRegression(n_components=int(best_k), scale=False)
    model.fit(X_tv, y_tv)
    y_pred = model.predict(X_test).ravel()

    return WindowFitResult(
        y_pred=y_pred,
        best_params={"n_components": int(best_k)},
        best_score=float(best_rmse),
        complexity={"n_components": int(best_k)},
        fitted_model=model,
    )
