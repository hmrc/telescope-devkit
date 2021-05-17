import logging
import os
import sys

from telemetry.telescope_devkit import APP_NAME
from telemetry.telescope_devkit.filesystem import get_repo_path


def create_app_logger(level: str = logging.DEBUG):
    level = level.upper() if isinstance(level, str) else level

    logger = logging.getLogger(APP_NAME)
    logger.setLevel(level)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


def get_app_logger():
    return logging.getLogger(APP_NAME)

def create_file_logger(filename: str, level: str = logging.DEBUG):
    level = level.upper() if isinstance(level, str) else level

    logger = logging.getLogger(filename)
    logger.setLevel(level)

    log_dir = os.path.join(get_repo_path(), "log")
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    file_handler = logging.FileHandler(os.path.join(log_dir, filename))
    file_handler.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
