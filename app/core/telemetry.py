"""OpenTelemetry tracing hooks and Prometheus-compatible metrics (Module 2).

Metric instruments are defined once here so identity is stable across the
app — later modules (BaseAgent, LangGraph nodes, the Gemma client, HTTP
middleware) record into these shared instruments rather than each defining
their own, which would fragment the same logical counter across labels.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)
from opentelemetry.trace import Span, Tracer
from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

from app.core.config import Settings

SERVICE_NAME = "nyayaos"

_configured = False


def configure_telemetry(settings: Settings) -> None:
    """Configure the global OpenTelemetry tracer provider. Idempotent —
    safe to call more than once (e.g. across module reloads in tests)."""
    global _configured
    if _configured:
        return

    resource = Resource.create(
        {"service.name": SERVICE_NAME, "deployment.environment": settings.environment}
    )
    provider = TracerProvider(resource=resource)

    if settings.environment != "prod":
        # SimpleSpanProcessor exports synchronously on span end — no
        # background thread, which matters for short-lived processes
        # (tests, CLI scripts) as well as local dev; console export has
        # no batching benefit to begin with.
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    else:
        exporter = _build_otlp_exporter_if_available()
        if exporter is not None:
            # A real collector benefits from batching; a long-lived server
            # process is expected to call provider.shutdown() (via the
            # FastAPI lifespan hook, added once app.main exists) to flush
            # and stop this processor's background thread on exit.
            provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    _configured = True


def _build_otlp_exporter_if_available() -> Any | None:
    """OTLP export is an optional extra (pip install '.[otel]') — a prod
    deployment without a collector configured still runs, just without
    span export, rather than failing to start."""
    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # type: ignore[import-not-found]
            OTLPSpanExporter,
        )
    except ImportError:
        return None
    return OTLPSpanExporter()


def get_tracer(name: str = SERVICE_NAME) -> Tracer:
    return trace.get_tracer(name)


@contextmanager
def start_span(name: str, **attributes: Any) -> Iterator[Span]:
    """Open an OTEL span named `name` with the given attributes. Safe to
    call even before configure_telemetry() — falls back to OTel's no-op
    tracer, which accepts set_attribute() calls silently."""
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)
        yield span


# --- Prometheus metrics -----------------------------------------------

METRICS_REGISTRY = CollectorRegistry()

AGENT_EXECUTIONS_TOTAL = Counter(
    "nyaya_agent_executions_total",
    "Total agent/graph-node executions",
    ["agent_name", "status"],
    registry=METRICS_REGISTRY,
)
AGENT_EXECUTION_SECONDS = Histogram(
    "nyaya_agent_execution_seconds",
    "Agent/graph-node execution latency, in seconds",
    ["agent_name"],
    registry=METRICS_REGISTRY,
)
LLM_CALLS_TOTAL = Counter(
    "nyaya_llm_calls_total",
    "Total LLM calls",
    ["model", "status"],
    registry=METRICS_REGISTRY,
)
LLM_CALL_SECONDS = Histogram(
    "nyaya_llm_call_seconds",
    "LLM call latency, in seconds",
    ["model"],
    registry=METRICS_REGISTRY,
)
LLM_TOKENS_TOTAL = Counter(
    "nyaya_llm_tokens_total",
    "Total LLM tokens processed",
    ["model", "direction"],  # direction: "input" | "output"
    registry=METRICS_REGISTRY,
)
LLM_RETRIES_TOTAL = Counter(
    "nyaya_llm_retries_total",
    "Total LLM call retries",
    ["model"],
    registry=METRICS_REGISTRY,
)
HTTP_REQUESTS_TOTAL = Counter(
    "nyaya_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
    registry=METRICS_REGISTRY,
)
HTTP_REQUEST_SECONDS = Histogram(
    "nyaya_http_request_seconds",
    "HTTP request latency, in seconds",
    ["method", "path"],
    registry=METRICS_REGISTRY,
)


def render_metrics() -> bytes:
    """Render all registered metrics in Prometheus text exposition format,
    ready to be served from a `/metrics` route once the FastAPI app exists."""
    return generate_latest(METRICS_REGISTRY)
