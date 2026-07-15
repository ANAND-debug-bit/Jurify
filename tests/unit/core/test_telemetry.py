from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from app.core import telemetry
from app.core.config import Settings
from app.core.telemetry import (
    AGENT_EXECUTIONS_TOTAL,
    LLM_CALLS_TOTAL,
    get_tracer,
    render_metrics,
    start_span,
)


def test_configure_telemetry_is_idempotent() -> None:
    telemetry._configured = False
    settings = Settings(environment="dev")

    telemetry.configure_telemetry(settings)
    assert telemetry._configured is True
    telemetry.configure_telemetry(settings)  # second call must not raise
    assert telemetry._configured is True


def test_get_tracer_returns_usable_tracer() -> None:
    tracer = get_tracer()
    assert hasattr(tracer, "start_as_current_span")


def test_start_span_records_name_and_attributes(monkeypatch) -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    isolated_tracer = provider.get_tracer("test")

    monkeypatch.setattr(telemetry, "get_tracer", lambda name=telemetry.SERVICE_NAME: isolated_tracer)

    with start_span("graph_node", agent_name="risk_assessment", case_id="c1"):
        pass

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "graph_node"
    attributes = spans[0].attributes
    assert attributes is not None
    assert attributes["agent_name"] == "risk_assessment"
    assert attributes["case_id"] == "c1"


def test_start_span_skips_none_attributes(monkeypatch) -> None:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    isolated_tracer = provider.get_tracer("test")

    monkeypatch.setattr(telemetry, "get_tracer", lambda name=telemetry.SERVICE_NAME: isolated_tracer)

    with start_span("graph_node", agent_name="risk_assessment", case_id=None):
        pass

    spans = exporter.get_finished_spans()
    attributes = spans[0].attributes
    assert attributes is not None
    assert "case_id" not in attributes


def test_agent_executions_counter_increments() -> None:
    before = AGENT_EXECUTIONS_TOTAL.labels(agent_name="unit_test_agent", status="success")._value.get()

    AGENT_EXECUTIONS_TOTAL.labels(agent_name="unit_test_agent", status="success").inc()

    after = AGENT_EXECUTIONS_TOTAL.labels(agent_name="unit_test_agent", status="success")._value.get()
    assert after == before + 1


def test_llm_calls_counter_increments() -> None:
    before = LLM_CALLS_TOTAL.labels(model="gemma3n", status="success")._value.get()

    LLM_CALLS_TOTAL.labels(model="gemma3n", status="success").inc()

    after = LLM_CALLS_TOTAL.labels(model="gemma3n", status="success")._value.get()
    assert after == before + 1


def test_render_metrics_returns_prometheus_text_format() -> None:
    AGENT_EXECUTIONS_TOTAL.labels(agent_name="render_test_agent", status="success").inc()

    output = render_metrics()

    assert isinstance(output, bytes)
    text = output.decode("utf-8")
    assert "nyaya_agent_executions_total" in text
    assert 'agent_name="render_test_agent"' in text
