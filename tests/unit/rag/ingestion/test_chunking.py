from __future__ import annotations

from langchain_core.documents import Document

from app.rag.ingestion.chunking import chunk_documents
from app.rag.ingestion.loaders import SAMPLE_STATUTE_CORPUS


def test_short_documents_stay_as_one_chunk() -> None:
    # Every sample corpus entry is well under the default chunk size.
    chunks = chunk_documents(SAMPLE_STATUTE_CORPUS)

    assert len(chunks) == len(SAMPLE_STATUTE_CORPUS)


def test_metadata_is_preserved_through_chunking() -> None:
    chunks = chunk_documents(SAMPLE_STATUTE_CORPUS)

    for chunk in chunks:
        assert "act_name" in chunk.metadata
        assert "section" in chunk.metadata


def test_long_document_is_split_into_multiple_chunks() -> None:
    long_document = Document(
        page_content=" ".join(f"sentence number {i}." for i in range(200)),
        metadata={"act_name": "Test Act", "section": "Section 1"},
    )

    chunks = chunk_documents([long_document], chunk_size=100, chunk_overlap=20)

    assert len(chunks) > 1
    assert all(chunk.metadata["act_name"] == "Test Act" for chunk in chunks)
