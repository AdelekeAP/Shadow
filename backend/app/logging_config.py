"""
Logging configuration for Shadow API.

In production (ENVIRONMENT=production): structured JSON output via python-json-logger.
In development/testing: human-readable format for easier local debugging.
"""
import logging
import os
import sys

_IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"


def setup_logging(level: str = "INFO"):
    """Configure application logging.

    Selects JSON formatting in production and a concise human-readable
    format in development/testing environments.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if _IS_PRODUCTION:
        from pythonjsonlogger import json as json_logger

        formatter = json_logger.JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(name)s  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Quieten noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
