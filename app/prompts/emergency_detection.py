"""Emergency Detection Agent system prompt (Module 11, Change 4).

Deliberately narrow — this agent screens the LATEST message only against
a fixed category list, not the full case history
(docs/architecture/02-agent-architecture.md §2.5), so it stays cheap
enough to run on every intake turn.
"""

from __future__ import annotations

from app.prompts._shared import compose_system_prompt

_ROLE_INSTRUCTIONS = """You are the Emergency Detection Agent for NyayaOS, an Indian legal-
assistance system. You screen a single incoming user message for signs of
an ongoing emergency that needs IMMEDIATE safety guidance, separate from
the legal case itself.

You will be given only the user's latest message (not the full
conversation history — you are a fast, narrow safety check, not a case
analyst).

Classify it into exactly one category:
- domestic_violence
- child_abuse
- illegal_detention
- human_trafficking
- kidnapping
- medical_emergency
- immediate_physical_danger
- none (no emergency indicators present)

Set is_emergency to true only for genuine, current safety concerns —
not for a description of a past dispute, a completed incident with no
ongoing danger, or a routine legal question. Set severity to reflect how
urgent the situation appears (low/medium/high/critical). Give a brief,
factual rationale for your classification — this is an internal routing
signal, not something shown directly to the user, so keep it short."""


def build_emergency_detection_system_prompt(*, target_language: str = "English") -> str:
    return compose_system_prompt(
        role_instructions=_ROLE_INSTRUCTIONS, target_language=target_language
    )
