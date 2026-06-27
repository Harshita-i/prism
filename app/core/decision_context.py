from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["Low", "Medium", "High", "Critical"]
Sentiment = Literal["Positive", "Neutral", "Negative", "Mixed"]
Urgency = Literal["Low", "Medium", "High", "Critical"]


class ContextSignal(BaseModel):
    label: str
    category: str = "Business Signal"
    severity: RiskLevel = "Medium"
    evidence: str = ""


class StructuredContext(BaseModel):
    primary_problem: str
    decision_type: str
    urgency: Urgency = "Medium"
    sentiment: Sentiment = "Neutral"
    entities: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    business_signals: list[ContextSignal] = Field(default_factory=list)
    required_context: list[str] = Field(default_factory=list)
    extracted_metrics: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    def retrieval_query(self) -> str:
        parts = [
            self.primary_problem,
            self.decision_type,
            self.urgency,
            self.sentiment,
            *self.entities,
            *self.stakeholders,
            *[signal.label for signal in self.business_signals],
        ]
        return " ".join(str(part) for part in parts if part)


class KnowledgeFinding(BaseModel):
    id: str
    title: str
    source_type: str
    domain: str
    excerpt: str
    score: float = 0.0
    constraints: list[str] = Field(default_factory=list)


class MemoryFinding(BaseModel):
    id: str
    entity_name: str
    problem: str
    recommendation: str
    outcome: str
    summary: str
    relevance: float = 0.0
    lesson: str = ""


class RiskFinding(BaseModel):
    label: str
    level: RiskLevel
    rationale: str
    evidence: str = ""


class RiskAnalysis(BaseModel):
    overall_level: RiskLevel = "Medium"
    score: int = Field(default=50, ge=0, le=100)
    business_risks: list[RiskFinding] = Field(default_factory=list)
    financial_risks: list[RiskFinding] = Field(default_factory=list)
    operational_risks: list[RiskFinding] = Field(default_factory=list)
    execution_risks: list[RiskFinding] = Field(default_factory=list)
    confidence_risks: list[RiskFinding] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)


class SimulationStrategy(BaseModel):
    title: str
    description: str
    probability: int = Field(ge=0, le=100)
    risk: RiskLevel
    expected_outcome: str
    reason: str
    owner: str
    evidence: list[str] = Field(default_factory=list)


class CouncilMessage(BaseModel):
    turn: int
    agent: str
    message_type: Literal["finding", "question", "challenge", "support", "clarification", "consensus"]
    message: str
    references: list[str] = Field(default_factory=list)
    confidence: int | None = None


class Consensus(BaseModel):
    status: Literal["Reached", "Needs More Information"] = "Reached"
    level: Literal["Weak", "Moderate", "Strong"] = "Moderate"
    preferred_strategy: str | None = None
    rationale: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    confidence: int = Field(default=70, ge=0, le=100)


class Recommendation(BaseModel):
    executive_summary: str
    recommended_action: SimulationStrategy
    alternatives: list[SimulationStrategy] = Field(default_factory=list)
    decision_matrix: list[dict[str, Any]] = Field(default_factory=list)
    confidence: int = Field(default=70, ge=0, le=100)
    reasoning: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class DecisionMetadata(BaseModel):
    decision_id: str
    title: str
    persona_id: str
    persona_label: str
    domain: str
    entity_name: str
    lifecycle_stage: str = "Draft"


class DecisionContext(BaseModel):
    metadata: DecisionMetadata
    persona: dict[str, Any] = Field(default_factory=dict)
    user_input: dict[str, Any]
    llm_metadata: dict[str, Any] = Field(default_factory=dict)
    structured_context: StructuredContext | None = None
    retrieved_knowledge: list[KnowledgeFinding] = Field(default_factory=list)
    historical_memory: list[MemoryFinding] = Field(default_factory=list)
    risk_analysis: RiskAnalysis | None = None
    simulations: list[SimulationStrategy] = Field(default_factory=list)
    council_messages: list[CouncilMessage] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    consensus: Consensus | None = None
    recommendation: Recommendation | None = None

    def add_message(
        self,
        *,
        agent: str,
        message_type: Literal["finding", "question", "challenge", "support", "clarification", "consensus"],
        message: str,
        references: list[str] | None = None,
        confidence: int | None = None,
    ) -> None:
        self.council_messages.append(
            CouncilMessage(
                turn=len(self.council_messages) + 1,
                agent=agent,
                message_type=message_type,
                message=message,
                references=references or [],
                confidence=confidence,
            )
        )
