from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from pydantic import BaseModel, ConfigDict

from app.agents.base import BaseAgent
from app.agents.exceptions import AgentExecutionError
from app.graph.state import CaseState, create_initial_state
from tests.unit.agents.fakes import FakeStructuredChatModel


class _EchoOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: str


class _EchoAgent(BaseAgent[_EchoOutput]):
    name = "echo_test_agent"
    output_schema = _EchoOutput

    def _system_prompt(self) -> str:
        return "You are a test echo agent."

    def _build_user_content(self, state: CaseState, context: Any) -> str:
        return "echo"


def _state() -> CaseState:
    return create_initial_state(uuid4(), uuid4())


async def test_run_returns_parsed_output_on_first_success() -> None:
    llm = FakeStructuredChatModel(responses=[_EchoOutput(value="ok")])
    agent = _EchoAgent(llm, model_name="fake-model")

    result = await agent.run(_state())

    assert result.success is True
    assert result.output.value == "ok"
    assert result.retry_count == 0
    assert result.tokens_input == 10
    assert result.tokens_output == 5


async def test_run_retries_once_then_succeeds() -> None:
    llm = FakeStructuredChatModel(responses=["not valid json", _EchoOutput(value="ok")])
    agent = _EchoAgent(llm, model_name="fake-model")

    result = await agent.run(_state())

    assert result.success is True
    assert result.retry_count == 1
    assert result.output.value == "ok"


async def test_run_raises_after_exhausting_retries() -> None:
    llm = FakeStructuredChatModel(responses=["bad-1", "bad-2", "bad-3"])
    agent = _EchoAgent(llm, model_name="fake-model", max_retries=2)

    with pytest.raises(AgentExecutionError, match="echo_test_agent failed after 2 retries"):
        await agent.run(_state())


async def test_run_uses_max_retries_from_constructor() -> None:
    # max_retries=0 -> a single attempt, no retries at all.
    llm = FakeStructuredChatModel(responses=["bad"])
    agent = _EchoAgent(llm, model_name="fake-model", max_retries=0)

    with pytest.raises(AgentExecutionError, match="failed after 0 retries"):
        await agent.run(_state())


async def test_run_logs_llm_call_with_expected_fields(capsys) -> None:
    from app.core.config import Settings
    from app.core.logging import clear_log_context, configure_logging

    configure_logging(Settings(environment="prod"))
    clear_log_context()

    llm = FakeStructuredChatModel(responses=[_EchoOutput(value="ok")])
    agent = _EchoAgent(llm, model_name="fake-model")

    await agent.run(_state())

    import json

    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    llm_call_events = [line for line in lines if line.get("event") == "llm_call"]
    assert len(llm_call_events) == 1
    event = llm_call_events[0]
    assert event["model"] == "fake-model"
    assert event["agent_name"] == "echo_test_agent"
    assert event["success"] is True
    assert "prompt" not in event
    assert "response" not in event
