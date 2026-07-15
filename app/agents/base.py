"""BaseAgent — shared machinery every agent subclasses (Module 10).

Wraps LangChain's `.with_structured_output()` so every agent is *forced*
into its declared Pydantic output contract (ADR-3): on validation
failure, the error is fed back into the conversation and the call is
retried up to max_retries times before raising AgentExecutionError.
Every call is logged via app.core.execution_logging.log_llm_call
(latency, token usage, retry count — never prompt/response text), per
docs/architecture/02-agent-architecture.md §2.1.

Persistence is deliberately NOT this class's job. docs/architecture/07-
class-diagram.md sketches a `_persist` method on BaseAgent, but pushing
that here would give every agent a database dependency, breaking the
"Agent tests: fake ChatModel, no network, no DB" testing tier in
docs/architecture/14-testing-and-implementation-plan.md §14.1.
Persistence belongs to the graph node that wraps an agent (it already
has the right Service from Module 8 to call, independently testable
against repository fakes).
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

from app.agents.exceptions import AgentExecutionError
from app.core.execution_logging import log_llm_call
from app.graph.state import CaseState

TOutput = TypeVar("TOutput", bound=BaseModel)


@dataclass(frozen=True)
class AgentResult(Generic[TOutput]):
    """Plain dataclass, not a Pydantic model — `output` was already
    validated by the LLM structured-output call; wrapping it in a second
    Pydantic model here would just add fragile runtime-generic-
    parametrization for no validation benefit."""

    output: TOutput
    latency_ms: int
    tokens_input: int
    tokens_output: int
    retry_count: int
    success: bool


def _extract_token_usage(raw_message: AIMessage | None) -> tuple[int, int]:
    if raw_message is None:
        return 0, 0
    usage = getattr(raw_message, "usage_metadata", None)
    if not usage:
        return 0, 0
    return usage.get("input_tokens", 0) or 0, usage.get("output_tokens", 0) or 0


class BaseAgent(ABC, Generic[TOutput]):
    name: str
    output_schema: type[TOutput]

    def __init__(self, llm: BaseChatModel, model_name: str, max_retries: int = 2) -> None:
        self._llm = llm
        self._model_name = model_name
        self.max_retries = max_retries

    @abstractmethod
    def _system_prompt(self) -> str:
        """Rendered from prompts/<agent_name>.py — never an inline string
        (ADR-10)."""

    @abstractmethod
    def _build_user_content(self, state: CaseState, context: Any) -> str:
        """What this agent is given to reason about, extracted from
        CaseState — deliberately per-agent. The Supervisor's override, for
        example, must return only a condensed flag summary, never the
        full case narrative (Change 1, ADR-12).

        `context` is whatever `_gather_context` returned — most agents
        ignore it; the Legal Research Agent uses it to inject retrieved
        statute chunks (Module 12)."""

    async def _gather_context(self, state: CaseState) -> Any:
        """Optional async hook run before prompt construction, for agents
        that need to fetch data the synchronous `_build_user_content`
        can't (e.g. RAG retrieval). Default no-op; override to return
        whatever `_build_user_content` needs as `context`."""
        return None

    async def run(self, state: CaseState) -> AgentResult[TOutput]:
        structured_llm = self._llm.with_structured_output(self.output_schema, include_raw=True)
        context = await self._gather_context(state)
        messages: list[BaseMessage] = [
            SystemMessage(content=self._system_prompt()),
            HumanMessage(content=self._build_user_content(state, context)),
        ]

        start = time.perf_counter()
        retry_count = 0

        while True:
            raw_result: dict[str, Any] = await structured_llm.ainvoke(messages)  # type: ignore[assignment]
            parsed = raw_result.get("parsed")
            raw_message = raw_result.get("raw")
            parsing_error = raw_result.get("parsing_error")

            input_tokens, output_tokens = _extract_token_usage(raw_message)

            if parsed is not None:
                latency = time.perf_counter() - start
                log_llm_call(
                    model=self._model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency=latency,
                    retries=retry_count,
                    success=True,
                    agent_name=self.name,
                )
                return AgentResult(
                    output=parsed,
                    latency_ms=int(latency * 1000),
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    retry_count=retry_count,
                    success=True,
                )

            if retry_count >= self.max_retries:
                latency = time.perf_counter() - start
                log_llm_call(
                    model=self._model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency=latency,
                    retries=retry_count,
                    success=False,
                    agent_name=self.name,
                )
                raise AgentExecutionError(
                    f"{self.name} failed after {retry_count} retries: {parsing_error}"
                )

            if raw_message is not None:
                messages.append(raw_message)
            messages.append(
                HumanMessage(
                    content=(
                        "Your previous response did not match the required schema: "
                        f"{parsing_error}. Respond again with valid JSON matching the "
                        "schema exactly."
                    )
                )
            )
            retry_count += 1
