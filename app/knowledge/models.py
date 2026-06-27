from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeDocument(BaseModel):
    id: str
    title: str
    source_type: str
    domain: str
    tags: list[str] = Field(default_factory=list)
    content: str
    source_path: str | None = None
    version: str = "v1"
    effective_date: str | None = None
    expires_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    title: str
    source_type: str
    domain: str
    tags: list[str] = Field(default_factory=list)
    text: str
    index: int
    version: str = "v1"
    effective_date: str | None = None
    expires_at: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    chunk: DocumentChunk
    relevance: float = Field(ge=0.0, le=1.0)


class RankedEvidence(BaseModel):
    chunk: DocumentChunk
    relevance: float = Field(ge=0.0, le=1.0)
    business_importance: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    policy_priority: int = Field(ge=0, le=100)
    freshness: int = Field(ge=0, le=100)
    duplicate_score: float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=1.0)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
