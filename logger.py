import logging
import os
import sys
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

from handlers import TkinterHandler

LOG_FILE_PATH = 'logs/main.log'
os.makedirs('logs', exist_ok=True)

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    '%m/%d/%Y %I:%M:%S %p',
)


stream_handler = StreamHandler(sys.stdout)
file_handler = RotatingFileHandler(
    LOG_FILE_PATH, maxBytes=1_048_576, backupCount=100
)  # 100 MB


file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.INFO)


def get_logger(logger_type, tk_handler):
    logger = logging.Logger(logger_type)

    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.addHandler(tk_handler)
    return logger


def get_tk_handler(type):
    tk_handler = TkinterHandler(type)
    tk_handler.setFormatter(formatter)
    return tk_handler
