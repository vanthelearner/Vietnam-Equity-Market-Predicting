from __future__ import annotations

import logging


def get_logger() -> logging.Logger:
    logger = logging.getLogger('v2_process')
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
