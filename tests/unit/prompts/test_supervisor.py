from __future__ import annotations

from app.prompts.supervisor import build_supervisor_system_prompt


def test_supervisor_prompt_instructs_routing_only() -> None:
    normalized = build_supervisor_system_prompt().lower().replace("\n", " ")

    assert "you only route between stages" in normalized


def test_supervisor_prompt_never_mentions_legal_analysis_as_its_job() -> None:
    prompt = build_supervisor_system_prompt()

    assert "do not analyze" in prompt.lower()


def test_supervisor_prompt_is_a_valid_composed_system_prompt() -> None:
    prompt = build_supervisor_system_prompt(target_language="Tamil")

    assert "untrusted DATA" in prompt
    assert "Target language for free-text values: Tamil." in prompt
