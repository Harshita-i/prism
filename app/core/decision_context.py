from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["Low", "Medium", "High", "Critical"]
Sentiment = Literal["Positive", "Neutral", "Negative", "Mixed"]
Urgency = Literal["Low", "Medium", "High", "Critical"]
CouncilCategory = Literal[
    "finding",
    "question",
    "challenge",
    "support",
    "clarification",
    "disagreement",
    "evidence",
    "revision",
    "consensus",
]


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


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


class KnowledgePacket(BaseModel):
    id: str
    title: str
    finding: str
    importance: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    policy_priority: int = Field(default=50, ge=0, le=100)
    freshness: int = Field(default=70, ge=0, le=100)
    duplicate_score: float = Field(default=0.0, ge=0.0, le=1.0)
    weighted_score: float = Field(default=0.0, ge=0.0, le=1.0)
    supports: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    source: str
    source_type: str
    domain: str
    document_id: str
    chunk_ids: list[str] = Field(default_factory=list)
    evidence_excerpt: str = ""


class MemoryFinding(BaseModel):
    id: str
    entity_name: str
    problem: str
    recommendation: str
    outcome: str
    summary: str
    relevance: float = 0.0
    lesson: str = ""


class MemoryPacket(BaseModel):
    id: str
    title: str
    similarity: float = Field(ge=0.0, le=1.0)
    outcome: str
    outcome_quality: int = Field(ge=0, le=100)
    winning_strategy: str
    confidence: float = Field(ge=0.0, le=1.0)
    recency: int = Field(ge=0, le=100)
    business_importance: int = Field(ge=0, le=100)
    evidence_strength: int = Field(ge=0, le=100)
    weighted_score: float = Field(ge=0.0, le=1.0)
    reason: str
    source_decision: str
    persona_id: str
    decision_type: str
    business_signals: list[str] = Field(default_factory=list)
    knowledge_references: list[str] = Field(default_factory=list)
    simulation_references: list[str] = Field(default_factory=list)
    explainability: str = ""


class MemoryInsight(BaseModel):
    label: str
    count: int
    evidence: list[str] = Field(default_factory=list)
    summary: str


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


class WhatIfProjection(BaseModel):
    condition: str
    projected_change: str
    success_delta: int = Field(default=0, ge=-100, le=100)
    risk_delta: str = "No material change"
    mitigation: str = ""


class ScenarioPacket(BaseModel):
    id: str
    title: str
    strategy_type: str
    description: str
    success_probability: float = Field(ge=0.0, le=1.0)
    business_risk: RiskLevel
    operational_risk: RiskLevel = "Medium"
    financial_cost: Literal["Low", "Medium", "High"] = "Medium"
    implementation_complexity: Literal["Low", "Medium", "High"] = "Medium"
    expected_outcome: str
    time_to_impact: str
    confidence: float = Field(ge=0.0, le=1.0)
    weighted_score: float = Field(ge=0.0, le=1.0)
    knowledge_support: float = Field(default=0.0, ge=0.0, le=1.0)
    historical_support: float = Field(default=0.0, ge=0.0, le=1.0)
    planner_priority: float = Field(default=0.5, ge=0.0, le=1.0)
    reason: str
    owner: str
    evidence: list[str] = Field(default_factory=list)
    knowledge_packet_ids: list[str] = Field(default_factory=list)
    memory_packet_ids: list[str] = Field(default_factory=list)
    what_if: list[WhatIfProjection] = Field(default_factory=list)
    rejection_reason: str | None = None


class ScenarioMetrics(BaseModel):
    generated: int = 0
    ranked: int = 0
    rejected: int = 0
    average_confidence: float = 0.0
    average_success: float = 0.0


class CouncilMessage(BaseModel):
    turn: int
    agent: str
    message_type: CouncilCategory
    message: str
    references: list[str] = Field(default_factory=list)
    confidence: int | None = None
    timestamp: str = Field(default_factory=utc_timestamp)
    reply_to: int | None = None
    supports: list[str] = Field(default_factory=list)
    challenges: list[str] = Field(default_factory=list)
    confidence_before: int | None = None
    confidence_after: int | None = None
    evidence_references: list[str] = Field(default_factory=list)


class Consensus(BaseModel):
    status: Literal["Reached", "Needs More Information"] = "Reached"
    level: Literal["Weak", "Moderate", "Strong"] = "Moderate"
    preferred_strategy: str | None = None
    rationale: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    confidence: int = Field(default=70, ge=0, le=100)
    agreement_score: int = Field(default=70, ge=0, le=100)
    strength: Literal["Weak", "Moderate", "Strong"] = "Moderate"
    minority_opinions: list[str] = Field(default_factory=list)
    rejected_arguments: list[str] = Field(default_factory=list)
    explanation: str = ""


class Recommendation(BaseModel):
    executive_summary: str
    recommended_action: SimulationStrategy
    alternatives: list[SimulationStrategy] = Field(default_factory=list)
    decision_matrix: list[dict[str, Any]] = Field(default_factory=list)
    confidence: int = Field(default=70, ge=0, le=100)
    reasoning: list[str] = Field(default_factory=list)
    evidence: list[dict[str, Any]] = Field(default_factory=list)


class DecisionLifecycleEvent(BaseModel):
    stage: str
    status: str = "completed"
    timestamp: str = Field(default_factory=utc_timestamp)
    actor: str = "Prism"
    notes: str = ""


class ApprovalRecord(BaseModel):
    status: Literal["pending", "approve", "reject", "request_changes", "request_more_information", "modify"] = "pending"
    reviewer: str | None = None
    notes: str = ""
    modified_action: str | None = None
    timestamp: str = Field(default_factory=utc_timestamp)


class OutcomeMetrics(BaseModel):
    outcome: Literal["Pending", "Succeeded", "Failed", "Partially Successful", "Cancelled", "Unknown"] = "Pending"
    success_score: int | None = Field(default=None, ge=0, le=100)
    business_impact: str = ""
    notes: str = ""
    recorded_at: str | None = None


class DecisionVersion(BaseModel):
    version: int
    timestamp: str = Field(default_factory=utc_timestamp)
    actor: str = "Prism"
    change_type: str = "created"
    change_log: list[str] = Field(default_factory=list)
    snapshot: dict[str, Any] = Field(default_factory=dict)


class EnterpriseDecisionCard(BaseModel):
    decision_id: str
    decision_title: str
    executive_summary: str
    recommendation: dict[str, Any]
    alternative_strategies: list[dict[str, Any]] = Field(default_factory=list)
    decision_matrix: list[dict[str, Any]] = Field(default_factory=list)
    supporting_evidence: list[dict[str, Any]] = Field(default_factory=list)
    confidence: int = Field(ge=0, le=100)
    consensus_strength: str
    business_impact: str
    risk: str
    estimated_cost: str
    time_to_impact: str
    approval_status: str = "pending"
    version: int = 1
    timestamp: str = Field(default_factory=utc_timestamp)
    planner_reasoning: list[str] = Field(default_factory=list)
    council_summary: str = ""
    knowledge_references: list[str] = Field(default_factory=list)
    memory_references: list[str] = Field(default_factory=list)
    scenario_references: list[str] = Field(default_factory=list)
    why_selected: list[str] = Field(default_factory=list)
    why_alternatives_rejected: list[str] = Field(default_factory=list)
    traceability: dict[str, Any] = Field(default_factory=dict)


class DecisionAnalytics(BaseModel):
    decision_success_rate: float = 0.0
    average_confidence: float = 0.0
    top_strategies: list[dict[str, Any]] = Field(default_factory=list)
    most_common_risks: list[dict[str, Any]] = Field(default_factory=list)
    most_successful_personas: list[dict[str, Any]] = Field(default_factory=list)
    decision_volume: int = 0


class ExecutionCondition(BaseModel):
    condition: str
    execute: str
    reason: str = ""


class ExecutionNode(BaseModel):
    id: str
    agent: str
    required: bool = True
    depends_on: list[str] = Field(default_factory=list)
    retry_of: str | None = None
    reason: str = ""


class ExecutionPlan(BaseModel):
    steps: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)
    conditional: list[ExecutionCondition] = Field(default_factory=list)
    skip: list[str] = Field(default_factory=list)
    graph: list[ExecutionNode] = Field(default_factory=list)
    reasoning: list[str] = Field(default_factory=list)


class PlannerTimelineEvent(BaseModel):
    step: str
    status: Literal["planned", "executed", "skipped", "retried", "failed"]
    reason: str
    confidence: float | None = None


class ExecutionMetrics(BaseModel):
    planned_steps: int = 0
    executed_steps: int = 0
    skipped_steps: int = 0
    retries: int = 0
    average_confidence: float = 0.0


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
    knowledge_packets: list[KnowledgePacket] = Field(default_factory=list)
    historical_memory: list[MemoryFinding] = Field(default_factory=list)
    memory_packets: list[MemoryPacket] = Field(default_factory=list)
    winning_patterns: list[MemoryInsight] = Field(default_factory=list)
    failure_patterns: list[MemoryInsight] = Field(default_factory=list)
    historical_evidence: list[dict[str, Any]] = Field(default_factory=list)
    memory_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    risk_analysis: RiskAnalysis | None = None
    simulations: list[SimulationStrategy] = Field(default_factory=list)
    scenario_packets: list[ScenarioPacket] = Field(default_factory=list)
    scenario_ranking: list[dict[str, Any]] = Field(default_factory=list)
    scenario_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    scenario_metrics: ScenarioMetrics = Field(default_factory=ScenarioMetrics)
    rejected_scenarios: list[ScenarioPacket] = Field(default_factory=list)
    winning_scenario: ScenarioPacket | None = None
    council_messages: list[CouncilMessage] = Field(default_factory=list)
    council_timeline: list[CouncilMessage] = Field(default_factory=list)
    consensus_score: int = Field(default=0, ge=0, le=100)
    consensus_strength: Literal["Weak", "Moderate", "Strong"] = "Weak"
    rejected_arguments: list[str] = Field(default_factory=list)
    supporting_evidence: list[str] = Field(default_factory=list)
    minority_opinions: list[str] = Field(default_factory=list)
    planner_actions: list[str] = Field(default_factory=list)
    consensus_explanation: str = ""
    agent_confidence: dict[str, int] = Field(default_factory=dict)
    open_questions: list[str] = Field(default_factory=list)
    consensus: Consensus | None = None
    recommendation: Recommendation | None = None
    decision_card: EnterpriseDecisionCard | None = None
    decision_lifecycle: list[DecisionLifecycleEvent] = Field(default_factory=list)
    decision_versions: list[DecisionVersion] = Field(default_factory=list)
    approval_status: str = "pending"
    approval_log: list[ApprovalRecord] = Field(default_factory=list)
    outcome_metrics: OutcomeMetrics = Field(default_factory=OutcomeMetrics)
    decision_analytics: DecisionAnalytics = Field(default_factory=DecisionAnalytics)
    execution_plan: ExecutionPlan | None = None
    executed_steps: list[str] = Field(default_factory=list)
    skipped_steps: list[str] = Field(default_factory=list)
    planner_reasoning: list[str] = Field(default_factory=list)
    planner_timeline: list[PlannerTimelineEvent] = Field(default_factory=list)
    confidence_timeline: list[dict[str, Any]] = Field(default_factory=list)
    execution_metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)

    def add_message(
        self,
        *,
        agent: str,
        message_type: CouncilCategory,
        message: str,
        references: list[str] | None = None,
        confidence: int | None = None,
        reply_to: int | None = None,
        supports: list[str] | None = None,
        challenges: list[str] | None = None,
        confidence_before: int | None = None,
        confidence_after: int | None = None,
        evidence_references: list[str] | None = None,
    ) -> None:
        council_message = CouncilMessage(
            turn=len(self.council_messages) + 1,
            agent=agent,
            message_type=message_type,
            message=message,
            references=references or [],
            confidence=confidence,
            reply_to=reply_to,
            supports=supports or [],
            challenges=challenges or [],
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            evidence_references=evidence_references or references or [],
        )
        self.council_messages.append(council_message)
        self.council_timeline.append(council_message)
        if confidence_after is not None:
            self.agent_confidence[agent] = confidence_after
        elif confidence is not None:
            self.agent_confidence[agent] = confidence
