import logging
import sys
import traceback
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "app.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "error.log")

def setup_logger():
    # Make sure logs directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Base logger configuration
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Formatter for log messages
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. Console Handler (for terminal)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. General App Log Handler (Rolling file max 5MB, keep 3 backups)
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 3. Error Log Handler (Only for warnings and errors)
    error_handler = RotatingFileHandler(ERROR_LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)

    # Global Exception Hook to capture crashes
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Ignore KeyboardInterrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception

    return logger
