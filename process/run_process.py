#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from v2_process.config import load_config
from v2_process.runner import run_pipeline


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Version 2 process pipeline.')
    p.add_argument('--config', type=str, required=True)
    p.add_argument('--stages', type=str, default='all')
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg, cfg_path = load_config(args.config)
    stages = [s.strip() for s in args.stages.split(',') if s.strip()]
    manifest, paths = run_pipeline(cfg, str(cfg_path), stages)
    print('Pipeline completed. Outputs saved to:', paths.root)


if __name__ == '__main__':
    main()
