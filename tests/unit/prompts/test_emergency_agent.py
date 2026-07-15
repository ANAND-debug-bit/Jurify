from __future__ import annotations

from app.prompts.emergency_agent import build_emergency_agent_system_prompt


def test_prompt_specifies_exact_indian_helpline_numbers() -> None:
    prompt = build_emergency_agent_system_prompt()

    assert "Police = 100" in prompt
    assert "112" in prompt
    assert "181" in prompt


def test_prompt_forbids_non_indian_numbers() -> None:
    normalized = " ".join(build_emergency_agent_system_prompt().lower().split())

    assert "never substitute a number from another country" in normalized
