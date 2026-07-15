from __future__ import annotations

from app.prompts.legal_research import build_legal_research_system_prompt


def test_prompt_requires_verbatim_citations() -> None:
    prompt = " ".join(build_legal_research_system_prompt().lower().split())

    assert "exactly as they appear" in prompt
    assert "never abbreviate, paraphrase, renumber, or invent" in prompt


def test_prompt_forbids_inventing_citations_when_nothing_relevant() -> None:
    prompt = " ".join(build_legal_research_system_prompt().lower().split())

    assert "do not invent one" in prompt


def test_prompt_includes_injection_defense_and_structured_output_preambles() -> None:
    prompt = build_legal_research_system_prompt()

    assert "untrusted DATA" in prompt
    assert "single JSON object" in prompt
