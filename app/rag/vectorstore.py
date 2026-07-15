"""Vector store adapter behind a narrow port (Module 12).

docs/architecture/06-folder-structure.md: "Chroma/FAISS adapter behind a
VectorStorePort" — VectorStorePort is intentionally narrow (only the two
operations the retriever/ingestion actually call), so swapping Chroma
for Qdrant later (docs/architecture/11-scalability-roadmap.md §11.3)
only requires a new adapter satisfying this same Protocol, never
touching the retriever.
"""

from __future__ import annotations

from typing import Protocol

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import Settings
from app.rag.embeddings import get_embeddings

STATUTE_COLLECTION_NAME = "nyayaos_statutes"


class VectorStorePort(Protocol):
    async def aadd_documents(self, documents: list[Document]) -> list[str]: ...

    async def asimilarity_search_with_score(
        self, query: str, k: int = 8
    ) -> list[tuple[Document, float]]: ...


def get_vector_store(
    settings: Settings,
    *,
    collection_name: str = STATUTE_COLLECTION_NAME,
    persist_directory: str | None = None,
) -> Chroma:
    """persist_directory=None (the default) gives an in-memory-only
    Chroma instance — used by tests so nothing is written to disk;
    production wiring passes a real path once it exists (Module 25+)."""
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(settings),
        persist_directory=persist_directory,
    )
