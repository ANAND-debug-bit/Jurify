"""Gemma LLM client factory (Module 10).

get_chat_model() is the single place LLM_PROVIDER (ollama | vllm) is
branched on — agents depend on this function's return type
(BaseChatModel), never on ChatOllama/ChatOpenAI directly, so swapping
providers or pointing at a fine-tuned model later touches one file
(docs/architecture/10-design-decisions.md ADR-2, ADR-4).
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.core.config import Settings


def get_chat_model(settings: Settings, *, temperature: float = 0.0) -> BaseChatModel:
    llm_settings = settings.llm

    if llm_settings.llm_provider == "ollama":
        return ChatOllama(
            model=llm_settings.gemma_model_name,
            base_url=llm_settings.ollama_base_url,
            temperature=temperature,
        )

    if llm_settings.llm_provider == "vllm":
        # vLLM exposes an OpenAI-compatible endpoint — ChatOpenAI pointed
        # at it works without a real OpenAI account; api_key is required
        # by the client but ignored by vLLM's own server.
        return ChatOpenAI(
            model=llm_settings.gemma_model_name,
            base_url=f"{llm_settings.vllm_base_url}/v1",
            api_key="not-needed",
            temperature=temperature,
        )

    raise ValueError(f"Unknown LLM provider: {llm_settings.llm_provider!r}")
