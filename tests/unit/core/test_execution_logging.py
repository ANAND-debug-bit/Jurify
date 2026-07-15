import json

import pytest

from app.core.config import Settings
from app.core.execution_logging import log_llm_call, log_node_execution, with_node_logging
from app.core.logging import clear_log_context, configure_logging, current_log_context
from app.core.telemetry import (
    AGENT_EXECUTIONS_TOTAL,
    AGENT_EXECUTION_SECONDS,
    LLM_CALLS_TOTAL,
    LLM_RETRIES_TOTAL,
    LLM_TOKENS_TOTAL,
)


@pytest.fixture(autouse=True)
def _clean_log_context():
    clear_log_context()
    yield
    clear_log_context()


async def test_log_node_execution_binds_agent_name_during_block() -> None:
    async with log_node_execution("legal_research"):
        assert current_log_context()["agent_name"] == "legal_research"

    assert "agent_name" not in current_log_context()


async def test_log_node_execution_records_success_metrics() -> None:
    before = AGENT_EXECUTIONS_TOTAL.labels(
        agent_name="metrics_test_node", status="success"
    )._value.get()
    before_hist_count = AGENT_EXECUTION_SECONDS.labels(agent_name="metrics_test_node")._sum.get()

    async with log_node_execution("metrics_test_node"):
        pass

    after = AGENT_EXECUTIONS_TOTAL.labels(
        agent_name="metrics_test_node", status="success"
    )._value.get()
    after_hist_sum = AGENT_EXECUTION_SECONDS.labels(agent_name="metrics_test_node")._sum.get()

    assert after == before + 1
    assert after_hist_sum >= before_hist_count


async def test_log_node_execution_records_failure_and_reraises() -> None:
    before = AGENT_EXECUTIONS_TOTAL.labels(
        agent_name="failing_node", status="failed"
    )._value.get()

    with pytest.raises(ValueError, match="node exploded"):
        async with log_node_execution("failing_node"):
            raise ValueError("node exploded")

    after = AGENT_EXECUTIONS_TOTAL.labels(agent_name="failing_node", status="failed")._value.get()
    assert after == before + 1


async def test_log_node_execution_emits_started_and_completed_events(capsys) -> None:
    configure_logging(Settings(environment="prod"))

    async with log_node_execution("evidence_analysis"):
        pass

    lines = capsys.readouterr().out.strip().splitlines()
    events = [json.loads(line)["event"] for line in lines]

    assert "node_started" in events
    assert "node_completed" in events
    completed = next(json.loads(line) for line in lines if json.loads(line)["event"] == "node_completed")
    assert "execution_time" in completed
    assert completed["node_name"] == "evidence_analysis"


async def test_with_node_logging_decorator_wraps_async_function() -> None:
    @with_node_logging("case_intake")
    async def fake_node(x: int) -> int:
        assert current_log_context()["agent_name"] == "case_intake"
        return x * 2

    result = await fake_node(21)

    assert result == 42
    assert "agent_name" not in current_log_context()


def test_log_llm_call_records_metrics_and_never_logs_prompt_param() -> None:
    import inspect

    signature = inspect.signature(log_llm_call)
    assert "prompt" not in signature.parameters
    assert "response" not in signature.parameters
    assert "response_text" not in signature.parameters

    before_calls = LLM_CALLS_TOTAL.labels(model="gemma3n-test", status="success")._value.get()
    before_tokens_in = LLM_TOKENS_TOTAL.labels(model="gemma3n-test", direction="input")._value.get()
    before_retries = LLM_RETRIES_TOTAL.labels(model="gemma3n-test")._value.get()

    log_llm_call(
        model="gemma3n-test",
        input_tokens=120,
        output_tokens=45,
        latency=0.83,
        retries=1,
        success=True,
        agent_name="legal_research",
    )

    assert LLM_CALLS_TOTAL.labels(model="gemma3n-test", status="success")._value.get() == before_calls + 1
    assert (
        LLM_TOKENS_TOTAL.labels(model="gemma3n-test", direction="input")._value.get()
        == before_tokens_in + 120
    )
    assert LLM_RETRIES_TOTAL.labels(model="gemma3n-test")._value.get() == before_retries + 1


def test_log_llm_call_emits_structured_event_without_prompt_text(capsys) -> None:
    configure_logging(Settings(environment="prod"))

    log_llm_call(
        model="gemma3n-test2",
        input_tokens=10,
        output_tokens=5,
        latency=0.12,
        success=True,
    )

    line = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(line)

    assert payload["event"] == "llm_call"
    assert payload["model"] == "gemma3n-test2"
    assert payload["input_tokens"] == 10
    assert payload["output_tokens"] == 5
    assert "execution_time" in payload
    assert "prompt" not in payload
    assert "response" not in payload
