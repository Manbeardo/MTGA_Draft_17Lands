import os
import sys
import logging
import logging.handlers

from src.logger.CustomFormatter import CustomFormatter


DEBUG_LOG_FOLDER = os.path.join(os.getcwd(), "Debug")
DEBUG_LOG_FILE = os.path.join(DEBUG_LOG_FOLDER, "debug.log")
DEBUG_LOGGER_NAME = "debug_log"

if not os.path.exists(DEBUG_LOG_FOLDER):
    os.makedirs(DEBUG_LOG_FOLDER)


# Create the shared logger
shared_logger = logging.getLogger(DEBUG_LOGGER_NAME)
shared_logger.setLevel(logging.DEBUG)

# Create a file handler for the shared logger
handlers = {
    logging.handlers.TimedRotatingFileHandler(
        DEBUG_LOG_FILE, when='D', interval=1, backupCount=7, utc=True),
    logging.StreamHandler(sys.stdout),
}

formatter = CustomFormatter()

for handler in handlers:
    handler.setFormatter(formatter)
    shared_logger.addHandler(handler)


def create_logger():
    logger = logging.getLogger(DEBUG_LOGGER_NAME)
    return logger
