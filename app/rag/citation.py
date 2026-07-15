"""Citation formatting from retrieved chunks (Module 12).

Converts a raw retrieved langchain Document into the structured
LegalCitation schema (app.schemas.legal_research) — metadata keys are
fixed by the ingestion pipeline (app.rag.ingestion.loaders), not guessed
here.
"""

from __future__ import annotations

from langchain_core.documents import Document

from app.schemas.legal_research import LegalCitation

EXCERPT_MAX_LENGTH = 500


def to_citation(document: Document) -> LegalCitation:
    metadata = document.metadata
    excerpt = document.page_content[:EXCERPT_MAX_LENGTH]
    return LegalCitation(
        act_name=metadata.get("act_name", "Unknown Act"),
        section=metadata.get("section", "Unknown Section"),
        source_url=metadata.get("source_url"),
        excerpt=excerpt,
    )
