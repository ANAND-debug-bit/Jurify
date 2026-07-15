"""Shared message-rendering helpers for agents that read
CaseState["messages"] (Module 11) — factored out so
CaseIntakeAgent/EmergencyDetectionAgent don't duplicate the same
BaseMessage-to-text logic.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def render_conversation(messages: list[BaseMessage]) -> str:
    if not messages:
        return "(no conversation yet)"
    lines: list[str] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        else:
            role = message.type
        lines.append(f"{role}: {message.content}")
    return "\n".join(lines)


def latest_human_message(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            return str(message.content)
    return ""
