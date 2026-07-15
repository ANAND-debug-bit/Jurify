"""FakeStructuredChatModel — a BaseChatModel test double that returns a
pre-programmed sequence of structured-output results (docs/architecture/
14-testing-and-implementation-plan.md §14.1: "agent tests use a
FakeChatModel... rather than unittest.mock.Mock").

It overrides `with_structured_output` directly (rather than implementing
LangChain's default tool-calling machinery) so BaseAgent's own retry/
logging/error-handling logic is exercised exactly as it would be against
a real provider, deterministically and without network access. The
deeper "does LangChain's structured-output parsing actually work against
Gemma" question is separately verified by the live Ollama tests in this
same package.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.runnables import Runnable
from pydantic import BaseModel


class _FakeStructuredRunnable(Runnable[Any, dict[str, Any]]):
    def __init__(self, model: FakeStructuredChatModel) -> None:
        self._model = model

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError("FakeStructuredChatModel only supports async invocation")

    async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> dict[str, Any]:
        index = self._model.call_count
        self._model.call_count += 1
        item = self._model.responses[index]

        if isinstance(item, BaseModel):
            return {
                "raw": AIMessage(
                    content=item.model_dump_json(),
                    usage_metadata={
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "total_tokens": 15,
                    },
                ),
                "parsed": item,
                "parsing_error": None,
            }

        # Any non-BaseModel entry simulates a validation/parsing failure.
        return {
            "raw": AIMessage(content=str(item)),
            "parsed": None,
            "parsing_error": ValueError(str(item)),
        }


class FakeStructuredChatModel(BaseChatModel):
    """responses: the sequence of results to return, one per call to
    .with_structured_output(...).ainvoke(...) — a BaseModel instance for
    a successful parse, or any other value (e.g. a str) to simulate a
    parsing failure on that attempt."""

    responses: Sequence[Any] = ()
    call_count: int = 0

    @property
    def _llm_type(self) -> str:
        return "fake-structured-chat-model"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=""))])

    def with_structured_output(self, schema: Any, **kwargs: Any) -> Runnable[Any, dict[str, Any]]:
        return _FakeStructuredRunnable(self)
