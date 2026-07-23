"""Structured logging configuration with structlog."""

import logging
import sys
from typing import Any

from src.core.config import get_settings

try:
    import structlog
    from structlog.stdlib import BoundLogger
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal environments
    structlog = None
    BoundLogger = logging.Logger


class _CompatLogger:
    """Adapter that accepts structlog-style keyword context when structlog is unavailable.

    Delegates to stdlib logging.Logger while accepting keyword arguments
    as structured context appended to the log message.
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log at DEBUG level with optional keyword context."""
        self._logger.debug(self._format(event, kwargs))

    def info(self, event: str, **kwargs: Any) -> None:
        """Log at INFO level with optional keyword context."""
        self._logger.info(self._format(event, kwargs))

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log at WARNING level with optional keyword context."""
        self._logger.warning(self._format(event, kwargs))

    def error(self, event: str, **kwargs: Any) -> None:
        """Log at ERROR level with optional keyword context."""
        self._logger.error(self._format(event, kwargs))

    def exception(self, event: str, **kwargs: Any) -> None:
        """Log at ERROR level with exception traceback and optional keyword context."""
        self._logger.exception(self._format(event, kwargs))

    @staticmethod
    def _format(event: str, kwargs: dict[str, Any]) -> str:
        """Format a log event with structured keyword context."""
        if not kwargs:
            return event
        context = " ".join(f"{key}={value!r}" for key, value in kwargs.items())
        return f"{event} {context}"


def configure_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    if structlog is None:
        return

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
            if settings.log_format == "json"
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> BoundLogger:
    """Get a structured logger instance."""
    if structlog is None:
        return _CompatLogger(logging.getLogger(name))
    return structlog.get_logger(name)


# Configure on import
configure_logging()
