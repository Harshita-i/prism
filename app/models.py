from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


LIFECYCLE_STAGES = [
    "Draft",
    "Evidence Collection",
    "Decision Council Discussion",
    "Simulation",
    "Recommendation",
    "Human Review",
    "Approved",
    "Executed",
    "Outcome Recorded",
    "Learning",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AgentResult:
    name: str
    role: str
    status: str
    summary: str
    confidence: int
    findings: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ActionOption:
    action: str
    success_probability: int
    revenue_impact: str
    risk_level: str
    reasoning: str
    required_owner: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionCard:
    decision_id: str
    title: str
    customer_name: str
    domain: str
    lifecycle_stage: str
    executive_summary: str
    recommendation: dict[str, Any]
    confidence: int
    alternatives: list[dict[str, Any]]
    council_outputs: dict[str, Any]
    evidence: list[dict[str, Any]]
    risks: list[str]
    missing_information: list[str]
    business_reasoning: list[str]
    human_review: dict[str, Any]
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
