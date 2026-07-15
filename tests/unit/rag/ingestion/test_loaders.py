from __future__ import annotations

from app.rag.ingestion.loaders import SAMPLE_STATUTE_CORPUS


def test_every_entry_has_required_metadata() -> None:
    for document in SAMPLE_STATUTE_CORPUS:
        assert document.metadata.get("act_name")
        assert document.metadata.get("section")
        assert document.metadata.get("source_url")
        assert document.page_content.strip()


def test_every_entry_is_marked_unverified() -> None:
    # These are hand-paraphrased summaries, not verbatim statutory text
    # (see the module's "NOT AUTHORITATIVE" docstring) — verified must
    # stay False until a real ingestion pipeline sources exact text from
    # an authoritative source.
    assert all(document.metadata.get("verified") is False for document in SAMPLE_STATUTE_CORPUS)


def test_corpus_has_no_duplicate_sections() -> None:
    keys = [(d.metadata["act_name"], d.metadata["section"]) for d in SAMPLE_STATUTE_CORPUS]
    assert len(keys) == len(set(keys))
