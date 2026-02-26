"""Structured logging with PII redaction."""

from __future__ import annotations

import re
from typing import Any

import structlog

_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (_EMAIL_RE, "[EMAIL_REDACTED]"),
    (_SSN_RE, "[SSN_REDACTED]"),
    (_PHONE_RE, "[PHONE_REDACTED]"),
]


def _redact_value(value: Any) -> Any:
    """Redact PII patterns from a string value."""
    if not isinstance(value, str):
        return value
    result = value
    for pattern, replacement in _PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def pii_redaction_processor(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Structlog processor that redacts PII from all string values."""
    return {k: _redact_value(v) for k, v in event_dict.items()}


def configure_logging() -> None:
    """Set up structlog with JSON rendering and PII redaction."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            pii_redaction_processor,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a named structured logger."""
    return structlog.get_logger(name)  # type: ignore[return-value]
