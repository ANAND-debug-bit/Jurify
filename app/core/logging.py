"""Structured logging configuration (structlog), per Module 2 of the
implementation plan (docs/architecture/14-testing-and-implementation-plan.md).

Every log emitted while request_id/case_id/user_id/agent_name/correlation_id
are bound (via bind_log_context()/log_context()) automatically carries them,
through structlog's contextvars merge — this module cannot force ad hoc log
calls elsewhere to pass these fields explicitly, but it makes them automatic
for anything emitted inside a properly-scoped context (see
app.core.middleware for the request-level scope and
app.core.execution_logging for the node/LLM-call-level scope).
execution_time is not a context var (it's meaningless outside of timing a
specific operation) — it is supplied per-event by callers that measure a
duration, notably app.core.execution_logging.

Sensitive data is never logged: _redact_sensitive strips any event-dict key
whose name appears in SENSITIVE_KEYS, and — more importantly — no helper in
this codebase accepts raw prompt/response/case-content text as a loggable
parameter in the first place (see app.core.execution_logging.log_llm_call).
"""

from __future__ import annotations

import logging
import sys
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from app.core.config import Settings

SENSITIVE_KEYS: frozenset[str] = frozenset(
    {
        "password",
        "token",
        "secret",
        "authorization",
        "access_token",
        "refresh_token",
        "prompt",
        "raw_prompt",
        "response_text",
        "message_content",
        "case_profile",
        "email",
        "phone",
        "ssn",
        "aadhaar",
        "raw_input",
    }
)

REDACTED = "[REDACTED]"


def _redact_sensitive(_logger: object, _method_name: str, event_dict: EventDict) -> EventDict:
    """structlog processor: replace values of any sensitive-named key."""
    for key in list(event_dict.keys()):
        if key.lower() in SENSITIVE_KEYS:
            event_dict[key] = REDACTED
    return event_dict


def _shared_processors() -> list[Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        _redact_sensitive,
    ]


def configure_logging(settings: Settings) -> None:
    """Configure structlog + stdlib logging. Call once at process startup.

    Production renders JSON (one object per line, machine-parseable).
    Development renders colorized, human-readable console output.
    Both structlog-originated and plain stdlib logs (uvicorn, sqlalchemy,
    etc.) are routed through the same renderer via ProcessorFormatter.
    """
    shared_processors = _shared_processors()

    renderer: Processor = (
        structlog.processors.JSONRenderer()
        if settings.environment == "prod"
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(settings.observability.log_level.upper())


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger


def new_request_id() -> str:
    return uuid.uuid4().hex


def new_correlation_id() -> str:
    return uuid.uuid4().hex


def bind_log_context(**kwargs: Any) -> Mapping[str, Any]:
    """Bind fields (request_id, case_id, user_id, agent_name,
    correlation_id, ...) to every log emitted from this point on, in this
    context (async task / thread). Returns reset tokens for
    reset_log_context(); prefer log_context() for automatic cleanup."""
    clean = {k: v for k, v in kwargs.items() if v is not None}
    return structlog.contextvars.bind_contextvars(**clean)


def reset_log_context(tokens: Mapping[str, Any]) -> None:
    structlog.contextvars.reset_contextvars(**tokens)


def clear_log_context() -> None:
    structlog.contextvars.clear_contextvars()


def current_log_context() -> dict[str, Any]:
    return dict(structlog.contextvars.get_contextvars())


@contextmanager
def log_context(**kwargs: Any) -> Iterator[None]:
    """Bind kwargs to every log emitted within this block, restoring
    whatever context existed before on exit (nesting-safe)."""
    tokens = bind_log_context(**kwargs)
    try:
        yield
    finally:
        reset_log_context(tokens)
