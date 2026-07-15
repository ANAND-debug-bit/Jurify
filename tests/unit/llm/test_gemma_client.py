from __future__ import annotations

import pytest
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import Settings
from app.llm.gemma_client import get_chat_model
from tests.conftest import ollama_is_reachable


def test_get_chat_model_returns_chat_ollama_for_ollama_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma3n")
    settings = Settings()

    llm = get_chat_model(settings)

    assert isinstance(llm, ChatOllama)
    assert llm.model == "gemma3n"


def test_get_chat_model_returns_chat_openai_for_vllm_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "vllm")
    monkeypatch.setenv("VLLM_BASE_URL", "http://localhost:8001")
    settings = Settings()

    llm = get_chat_model(settings)

    assert isinstance(llm, ChatOpenAI)
    assert str(llm.openai_api_base).startswith("http://localhost:8001")


def test_get_chat_model_rejects_unknown_provider(monkeypatch) -> None:
    settings = Settings()
    settings.llm.llm_provider = "bedrock"  # type: ignore[assignment]

    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_chat_model(settings)


def test_get_chat_model_construction_does_not_connect(monkeypatch) -> None:
    # No live server needed merely to construct the client — network
    # calls only happen on .ainvoke()/.invoke().
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://this-host-does-not-exist.invalid:11434")
    settings = Settings()

    llm = get_chat_model(settings)

    assert isinstance(llm, ChatOllama)


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_get_chat_model_live_call_against_local_gemma(monkeypatch) -> None:
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma2:2b")
    settings = Settings()
    llm = get_chat_model(settings)

    response = await llm.ainvoke("Reply with exactly one word: hello")

    assert response.content
