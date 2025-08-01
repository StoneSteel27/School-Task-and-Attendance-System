import logging
import sys
from logging.handlers import RotatingFileHandler

# Define the format for the logs
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging():
    """
    Set up logging to both console and file.
    """
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Create a formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Create a handler for console output
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # Create a handler for file output
    file_handler = RotatingFileHandler("app.log", maxBytes=1000000, backupCount=1, encoding="utf8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Configure uvicorn access logger
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = root_logger.handlers
    uvicorn_access_logger.propagate = False

    # Configure uvicorn error logger
    uvicorn_error_logger = logging.getLogger("uvicorn.error")
    uvicorn_error_logger.handlers = root_logger.handlers
    uvicorn_error_logger.propagate = False
