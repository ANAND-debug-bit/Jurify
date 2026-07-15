from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.opposition import (
    CounterReport,
    Objection,
    ObjectionCategory,
    OppositionReport,
    OppositionRound,
    Rebuttal,
)


def test_opposition_round_content_parses_as_opposition_report() -> None:
    round_ = OppositionRound(
        round_number=1,
        role="opposition",
        content={
            "round_number": 1,
            "objections": [
                {"category": "evidence", "argument": "no receipt", "severity": "high"}
            ],
        },
    )
    assert isinstance(round_.content, OppositionReport)
    assert round_.content.objections[0].category == ObjectionCategory.EVIDENCE


def test_opposition_round_content_parses_as_counter_report() -> None:
    round_ = OppositionRound(
        round_number=1,
        role="counter",
        content={
            "round_number": 1,
            "rebuttals": [
                {"responds_to_category": "evidence", "argument": "receipt provided later"}
            ],
        },
    )
    assert isinstance(round_.content, CounterReport)
    assert round_.content.rebuttals[0].responds_to_category == ObjectionCategory.EVIDENCE


def test_counter_report_unresolved_objections_defaults_empty() -> None:
    report = CounterReport(
        round_number=2,
        rebuttals=[Rebuttal(responds_to_category=ObjectionCategory.TIMELINE, argument="x")],
    )
    assert report.unresolved_objections == []


def test_objection_severity_uses_urgency_level_enum() -> None:
    objection = Objection(category=ObjectionCategory.JURISDICTION, argument="wrong forum", severity="critical")
    assert objection.severity.value == "critical"


def test_objection_category_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError):
        Objection(category="unrelated_category", argument="x", severity="low")
