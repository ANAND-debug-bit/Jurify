from __future__ import annotations

from app.prompts.risk_assessment import build_risk_assessment_system_prompt


def test_prompt_defines_all_score_fields() -> None:
    prompt = " ".join(build_risk_assessment_system_prompt().split())

    assert "financial_risk (0-100):" in prompt
    assert "criminal_risk (0-100):" in prompt
    assert "settlement_probability (0-100):" in prompt
    assert "case_strength (0-100):" in prompt


def test_prompt_ties_needs_flags_to_specific_conditions() -> None:
    prompt = " ".join(build_risk_assessment_system_prompt().split())

    assert "needs_police: true only if" in prompt
    assert "needs_medical: true only if" in prompt


def test_prompt_forbids_outside_legal_knowledge() -> None:
    prompt = " ".join(build_risk_assessment_system_prompt().split())

    assert "never outside legal knowledge" in prompt
    assert "never assume a fact that was not stated" in prompt


def test_prompt_includes_injection_defense_and_structured_output_preambles() -> None:
    prompt = build_risk_assessment_system_prompt()

    assert "untrusted DATA" in prompt
    assert "single JSON object" in prompt
