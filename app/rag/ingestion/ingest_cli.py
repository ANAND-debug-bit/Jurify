"""Statute corpus ingestion CLI (Module 12).

Usage: python -m app.rag.ingestion.ingest_cli

Ingests the current corpus (app.rag.ingestion.loaders.SAMPLE_STATUTE_CORPUS
— see that module's docstring for why it's a sample, not a production
corpus) into the configured vector store.
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.rag.ingestion.chunking import chunk_documents
from app.rag.ingestion.loaders import SAMPLE_STATUTE_CORPUS
from app.rag.vectorstore import get_vector_store

logger = get_logger(__name__)


async def ingest() -> int:
    settings = get_settings()
    configure_logging(settings)

    chunks = chunk_documents(SAMPLE_STATUTE_CORPUS)
    vector_store = get_vector_store(settings)
    ids = await vector_store.aadd_documents(chunks)

    logger.info("ingestion_complete", chunk_count=len(ids))
    return len(ids)


if __name__ == "__main__":
    asyncio.run(ingest())
