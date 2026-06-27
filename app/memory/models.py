from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ArchivedDecision(BaseModel):
    id: str
    title: str
    persona_id: str
    persona_label: str = ""
    domain: str
    decision_type: str
    entity_name: str
    primary_problem: str = ""
    urgency: str = "Medium"
    sentiment: str = "Neutral"
    business_signals: list[str] = Field(default_factory=list)
    recommendation: str = ""
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    decision_matrix: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: int = 0
    outcome: str = "Pending"
    outcome_notes: str = ""
    knowledge_references: list[str] = Field(default_factory=list)
    simulation_results: list[dict[str, Any]] = Field(default_factory=list)
    planner_reasoning: list[str] = Field(default_factory=list)
    council_consensus: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def searchable_text(self) -> str:
        return " ".join(
            [
                self.persona_id,
                self.domain,
                self.decision_type,
                self.primary_problem,
                self.urgency,
                self.sentiment,
                self.entity_name,
                self.recommendation,
                self.outcome,
                *self.business_signals,
            ]
        )


class RetrievedMemory(BaseModel):
    decision: ArchivedDecision
    similarity: float = Field(ge=0.0, le=1.0)


class RankedMemory(BaseModel):
    decision: ArchivedDecision
    similarity: float = Field(ge=0.0, le=1.0)
    outcome_quality: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    recency: int = Field(ge=0, le=100)
    business_importance: int = Field(ge=0, le=100)
    evidence_strength: int = Field(ge=0, le=100)
    weighted_score: float = Field(ge=0.0, le=1.0)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
