from __future__ import annotations

import itertools

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .base import WindowFitResult, rmse


class FeedForwardNet(nn.Module):
    def __init__(self, input_dim: int, hidden_layers: tuple[int, ...], dropout: float):
        super().__init__()
        layers: list[nn.Module] = []
        prev = int(input_dim)
        for width in hidden_layers:
            layers.append(nn.Linear(prev, int(width)))
            layers.append(nn.ReLU())
            if float(dropout) > 0:
                layers.append(nn.Dropout(float(dropout)))
            prev = int(width)
        layers.append(nn.Linear(prev, 1))
        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def _to_tensor(x: np.ndarray) -> torch.Tensor:
    return torch.as_tensor(x, dtype=torch.float32)


def _resolve_device(device: str) -> torch.device:
    return torch.device(device if device == 'cpu' or torch.cuda.is_available() else 'cpu')


def _train_once(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    *,
    hidden_layers: tuple[int, ...],
    dropout: float,
    learning_rate: float,
    weight_decay: float,
    batch_size: int,
    epochs: int,
    patience: int,
    seed: int,
    device: str,
) -> tuple[FeedForwardNet, float, int]:
    torch.manual_seed(int(seed))
    np.random.seed(int(seed))

    dev = _resolve_device(device)
    model = FeedForwardNet(X_train.shape[1], hidden_layers, dropout).to(dev)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(learning_rate), weight_decay=float(weight_decay))
    loss_fn = nn.MSELoss()

    ds = TensorDataset(_to_tensor(X_train), _to_tensor(y_train))
    loader = DataLoader(ds, batch_size=min(int(batch_size), len(ds)), shuffle=True)
    Xv = _to_tensor(X_val).to(dev)
    yv = _to_tensor(y_val).to(dev)

    best_state = None
    best_rmse = np.inf
    best_epoch = 0
    stale = 0

    for epoch in range(1, int(epochs) + 1):
        model.train()
        for xb, yb in loader:
            xb = xb.to(dev)
            yb = yb.to(dev)
            optimizer.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            optimizer.step()

        model.eval()
        with torch.no_grad():
            val_pred = model(Xv).detach().cpu().numpy()
        cur_rmse = rmse(y_val, val_pred)
        if cur_rmse < best_rmse:
            best_rmse = float(cur_rmse)
            best_epoch = int(epoch)
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
            if stale >= int(patience):
                break

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, float(best_rmse), int(best_epoch)


def _fit_fixed_epochs(
    X_train: np.ndarray,
    y_train: np.ndarray,
    *,
    hidden_layers: tuple[int, ...],
    dropout: float,
    learning_rate: float,
    weight_decay: float,
    batch_size: int,
    epochs: int,
    seed: int,
    device: str,
) -> FeedForwardNet:
    torch.manual_seed(int(seed))
    np.random.seed(int(seed))

    dev = _resolve_device(device)
    model = FeedForwardNet(X_train.shape[1], hidden_layers, dropout).to(dev)
    optimizer = torch.optim.Adam(model.parameters(), lr=float(learning_rate), weight_decay=float(weight_decay))
    loss_fn = nn.MSELoss()

    ds = TensorDataset(_to_tensor(X_train), _to_tensor(y_train))
    loader = DataLoader(ds, batch_size=min(int(batch_size), len(ds)), shuffle=True)

    for _ in range(max(int(epochs), 1)):
        model.train()
        for xb, yb in loader:
            xb = xb.to(dev)
            yb = yb.to(dev)
            optimizer.zero_grad()
            pred = model(xb)
            loss = loss_fn(pred, yb)
            loss.backward()
            optimizer.step()

    return model


def _predict(model: FeedForwardNet, X: np.ndarray, device: str) -> np.ndarray:
    dev = _resolve_device(device)
    model = model.to(dev)
    model.eval()
    with torch.no_grad():
        pred = model(_to_tensor(X).to(dev)).detach().cpu().numpy()
    return pred.astype(float)


def run_window(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    X_test: np.ndarray,
    *,
    hidden_layer_grid: list[list[int]],
    dropout_grid: list[float],
    learning_rate_grid: list[float],
    weight_decay_grid: list[float],
    batch_size: int = 1024,
    epochs: int = 80,
    patience: int = 8,
    random_state: int = 42,
    device: str = 'cpu',
) -> WindowFitResult:
    best = None
    best_score = np.inf

    for hidden_layers, dropout, lr, wd in itertools.product(hidden_layer_grid, dropout_grid, learning_rate_grid, weight_decay_grid):
        hidden_layers = tuple(int(x) for x in hidden_layers)
        model, val_rmse, best_epoch = _train_once(
            X_train,
            y_train,
            X_val,
            y_val,
            hidden_layers=hidden_layers,
            dropout=float(dropout),
            learning_rate=float(lr),
            weight_decay=float(wd),
            batch_size=int(batch_size),
            epochs=int(epochs),
            patience=int(patience),
            seed=int(random_state),
            device=device,
        )
        if val_rmse < best_score:
            best_score = float(val_rmse)
            best = {
                'hidden_layers': hidden_layers,
                'dropout': float(dropout),
                'learning_rate': float(lr),
                'weight_decay': float(wd),
                'best_epoch': int(best_epoch),
            }

    X_tv = np.vstack([X_train, X_val])
    y_tv = np.concatenate([y_train, y_val])
    final_model = _fit_fixed_epochs(
        X_tv,
        y_tv,
        hidden_layers=best['hidden_layers'],
        dropout=best['dropout'],
        learning_rate=best['learning_rate'],
        weight_decay=best['weight_decay'],
        batch_size=int(batch_size),
        epochs=max(int(best['best_epoch']), 1),
        seed=int(random_state),
        device=device,
    )
    y_pred = _predict(final_model, X_test, device=device)
    n_params = int(sum(p.numel() for p in final_model.parameters()))

    return WindowFitResult(
        y_pred=y_pred,
        best_params={
            'hidden_layers': list(best['hidden_layers']),
            'dropout': float(best['dropout']),
            'learning_rate': float(best['learning_rate']),
            'weight_decay': float(best['weight_decay']),
            'best_epoch': int(best['best_epoch']),
            'batch_size': int(batch_size),
        },
        best_score=float(best_score),
        complexity={
            'n_layers': int(len(best['hidden_layers'])),
            'hidden_layers': '-'.join(str(x) for x in best['hidden_layers']),
            'n_params': int(n_params),
            'best_epoch': int(best['best_epoch']),
        },
        fitted_model=final_model,
    )
