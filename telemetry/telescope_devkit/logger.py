import logging
import sys

from telemetry.telescope_devkit import APP_NAME


def create_app_logger(level: str = logging.DEBUG):
    level = level.upper() if isinstance(level, str) else level

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def get_app_logger():
    return logging.getLogger(APP_NAME)
