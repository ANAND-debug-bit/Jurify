"""Statute retriever (Module 12).

Vector-only for now. The KEYWORD half of the hybrid retriever described
in docs/architecture/09-sequence-diagrams.md §9.4 needs a full-text
index over the statute corpus, which doesn't exist yet — Module 5
modeled application data, not a statute-corpus table, and no module in
the implementation plan has added one. This retriever is built against
VectorStorePort specifically so a keyword half + reciprocal-rank fusion
can be added later without changing the Legal Research Agent's call site.
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.documents import Document

from app.rag.vectorstore import VectorStorePort

DEFAULT_TOP_K = 8


@dataclass(frozen=True)
class RetrievedChunk:
    document: Document
    score: float


class StatuteRetriever:
    def __init__(self, vector_store: VectorStorePort, *, top_k: int = DEFAULT_TOP_K) -> None:
        self._vector_store = vector_store
        self._top_k = top_k

    async def retrieve(self, query: str) -> list[RetrievedChunk]:
        results = await self._vector_store.asimilarity_search_with_score(query, k=self._top_k)
        return [RetrievedChunk(document=doc, score=score) for doc, score in results]
