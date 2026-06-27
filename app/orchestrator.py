from __future__ import annotations

from typing import Any

from app.agents import ContextAgent, KnowledgeAgent, MemoryAgent, RiskAgent, SimulationAgent
from app.core.context_extractor import LLMContextExtractor
from app.core.decision_context import DecisionContext, DecisionMetadata, Recommendation, SimulationStrategy
from app.core.executive_council import ExecutiveCouncil
from app.core.planner import Planner
from app.llm.service import LLMService
from app.models import utc_now
from app.personas import get_persona


class DecisionOrchestrator:
    def __init__(self, storage: Any, llm_service: LLMService | None = None):
        self.storage = storage
        self.llm_service = llm_service or LLMService.from_env()
        self.planner = Planner(
            agents=[
                ContextAgent(LLMContextExtractor(self.llm_service)),
                KnowledgeAgent(storage),
                MemoryAgent(storage),
                RiskAgent(),
                SimulationAgent(),
            ],
            council=ExecutiveCouncil(self.llm_service),
        )

    def run_decision(self, decision_id: str) -> dict[str, Any]:
        decision = self.storage.get_decision(decision_id)
        if decision is None:
            raise KeyError(f"Decision not found: {decision_id}")

        persona = get_persona(decision["input"].get("persona_id"))
        context = self._create_context(decision, persona)

        self.storage.update_decision(decision_id, lifecycle_stage="Evidence Collection")
        context = self.planner.run(context)

        card = self._decision_card(decision, context)
        return self.storage.update_decision(
            decision_id,
            lifecycle_stage="Human Review",
            card=card,
            review=card["human_review"],
        )

    def record_review(
        self,
        decision_id: str,
        action: str,
        reviewer: str,
        notes: str = "",
        modified_action: str | None = None,
    ) -> dict[str, Any]:
        decision = self.storage.get_decision(decision_id)
        if decision is None:
            raise KeyError(f"Decision not found: {decision_id}")
        if decision["card"] is None:
            raise ValueError("Run the decision council before human review.")

        normalized = action.strip().lower()
        if normalized not in {"approve", "reject", "modify", "request_more_information"}:
            raise ValueError("Review action must be approve, reject, modify, or request_more_information.")

        stage = "Approved" if normalized == "approve" else "Human Review"
        review = {
            "status": normalized,
            "reviewer": reviewer,
            "notes": notes,
            "modified_action": modified_action,
            "reviewed_at": utc_now(),
        }
        card = decision["card"]
        card["human_review"] = review
        return self.storage.update_decision(decision_id, lifecycle_stage=stage, card=card, review=review)

    def record_outcome(self, decision_id: str, outcome: str, notes: str = "") -> dict[str, Any]:
        decision = self.storage.get_decision(decision_id)
        if decision is None:
            raise KeyError(f"Decision not found: {decision_id}")
        if decision["card"] is None:
            raise ValueError("Cannot record outcome before a Decision Card exists.")

        card = decision["card"]
        recommendation = card["recommendation"]["action"]
        crm = decision["input"].get("crm_record") or {}
        outcome_record = {
            "outcome": outcome,
            "notes": notes,
            "recorded_at": utc_now(),
        }

        self.storage.insert_memory_case(
            {
                "customer_name": decision["customer_name"],
                "industry": crm.get("industry", decision["domain"]),
                "segment": crm.get("segment", "Unknown"),
                "problem": decision["title"],
                "recommendation": recommendation,
                "outcome": outcome,
                "confidence": card["confidence"],
                "tags": ["learned", decision["input"].get("persona_id", "persona"), outcome.lower()],
                "summary": (
                    f"{decision['customer_name']} decision: {decision['title']}. "
                    f"Recommendation was '{recommendation}'. Outcome: {outcome}. Notes: {notes}"
                ),
            }
        )

        return self.storage.update_decision(
            decision_id,
            lifecycle_stage="Learning",
            outcome=outcome_record,
        )

    def _create_context(self, decision: dict[str, Any], persona: dict[str, Any]) -> DecisionContext:
        input_payload = decision["input"]
        return DecisionContext(
            metadata=DecisionMetadata(
                decision_id=decision["id"],
                title=decision["title"],
                persona_id=persona["id"],
                persona_label=persona["label"],
                domain=persona["domain"],
                entity_name=decision["customer_name"],
                lifecycle_stage=decision["lifecycle_stage"],
            ),
            persona=persona,
            user_input=input_payload,
        )

    def _decision_card(self, decision: dict[str, Any], context: DecisionContext) -> dict[str, Any]:
        if context.recommendation is None:
            raise ValueError("Decision recommendation was not generated.")

        recommendation = context.recommendation
        return {
            "decision_id": decision["id"],
            "title": decision["title"],
            "customer_name": decision["customer_name"],
            "domain": context.metadata.domain,
            "lifecycle_stage": "Human Review",
            "executive_summary": recommendation.executive_summary,
            "recommendation": self._strategy_to_frontend(recommendation.recommended_action),
            "confidence": recommendation.confidence,
            "alternatives": [self._strategy_to_frontend(strategy) for strategy in recommendation.alternatives],
            "council_outputs": self._council_outputs(context),
            "evidence": recommendation.evidence,
            "risks": self._risks(context),
            "missing_information": context.open_questions,
            "business_reasoning": recommendation.reasoning,
            "human_review": {
                "status": "pending",
                "available_actions": ["approve", "reject", "modify", "request_more_information"],
            },
            "created_at": utc_now(),
            "structured_context": context.structured_context.model_dump() if context.structured_context else None,
            "council_discussion": [message.model_dump() for message in context.council_messages],
            "consensus": context.consensus.model_dump() if context.consensus else None,
            "decision_matrix": recommendation.decision_matrix,
            "llm_metadata": context.llm_metadata,
        }

    def _strategy_to_frontend(self, strategy: SimulationStrategy) -> dict[str, Any]:
        return {
            "action": strategy.title,
            "success_probability": strategy.probability,
            "revenue_impact": strategy.expected_outcome,
            "risk_level": strategy.risk,
            "reasoning": strategy.reason,
            "required_owner": strategy.owner,
            "evidence": strategy.evidence,
        }

    def _council_outputs(self, context: DecisionContext) -> dict[str, dict[str, Any]]:
        structured = context.structured_context
        risk = context.risk_analysis
        recommendation = context.recommendation

        return {
            "planner": {
                "name": "Planner",
                "role": "Orchestrates the shared DecisionContext and schedules the Executive Council.",
                "status": "completed",
                "summary": "Planner routed one shared blackboard through context, knowledge, memory, risk, simulation, council, and Decision Core.",
                "confidence": context.consensus.confidence if context.consensus else 80,
                "findings": {
                    "selected_agents": ["context", "knowledge", "memory", "risk", "simulation"],
                    "llm_metadata": context.llm_metadata,
                    "lifecycle": [
                        "Draft",
                        "Evidence Collection",
                        "Decision Council Discussion",
                        "Simulation",
                        "Recommendation",
                        "Human Review",
                    ],
                },
                "evidence": [],
                "missing_information": context.open_questions,
            },
            "context": {
                "name": "Context Agent",
                "role": "Only agent allowed to read the original input and convert it into structured business facts.",
                "status": "completed",
                "summary": structured.summary if structured else "Structured context unavailable.",
                "confidence": round((structured.confidence if structured else 0.5) * 100),
                "findings": {
                    "business_context": structured.model_dump() if structured else {},
                },
                "evidence": [],
                "missing_information": structured.required_context if structured else [],
            },
            "knowledge": {
                "name": "Knowledge Agent",
                "role": "Retrieves company policies, playbooks, SOPs, and guidelines.",
                "status": "completed",
                "summary": f"Retrieved {len(context.retrieved_knowledge)} relevant company knowledge source(s).",
                "confidence": self._retrieval_confidence([item.score for item in context.retrieved_knowledge]),
                "findings": {
                    "documents_found": len(context.retrieved_knowledge),
                    "constraints": [constraint for item in context.retrieved_knowledge for constraint in item.constraints],
                },
                "evidence": [item.model_dump() for item in context.retrieved_knowledge],
                "missing_information": [],
            },
            "memory": {
                "name": "Memory Agent",
                "role": "Retrieves similar historical decisions and outcomes.",
                "status": "completed",
                "summary": f"Found {len(context.historical_memory)} historical memory case(s).",
                "confidence": self._retrieval_confidence([item.relevance for item in context.historical_memory]),
                "findings": {
                    "similar_cases": len(context.historical_memory),
                    "outcomes": [item.outcome for item in context.historical_memory],
                },
                "evidence": [item.model_dump() for item in context.historical_memory],
                "missing_information": [],
            },
            "risk": {
                "name": "Risk Agent",
                "role": "Evaluates business, financial, operational, execution, and confidence risk.",
                "status": "completed",
                "summary": (
                    f"{risk.overall_level} risk detected with score {risk.score}/100."
                    if risk
                    else "Risk analysis unavailable."
                ),
                "confidence": 84,
                "findings": risk.model_dump() if risk else {},
                "evidence": [{"source": "Structured Context", "detail": structured.model_dump() if structured else {}}],
                "missing_information": risk.missing_information if risk else [],
            },
            "simulation": {
                "name": "Simulation Agent",
                "role": "Compares multiple strategies without choosing the final answer.",
                "status": "completed",
                "summary": f"Simulated {len(context.simulations)} possible strategy path(s).",
                "confidence": 86,
                "findings": {
                    "strategies": [strategy.model_dump() for strategy in context.simulations],
                    "decision_core_selected": recommendation.recommended_action.title if recommendation else None,
                },
                "evidence": [{"source": "Decision Matrix", "detail": recommendation.decision_matrix if recommendation else []}],
                "missing_information": [],
            },
        }

    def _risks(self, context: DecisionContext) -> list[str]:
        risk = context.risk_analysis
        if risk is None:
            return []
        risks = [
            *risk.business_risks,
            *risk.financial_risks,
            *risk.operational_risks,
            *risk.execution_risks,
            *risk.confidence_risks,
        ]
        return [f"{item.label}: {item.rationale}" for item in risks]

    def _retrieval_confidence(self, scores: list[float]) -> int:
        if not scores:
            return 55
        return max(60, min(94, int(62 + max(scores) * 30)))
