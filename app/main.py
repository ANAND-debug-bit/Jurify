"""Jurify FastAPI entrypoint — Legal Document Intelligence (Gemma 4 demo).

Analyses are kept in an in-memory store (dict) for the demo. No Postgres is
needed for the /api/v1/documents/* path.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.documents import router as documents_router
from app.core.config import get_settings
from app.core.middleware import RequestLoggingMiddleware
from app.schemas.legal_document_intel import HealthResponse

settings = get_settings()

app = FastAPI(
    title="Jurify — Legal Document Intelligence",
    description=(
        "Explain legal documents with Gemma 4 (plain English/Hindi, key clauses, "
        "risk flags). Demo analyses are stored in-memory only (no Postgres)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(documents_router)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", model=settings.llm.gemma_model_name)
