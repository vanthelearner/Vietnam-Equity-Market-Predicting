from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class WindowFitResult:
    y_pred: np.ndarray
    best_params: dict[str, Any]
    best_score: float
    complexity: dict[str, Any]
    fitted_model: Any



def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))



def r2_oos_zero(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    den = float(np.sum(y_true**2))
    if den <= 0:
        return np.nan
    return float(1.0 - np.sum((y_true - y_pred) ** 2) / den)



def huber_loss_error(y_true: np.ndarray, y_pred: np.ndarray, delta: float = 1.35) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    err = y_true - y_pred
    abs_err = np.abs(err)
    quad = abs_err <= delta
    loss = np.where(quad, 0.5 * (err**2), delta * (abs_err - 0.5 * delta))
    return float(np.sum(loss))
