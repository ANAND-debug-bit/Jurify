from __future__ import annotations

from app.prompts.case_intake import build_case_intake_system_prompt


def test_case_intake_prompt_instructs_structured_extraction() -> None:
    prompt = build_case_intake_system_prompt()

    assert "structured case profile" in prompt.lower() or "case profile" in prompt.lower()


def test_case_intake_prompt_is_a_valid_composed_prompt() -> None:
    prompt = build_case_intake_system_prompt(target_language="Bengali")

    assert "untrusted DATA" in prompt
    assert "Target language for free-text values: Bengali." in prompt
