import numpy as np

from v2_model.models.base import huber_loss_error


def test_huber_loss_tail_formula():
    y_true = np.array([0.0])
    y_pred = np.array([2.0])
    loss = huber_loss_error(y_true, y_pred, delta=1.0)
    assert abs(loss - 1.5) < 1e-9
