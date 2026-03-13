# pcr.py

## Purpose
Principal components regression using PCA then linear regression. Source: `/model/src/v2_model/models/pcr.py`.

## Where it sits in the pipeline
Called by `/model/src/v2_model/pipeline.py` inside each rolling train/validation/test window. The file returns a standardized `WindowFitResult` so the rest of the pipeline can treat different model families uniformly.

## Inputs
- `X_train`, `y_train`
- `X_val`, `y_val`
- `X_test`
- model-specific hyperparameters from config

## Outputs / side effects
- returns a `WindowFitResult`
- no direct file writes; output persistence is handled by `pipeline.py`

## How the code works
PCA + LinearRegression pipeline

## Core Code
```python
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
```

## Math / logic
$$Z = X V_k$$

$$y = Z\beta + \varepsilon$$

PCR first compresses $X$ with PCA, then regresses on the retained components.

## Worked Example
If 40 features are highly collinear, PCR can reduce them to a smaller number of principal components before fitting a linear model. The validation step chooses how many components to keep.

## Visual Flow
```mermaid
flowchart LR
    A[X] --> B[PCA]
    B --> C[top k components]
    C --> D[linear regression]
    D --> E[predictions]
```

## What depends on it
- `/model/src/v2_model/pipeline.py`
- summary and portfolio construction downstream through the shared `WindowFitResult`

## Important caveats / assumptions
PCR is unsupervised in the dimensionality-reduction stage, so it may retain variance that is not useful for prediction.

## Linked Notes
- [Pipeline orchestrator](17_src_v2_model_pipeline.md)
- [Base model utilities](19_src_v2_model_models_base.md)
- [Main notebook](05_notebooks_00_run_and_review_model.md)

