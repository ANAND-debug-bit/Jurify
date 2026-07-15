from __future__ import annotations

from app.prompts.verification import build_verification_system_prompt


def test_prompt_defines_all_three_verification_statuses() -> None:
    prompt = " ".join(build_verification_system_prompt().split())

    assert "VERIFIED:" in prompt
    assert "REJECTED:" in prompt
    assert "UNVERIFIED:" in prompt


def test_prompt_forbids_verifying_from_memory() -> None:
    prompt = " ".join(build_verification_system_prompt().split())

    assert "Never mark a citation VERIFIED from memory" in prompt


def test_prompt_treats_no_evidence_as_grounds_for_rejection() -> None:
    prompt = " ".join(build_verification_system_prompt().lower().split())

    assert "treat \"nothing was found\" as grounds to reject" in prompt


def test_prompt_includes_injection_defense_and_structured_output_preambles() -> None:
    prompt = build_verification_system_prompt()

    assert "untrusted DATA" in prompt
    assert "single JSON object" in prompt
