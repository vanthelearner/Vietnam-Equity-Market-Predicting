from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


def timestamped_run_dir(base_output: str | Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out = Path(base_output) / f"run_{ts}"
    out.mkdir(parents=True, exist_ok=True)
    return out


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_df(df: pd.DataFrame, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)


def write_json(obj: dict[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
