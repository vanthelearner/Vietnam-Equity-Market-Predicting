from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression

from .base import WindowFitResult, rmse



def _valid_components(components: list[int], n_features: int, n_rows: int) -> list[int]:
    cap = max(1, min(int(n_features), int(n_rows)))
    vals = sorted({int(c) for c in components if int(c) >= 1 and int(c) <= cap})
    return vals or [1]



def _fit_predict_pcr(X_fit: np.ndarray, y_fit: np.ndarray, X_pred: np.ndarray, n_components: int):
    pca = PCA(n_components=int(n_components))
    X_fit_p = pca.fit_transform(X_fit)
    reg = LinearRegression()
    reg.fit(X_fit_p, y_fit)
    X_pred_p = pca.transform(X_pred)
    y_pred = reg.predict(X_pred_p)
    return y_pred, pca, reg



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
        y_val_pred, _, _ = _fit_predict_pcr(X_train, y_train, X_val, k)
        cur_rmse = rmse(y_val, y_val_pred)
        if cur_rmse < best_rmse:
            best_rmse = cur_rmse
            best_k = int(k)

    X_tv = np.vstack([X_train, X_val])
    y_tv = np.concatenate([y_train, y_val])
    y_pred, pca, reg = _fit_predict_pcr(X_tv, y_tv, X_test, best_k)

    return WindowFitResult(
        y_pred=y_pred,
        best_params={"n_components": int(best_k)},
        best_score=float(best_rmse),
        complexity={"n_components": int(best_k)},
        fitted_model={"pca": pca, "reg": reg},
    )
