"""Reusable execution-logging primitives (Module 2).

These are the pieces later used to automatically log every LangGraph node
execution and every LLM call — built now, ahead of the agents/graph
themselves (Modules 9+), as callable-agnostic decorators/context managers
so BaseAgent and graph nodes can wrap around them without this module
depending on anything not yet built (CaseState, agents/, graph/ don't
exist yet).

Per-case context (case_id, user_id, correlation_id) is expected to already
be bound via app.core.logging.log_context by the caller (e.g. a service
method) before a node runs — log_node_execution only adds agent_name and
timing on top of whatever context is already active.
"""

from __future__ import annotations

import functools
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import ParamSpec, TypeVar

from app.core.logging import get_logger, log_context
from app.core.telemetry import (
    AGENT_EXECUTION_SECONDS,
    AGENT_EXECUTIONS_TOTAL,
    LLM_CALL_SECONDS,
    LLM_CALLS_TOTAL,
    LLM_RETRIES_TOTAL,
    LLM_TOKENS_TOTAL,
    start_span,
)

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


@asynccontextmanager
async def log_node_execution(node_name: str) -> AsyncIterator[None]:
    """Wrap a single LangGraph node's execution: binds agent_name to the
    log context for the duration, times it, emits node_started /
    node_completed / node_failed, records Prometheus counters + histogram,
    and opens an OTEL span. Never receives or logs the node's state payload
    — only the node's identity and timing are logged."""
    start = time.perf_counter()
    with start_span("graph_node", agent_name=node_name), log_context(agent_name=node_name):
        logger.info("node_started", node_name=node_name)
        try:
            yield
        except Exception:
            execution_time = time.perf_counter() - start
            AGENT_EXECUTIONS_TOTAL.labels(agent_name=node_name, status="failed").inc()
            AGENT_EXECUTION_SECONDS.labels(agent_name=node_name).observe(execution_time)
            logger.exception(
                "node_failed", node_name=node_name, execution_time=execution_time
            )
            raise
        else:
            execution_time = time.perf_counter() - start
            AGENT_EXECUTIONS_TOTAL.labels(agent_name=node_name, status="success").inc()
            AGENT_EXECUTION_SECONDS.labels(agent_name=node_name).observe(execution_time)
            logger.info(
                "node_completed", node_name=node_name, execution_time=execution_time
            )


def with_node_logging(
    node_name: str,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator form of log_node_execution, for async LangGraph node
    functions: `@with_node_logging("legal_research")`."""

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            async with log_node_execution(node_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def log_llm_call(
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency: float,
    retries: int = 0,
    success: bool = True,
    agent_name: str | None = None,
) -> None:
    """Log one completed LLM call's metadata and record its metrics.

    Deliberately accepts only metadata — there is no parameter for prompt
    or response text, so sensitive case content structurally cannot reach
    this log line (defense in depth on top of app.core.logging's
    key-based redaction)."""
    status = "success" if success else "failed"
    LLM_CALLS_TOTAL.labels(model=model, status=status).inc()
    LLM_CALL_SECONDS.labels(model=model).observe(latency)
    LLM_TOKENS_TOTAL.labels(model=model, direction="input").inc(input_tokens)
    LLM_TOKENS_TOTAL.labels(model=model, direction="output").inc(output_tokens)
    if retries:
        LLM_RETRIES_TOTAL.labels(model=model).inc(retries)

    logger.info(
        "llm_call",
        model=model,
        agent_name=agent_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency=latency,
        execution_time=latency,
        retries=retries,
        success=success,
    )
