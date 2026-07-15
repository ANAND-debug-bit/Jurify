"""Complaint Generation Agent output contract.
docs/architecture/08-pydantic-schemas.md §8.7."""

from __future__ import annotations

from enum import StrEnum

from app.schemas._common import NyayaBaseModel


class DocumentType(StrEnum):
    POLICE_COMPLAINT = "police_complaint"
    LEGAL_NOTICE = "legal_notice"
    CONSUMER_COMPLAINT = "consumer_complaint"
    RTI_APPLICATION = "rti_application"
    LABOUR_COMPLAINT = "labour_complaint"
    CYBER_COMPLAINT = "cyber_complaint"


class GeneratedDocument(NyayaBaseModel):
    document_type: DocumentType
    title: str
    content: str  # fully formatted legal draft, ready to file
    recipient: str | None = None
    filing_authority: str | None = None
