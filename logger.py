import logging
import os
import sys
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

from handlers import TkinterHandler

LOG_FILE_PATH = 'logs/main.log'
os.makedirs('logs', exist_ok=True)

logger = logging.Logger('your-module')
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s',
    '%m/%d/%Y %I:%M:%S %p',
)

stream_handler = StreamHandler(sys.stdout)
file_handler = RotatingFileHandler(LOG_FILE_PATH, maxBytes=1_048_576, backupCount=100)  # 100 MB
tk_handler = TkinterHandler()

file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
tk_handler.setFormatter(formatter)

file_handler.setLevel(logging.DEBUG)
stream_handler.setLevel(logging.INFO)
tk_handler.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.addHandler(tk_handler)
