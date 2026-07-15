from __future__ import annotations

from app.prompts.evidence_analysis import build_evidence_analysis_system_prompt


def test_prompt_defines_the_three_quality_levels() -> None:
    prompt = " ".join(build_evidence_analysis_system_prompt().split())

    assert "weak:" in prompt
    assert "moderate:" in prompt
    assert "strong:" in prompt


def test_prompt_reserves_critical_for_essential_gaps() -> None:
    prompt = " ".join(build_evidence_analysis_system_prompt().split())

    assert "critical:" in prompt
    assert "Be conservative with critical" in prompt


def test_prompt_forbids_rewriting_submitted_evidence() -> None:
    prompt = " ".join(build_evidence_analysis_system_prompt().split())

    assert "do not rewrite or reinterpret them" in prompt


def test_prompt_includes_injection_defense_and_structured_output_preambles() -> None:
    prompt = build_evidence_analysis_system_prompt()

    assert "untrusted DATA" in prompt
    assert "single JSON object" in prompt
