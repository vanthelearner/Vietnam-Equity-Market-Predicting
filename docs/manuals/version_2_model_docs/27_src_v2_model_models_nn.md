# nn.py

## Purpose
Feed-forward tabular neural network with architecture search over hidden-layer grids. Source: `/model/src/v2_model/models/nn.py`.

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
Torch MLP with dropout/weight decay tuning

## Core Code
```python
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
```

## Math / logic
$$h^{(1)} = ReLU(W_1 x + b_1)$$

$$h^{(l)} = ReLU(W_l h^{(l-1)} + b_l)$$

$$\hat y = W_L h^{(L-1)} + b_L$$

## Worked Example
For a 2-layer architecture `[64, 32]`, the network maps the input feature vector into 64 hidden activations, compresses that into 32, and then outputs one predicted next-month excess return. Dropout randomly zeroes part of the hidden state during training to reduce overfit.

## Visual Flow
```mermaid
flowchart LR
    A[Input features] --> B[Dense 64 + ReLU]
    B --> C[Dropout]
    C --> D[Dense 32 + ReLU]
    D --> E[Output layer]
```

## What depends on it
- `/model/src/v2_model/pipeline.py`
- summary and portfolio construction downstream through the shared `WindowFitResult`

## Important caveats / assumptions
This is a tabular MLP, not a sequence model or an SDF deep-learning architecture.

## Linked Notes
- [Pipeline orchestrator](17_src_v2_model_pipeline.md)
- [Base model utilities](19_src_v2_model_models_base.md)
- [Main notebook](05_notebooks_00_run_and_review_model.md)

