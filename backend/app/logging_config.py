"""
Structured JSON logging configuration for Shadow API.
Replaces basic logging with JSON-formatted output including request correlation IDs.
"""
import logging
import sys
from pythonjsonlogger import json as json_logger


def setup_logging(level: str = "INFO"):
    """Configure structured JSON logging for the application."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # JSON handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    formatter = json_logger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Quieten noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
