from __future__ import annotations

from langchain_core.documents import Document

from app.rag.citation import EXCERPT_MAX_LENGTH, to_citation


def test_to_citation_maps_metadata_fields() -> None:
    document = Document(
        page_content="a consumer may file a complaint...",
        metadata={
            "act_name": "Consumer Protection Act, 2019",
            "section": "Section 35",
            "source_url": "https://www.indiacode.nic.in",
        },
    )

    citation = to_citation(document)

    assert citation.act_name == "Consumer Protection Act, 2019"
    assert citation.section == "Section 35"
    assert citation.source_url == "https://www.indiacode.nic.in"
    assert citation.excerpt == "a consumer may file a complaint..."


def test_to_citation_defaults_missing_metadata() -> None:
    document = Document(page_content="some text", metadata={})

    citation = to_citation(document)

    assert citation.act_name == "Unknown Act"
    assert citation.section == "Unknown Section"
    assert citation.source_url is None


def test_to_citation_truncates_long_excerpt() -> None:
    document = Document(
        page_content="x" * (EXCERPT_MAX_LENGTH + 100),
        metadata={"act_name": "Some Act", "section": "Section 1"},
    )

    citation = to_citation(document)

    assert citation.excerpt is not None
    assert len(citation.excerpt) == EXCERPT_MAX_LENGTH
