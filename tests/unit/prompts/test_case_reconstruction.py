from __future__ import annotations

from app.prompts.case_reconstruction import build_case_reconstruction_system_prompt


def test_prompt_instructs_chronological_timeline() -> None:
    prompt = build_case_reconstruction_system_prompt().lower()

    assert "chronological" in prompt
    assert "sequence_order" in prompt


def test_prompt_forbids_inventing_facts() -> None:
    prompt = build_case_reconstruction_system_prompt().lower()

    assert "do not invent" in prompt
