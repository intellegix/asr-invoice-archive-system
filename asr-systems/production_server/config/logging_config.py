"""
ASR Production Server - Structured Logging Configuration
Configures structlog as a stdlib bridge so all existing logger.info() calls
automatically get JSON rendering, timestamps, and context variables.
"""

import logging
import sys
from typing import Any

import structlog


def configure_logging(log_level: str = "INFO", log_format: str = "text") -> None:
    """Configure structured logging via structlog ProcessorFormatter.

    All stdlib ``logging.getLogger()`` calls flow through structlog processors,
    gaining ISO timestamps, log level, logger name, and any bound context vars.

    Args:
        log_level: Python log level name (DEBUG, INFO, WARNING, ERROR).
        log_format: ``"json"`` for machine-readable output, ``"text"`` for console.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Choose renderer based on format
    renderer: Any
    if log_format == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    # Shared processor chain applied to every log record
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    # Configure structlog itself (for direct structlog.get_logger() usage)
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Build a ProcessorFormatter that wraps structlog into stdlib
    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    # Single handler: stream to stdout (for Docker / ECS log collection)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Reset root logger — remove any existing handlers to avoid duplicates
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(level)
