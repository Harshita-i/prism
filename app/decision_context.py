from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from app.models import AgentResult, utc_now


@dataclass
class CouncilMessage:
    turn: int
    agent: str
    role: str
    message_type: str
    message: str
    references: list[str] = field(default_factory=list)
    confidence: int | None = None
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CouncilConsensus:
    recommended_action: str
    consensus_level: str
    confidence: int
    rationale: list[str] = field(default_factory=list)
    conflicts_resolved: list[str] = field(default_factory=list)
    rejected_alternatives: list[dict[str, Any]] = field(default_factory=list)
    open_questions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecisionContext:
    decision_id: str
    title: str
    persona_id: str
    domain: str
    entity_name: str
    raw_input: dict[str, Any]
    agent_outputs: dict[str, AgentResult] = field(default_factory=dict)
    discussion: list[CouncilMessage] = field(default_factory=list)
    consensus: CouncilConsensus | None = None
    lifecycle_stage: str = "Draft"
    questions: list[str] = field(default_factory=list)

    def add_agent_output(self, key: str, result: AgentResult) -> None:
        self.agent_outputs[key] = result

    def add_message(
        self,
        *,
        agent: str,
        role: str,
        message_type: str,
        message: str,
        references: list[str] | None = None,
        confidence: int | None = None,
    ) -> CouncilMessage:
        item = CouncilMessage(
            turn=len(self.discussion) + 1,
            agent=agent,
            role=role,
            message_type=message_type,
            message=message,
            references=references or [],
            confidence=confidence,
        )
        self.discussion.append(item)
        return item

    def set_consensus(self, consensus: CouncilConsensus) -> None:
        self.consensus = consensus

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "title": self.title,
            "persona_id": self.persona_id,
            "domain": self.domain,
            "entity_name": self.entity_name,
            "lifecycle_stage": self.lifecycle_stage,
            "agent_outputs": {key: value.to_dict() for key, value in self.agent_outputs.items()},
            "discussion": [item.to_dict() for item in self.discussion],
            "consensus": self.consensus.to_dict() if self.consensus else None,
            "questions": self.questions,
        }

