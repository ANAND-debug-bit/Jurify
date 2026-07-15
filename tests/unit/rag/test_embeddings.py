from __future__ import annotations

import pytest
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.core.config import Settings
from app.rag.embeddings import get_embeddings
from tests.conftest import ollama_is_reachable


def test_get_embeddings_returns_ollama_embeddings_for_ollama_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("EMBEDDING_MODEL", "nomic-embed-text")
    settings = Settings()

    embeddings = get_embeddings(settings)

    assert isinstance(embeddings, OllamaEmbeddings)
    assert embeddings.model == "nomic-embed-text"


def test_get_embeddings_returns_openai_embeddings_for_vllm_provider(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "vllm")
    monkeypatch.setenv("VLLM_BASE_URL", "http://localhost:8001")
    settings = Settings()

    embeddings = get_embeddings(settings)

    assert isinstance(embeddings, OpenAIEmbeddings)
    assert str(embeddings.openai_api_base).startswith("http://localhost:8001")


def test_get_embeddings_rejects_unknown_provider() -> None:
    settings = Settings()
    settings.llm.llm_provider = "bedrock"  # type: ignore[assignment]

    with pytest.raises(ValueError, match="Unknown LLM provider"):
        get_embeddings(settings)


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_live_embed_query_against_local_ollama(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL", "nomic-embed-text")
    settings = Settings()
    embeddings = get_embeddings(settings)

    vector = await embeddings.aembed_query("consumer protection complaint")

    assert len(vector) > 0
