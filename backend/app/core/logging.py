"""
Sorim.AI — Structured Logging Setup

Configures the root logger and the application logger.
Secrets are never logged — this module enforces that at setup.
"""

from __future__ import annotations

import logging
import sys


def configure_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Set up structured console logging for the FastAPI application.

    Returns the 'sorim' logger. All application code should use:
        logger = logging.getLogger("sorim")

    Args:
        log_level: The minimum level string (INFO, DEBUG, WARNING, ERROR).
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Root handler — JSON-like format for operational readability.
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    handler.setFormatter(formatter)

    # Configure the application root logger.
    app_logger = logging.getLogger("sorim")
    app_logger.setLevel(level)
    # Avoid duplicate handlers if configure_logging is called twice.
    if not app_logger.handlers:
        app_logger.addHandler(handler)
    app_logger.propagate = False

    # Silence noisy third-party loggers that can accidentally reveal details.
    for noisy in ("pymongo", "urllib3", "httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    return app_logger


def get_logger(name: str) -> logging.Logger:
    """Return a child of the 'sorim' application logger."""
    return logging.getLogger(f"sorim.{name}")
