"""Embedding model factory (Module 12).

Mirrors app.llm.gemma_client.get_chat_model()'s provider-branching
pattern — the retriever depends on this function's return type
(Embeddings), never on OllamaEmbeddings/OpenAIEmbeddings directly.
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings

from app.core.config import Settings


def get_embeddings(settings: Settings) -> Embeddings:
    llm_settings = settings.llm

    if llm_settings.llm_provider == "ollama":
        return OllamaEmbeddings(
            model=llm_settings.embedding_model, base_url=llm_settings.ollama_base_url
        )

    if llm_settings.llm_provider == "vllm":
        from langchain_openai import OpenAIEmbeddings

        return OpenAIEmbeddings(
            model=llm_settings.embedding_model,
            openai_api_base=f"{llm_settings.vllm_base_url}/v1",
            openai_api_key="not-needed",
        )

    raise ValueError(f"Unknown LLM provider: {llm_settings.llm_provider!r}")
