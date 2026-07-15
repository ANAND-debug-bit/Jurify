from __future__ import annotations

from app.prompts.emergency_detection import build_emergency_detection_system_prompt


def test_prompt_lists_all_seven_categories() -> None:
    prompt = build_emergency_detection_system_prompt()

    for category in [
        "domestic_violence",
        "child_abuse",
        "illegal_detention",
        "human_trafficking",
        "kidnapping",
        "medical_emergency",
        "immediate_physical_danger",
    ]:
        assert category in prompt


def test_prompt_instructs_latest_message_only() -> None:
    prompt = build_emergency_detection_system_prompt().lower()

    assert "latest message" in prompt or "latest user message" in prompt
