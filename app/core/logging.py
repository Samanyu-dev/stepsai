"""
Steps AI Logging Infrastructure.

This module configures unified, thread-safe, and asynchronous-friendly structured
logging powered by Loguru. It intercepts standard logging and manages rotation.
"""

import logging
import sys
from loguru import logger
from app.core.config import settings

class InterceptHandler(logging.Handler):
    """
    Default handler from python standard logging to intercept and route to Loguru.
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    # Remove default handlers
    logger.remove()

    # Determine log level from settings
    log_level = settings.LOG_LEVEL.upper()

    # Add console logger with rich formatting
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # Add file logger with rotation and retention policies (thread-safe)
    logger.add(
        "logs/stepsai.log",
        rotation="10 MB",
        retention="1 month",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        compression="zip",
        enqueue=True,
    )

    # Intercept all logs from standard logging library
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Re-route uvicorn and fastapi loggers
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    logger.info("Structured Loguru logging has been successfully initialized!")
