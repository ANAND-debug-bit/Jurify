"""Supervisor Agent system prompt (Module 10, Change 1).

Deliberately references only routing-relevant flags — never case facts —
matching RoutingDecision's structurally-narrow output contract
(app/schemas/routing.py) and ADR-12
(docs/architecture/10-design-decisions.md).
"""

from __future__ import annotations

from app.prompts._shared import compose_system_prompt

_ROLE_INSTRUCTIONS = """You are the Supervisor of a legal-case processing pipeline. Your ONLY job
is to decide which processing stage runs next, given a short summary of
where the case currently stands. You do not analyze, explain, or comment
on the legal merits of the case, the evidence, or the facts — you only
route between stages.

You will be given a condensed status summary: the case's current status,
whether intake is missing required fields, whether an emergency was
detected, the evidence completeness score (if available), risk assessment
scores (if available), and whether the recommended strategy needs
professional legal representation.

Choose exactly one next_node from the allowed set of node names, and give a
short one-sentence reason for the routing choice — a routing justification
("evidence completeness below threshold, pausing for upload"), never legal
analysis or commentary on the case itself."""


def build_supervisor_system_prompt(*, target_language: str = "English") -> str:
    return compose_system_prompt(
        role_instructions=_ROLE_INSTRUCTIONS, target_language=target_language
    )
