from __future__ import annotations

from langchain_core.documents import Document

from app.rag.retriever import DEFAULT_TOP_K, StatuteRetriever


class _FakeVectorStore:
    def __init__(self, results: list[tuple[Document, float]]) -> None:
        self._results = results
        self.last_query: str | None = None
        self.last_k: int | None = None

    async def aadd_documents(self, documents: list[Document]) -> list[str]:
        raise NotImplementedError

    async def asimilarity_search_with_score(
        self, query: str, k: int = 8
    ) -> list[tuple[Document, float]]:
        self.last_query = query
        self.last_k = k
        return self._results[:k]


async def test_retrieve_wraps_results_as_retrieved_chunks() -> None:
    document = Document(page_content="x", metadata={"act_name": "Test Act"})
    store = _FakeVectorStore([(document, 0.9)])
    retriever = StatuteRetriever(store)

    chunks = await retriever.retrieve("some query")

    assert len(chunks) == 1
    assert chunks[0].document is document
    assert chunks[0].score == 0.9


async def test_retrieve_passes_query_and_default_top_k_through() -> None:
    store = _FakeVectorStore([])
    retriever = StatuteRetriever(store)

    await retriever.retrieve("some query")

    assert store.last_query == "some query"
    assert store.last_k == DEFAULT_TOP_K


async def test_retrieve_respects_custom_top_k() -> None:
    store = _FakeVectorStore([])
    retriever = StatuteRetriever(store, top_k=3)

    await retriever.retrieve("some query")

    assert store.last_k == 3


async def test_retrieve_returns_empty_list_when_nothing_found() -> None:
    store = _FakeVectorStore([])
    retriever = StatuteRetriever(store)

    chunks = await retriever.retrieve("no matches")

    assert chunks == []
