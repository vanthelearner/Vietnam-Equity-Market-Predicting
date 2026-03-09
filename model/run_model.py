#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from v2_model.config import DEFAULT_MODELS, load_config
from v2_model.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Version 2 model pipeline.')
    p.add_argument('--config', type=str, required=True)
    p.add_argument('--models', type=str, default='all')
    p.add_argument('--stages', type=str, default='all')
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    models = [m.strip() for m in args.models.split(',') if m.strip()]
    if len(models) == 1 and models[0].lower() == 'all':
        models = DEFAULT_MODELS
    stages = [s.strip() for s in args.stages.split(',') if s.strip()]
    run_dir = run_pipeline(cfg, models, stages, args.config)
    print(f'Pipeline completed. Outputs saved to: {run_dir}')


if __name__ == '__main__':
    main()
