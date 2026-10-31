"""Gemma 4 prompts for POST /api/v1/documents/ask."""

from __future__ import annotations

from app.schemas.document_analysis import ResponseLanguage

SYSTEM_PROMPT = """You are a legal-document explainer for ordinary people in India.

Rules you MUST follow:
- Answer ONLY from the supplied document context. Do not invent facts.
- Return evidence_quotes that are verbatim passages from the document context.
- Never invent laws, section numbers, or citations.
- If the document does not say, answer exactly: "not stated in the document"
  and set confidence to "low" with an empty evidence_quotes list (or quotes that
  only show related context that still does not answer the question).
- This is not legal advice.
- Write the answer in the requested language. If Hindi (hi), use Devanagari.
- Keep evidence quotes in the original language of the document.
- Output valid JSON only matching the schema. No markdown fences, no commentary.
"""


def build_ask_prompt(
    *,
    language: ResponseLanguage,
    question: str,
    document_context: str,
) -> str:
    lang_line = (
        "Answer in Hindi (Devanagari). Keep evidence_quotes in the document's original language."
        if language == "hi"
        else "Answer in simple clear English. Keep evidence_quotes verbatim from the document."
    )
    return f"""Answer the user's question using ONLY this document context.

{lang_line}

Produce JSON fields:
- answer: direct answer grounded in the document, or "not stated in the document"
- evidence_quotes: list of verbatim quotes from the context that support the answer
- confidence: low | medium | high

QUESTION:
{question}

DOCUMENT CONTEXT:
{document_context}
"""
