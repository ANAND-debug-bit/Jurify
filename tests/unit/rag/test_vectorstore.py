from __future__ import annotations

import pytest
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import Settings
from app.rag.vectorstore import STATUTE_COLLECTION_NAME, get_vector_store
from tests.conftest import ollama_is_reachable


def test_get_vector_store_returns_in_memory_chroma_by_default(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    settings = Settings()

    store = get_vector_store(settings)

    assert isinstance(store, Chroma)
    assert store._collection.name == STATUTE_COLLECTION_NAME


def test_get_vector_store_accepts_custom_collection_name(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    settings = Settings()

    store = get_vector_store(settings, collection_name="a_test_collection")

    assert store._collection.name == "a_test_collection"


@pytest.mark.skipif(not ollama_is_reachable(), reason="no local Ollama server reachable")
async def test_live_add_and_search_returns_semantically_relevant_document(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_MODEL", "nomic-embed-text")
    settings = Settings()
    store = get_vector_store(settings, collection_name="vectorstore_test_live")

    await store.aadd_documents(
        [
            Document(
                page_content="A consumer may file a complaint about a defective product.",
                metadata={"act_name": "Consumer Protection Act, 2019", "section": "Section 35"},
            ),
            Document(
                page_content="An employee may claim unpaid wages before the labour authority.",
                metadata={"act_name": "Payment of Wages Act, 1936", "section": "Section 15"},
            ),
        ]
    )

    results = await store.asimilarity_search_with_score(
        "the shopkeeper sold me a broken television and refuses a refund", k=1
    )

    assert results[0][0].metadata["act_name"] == "Consumer Protection Act, 2019"
