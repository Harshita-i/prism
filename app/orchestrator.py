from __future__ import annotations

from typing import Any

from app.agents import ContextAgent, KnowledgeAgent, MemoryAgent, RiskAgent, SimulationAgent
from app.core.context_extractor import LLMContextExtractor
from app.core.decision_context import DecisionContext, DecisionMetadata, Recommendation, SimulationStrategy
from app.core.executive_council import ExecutiveCouncil
from app.core.planner import Planner
from app.llm.service import LLMService
from app.memory.engine import MemoryEngine
from app.models import utc_now
from app.personas import get_persona


class DecisionOrchestrator:
    def __init__(self, storage: Any, llm_service: LLMService | None = None):
        self.storage = storage
        self.llm_service = llm_service or LLMService.from_env()
        self.memory_engine = MemoryEngine(storage)
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

        if not decision.get("lifecycle_history"):
            self.storage.add_lifecycle_event(
                decision_id,
                stage="Draft",
                status="completed",
                actor="User",
                notes="Decision was created from business input.",
            )
        self.storage.add_lifecycle_event(
            decision_id,
            stage="Evidence Collection",
            status="active",
            actor="Planner",
            notes="Planner started adaptive evidence collection.",
        )
        self.storage.update_decision(decision_id, lifecycle_stage="Evidence Collection")
        context = self.planner.run(context)

        card = self._decision_card(decision, context)
        updated = self.storage.update_decision(
            decision_id,
            lifecycle_stage="Human Review",
            card=card,
            review=card["human_review"],
        )
        self.storage.add_lifecycle_event(
            decision_id,
            stage="Executive Council",
            status="completed",
            actor="Executive Council",
            notes="Council reached consensus and forwarded evidence to Decision Core.",
        )
        self.storage.add_lifecycle_event(
            decision_id,
            stage="Pending Approval",
            status="active",
            actor="Decision Core",
            notes="Enterprise Decision Card is ready for human approval.",
        )
        self.storage.create_decision_version(
            decision_id,
            actor="Decision Core",
            change_type="decision_card_created",
            snapshot=card,
            change_log=[
                "Created enterprise Decision Card.",
                "Attached evidence, council consensus, planner reasoning, scenario support, and traceability.",
            ],
        )
        return self.storage.get_decision(decision_id) or updated

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

        normalized = action.strip().lower().replace(" ", "_")
        aliases = {
            "approved": "approve",
            "request_changes": "request_changes",
            "changes_requested": "request_changes",
            "more_info": "request_more_information",
            "request_more_info": "request_more_information",
        }
        normalized = aliases.get(normalized, normalized)
        if normalized not in {"approve", "reject", "modify", "request_changes", "request_more_information"}:
            raise ValueError(
                "Review action must be approve, reject, modify, request_changes, or request_more_information."
            )

        stage = "Approved" if normalized == "approve" else "Human Review"
        review = {
            "status": normalized,
            "reviewer": reviewer,
            "notes": notes,
            "modified_action": modified_action,
            "reviewed_at": utc_now(),
        }
        card = decision["card"]
        approval_log = card.get("approval_log", [])
        approval_log.append(review)
        card["human_review"] = review
        card["approval_status"] = normalized
        card["approval_log"] = approval_log
        if card.get("enterprise_decision_card"):
            next_version = self.storage.next_decision_version(decision_id)
            card["enterprise_decision_card"]["approval_status"] = normalized
            card["enterprise_decision_card"]["version"] = next_version
        event_stage = "Approved" if normalized == "approve" else "Pending Approval"
        event_status = "completed" if normalized == "approve" else "active"
        self.storage.add_lifecycle_event(
            decision_id,
            stage=event_stage,
            status=event_status,
            actor=reviewer,
            notes=notes or f"Human review action: {normalized}.",
        )
        updated = self.storage.update_decision(decision_id, lifecycle_stage=stage, card=card, review=review)
        self.storage.create_decision_version(
            decision_id,
            actor=reviewer,
            change_type=f"human_review_{normalized}",
            snapshot=card,
            change_log=[
                f"Human reviewer selected {normalized}.",
                notes or "No reviewer notes supplied.",
            ],
        )
        return self.storage.get_decision(decision_id) or updated

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
        outcome_status = self._normalized_outcome(outcome)
        outcome_metrics = {
            "outcome": outcome_status,
            "success_score": self._success_score(outcome_status),
            "business_impact": notes or f"Outcome recorded as {outcome}.",
            "notes": notes,
            "recorded_at": outcome_record["recorded_at"],
        }
        card["outcome_metrics"] = outcome_metrics
        card["lifecycle_stage"] = "Archived"
        if card.get("enterprise_decision_card"):
            next_version = self.storage.next_decision_version(decision_id)
            card["enterprise_decision_card"]["version"] = next_version
            card["enterprise_decision_card"]["traceability"]["outcome"] = outcome_metrics

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
        self.storage.add_lifecycle_event(
            decision_id,
            stage="In Progress",
            status="completed",
            actor="Business Owner",
            notes="Approved action moved into execution.",
        )
        self.storage.add_lifecycle_event(
            decision_id,
            stage="Completed",
            status="completed",
            actor="Business Owner",
            notes="Business execution was completed or closed.",
        )
        self.storage.add_lifecycle_event(
            decision_id,
            stage="Outcome Recorded",
            status="completed",
            actor="Prism",
            notes=notes or f"Outcome recorded as {outcome}.",
        )
        self.storage.add_lifecycle_event(
            decision_id,
            stage="Archived",
            status="completed",
            actor="Prism",
            notes="Decision is now reusable organizational memory.",
        )
        updated = self.storage.update_decision(
            decision_id,
            lifecycle_stage="Archived",
            card=card,
            outcome=outcome_record,
        )
        self.storage.create_decision_version(
            decision_id,
            actor="Prism",
            change_type="outcome_recorded",
            snapshot=card,
            change_log=[
                f"Outcome recorded as {outcome_status}.",
                "Decision archived into organizational memory.",
            ],
        )
        refreshed = self.storage.get_decision(decision_id) or updated
        self.memory_engine.archive_decision(refreshed)
        return refreshed

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
            "knowledge_packets": [packet.model_dump() for packet in context.knowledge_packets],
            "memory_packets": [packet.model_dump() for packet in context.memory_packets],
            "winning_patterns": [item.model_dump() for item in context.winning_patterns],
            "failure_patterns": [item.model_dump() for item in context.failure_patterns],
            "historical_evidence": context.historical_evidence,
            "memory_confidence": context.memory_confidence,
            "scenario_packets": [scenario.model_dump() for scenario in context.scenario_packets],
            "scenario_ranking": context.scenario_ranking,
            "scenario_confidence": context.scenario_confidence,
            "scenario_metrics": context.scenario_metrics.model_dump(),
            "rejected_scenarios": [scenario.model_dump() for scenario in context.rejected_scenarios],
            "winning_scenario": context.winning_scenario.model_dump() if context.winning_scenario else None,
            "council_discussion": [message.model_dump() for message in context.council_messages],
            "council_timeline": [message.model_dump() for message in context.council_timeline],
            "consensus_score": context.consensus_score,
            "consensus_strength": context.consensus_strength,
            "rejected_arguments": context.rejected_arguments,
            "supporting_evidence": context.supporting_evidence,
            "minority_opinions": context.minority_opinions,
            "planner_actions": context.planner_actions,
            "consensus_explanation": context.consensus_explanation,
            "agent_confidence": context.agent_confidence,
            "consensus": context.consensus.model_dump() if context.consensus else None,
            "decision_matrix": recommendation.decision_matrix,
            "llm_metadata": context.llm_metadata,
            "execution_plan": context.execution_plan.model_dump() if context.execution_plan else None,
            "executed_steps": context.executed_steps,
            "skipped_steps": context.skipped_steps,
            "planner_reasoning": context.planner_reasoning,
            "planner_timeline": [event.model_dump() for event in context.planner_timeline],
            "confidence_timeline": context.confidence_timeline,
            "execution_metrics": context.execution_metrics.model_dump(),
            "enterprise_decision_card": context.decision_card.model_dump() if context.decision_card else None,
            "decision_lifecycle": [event.model_dump() for event in context.decision_lifecycle],
            "decision_versions": [version.model_dump() for version in context.decision_versions],
            "approval_status": context.approval_status,
            "approval_log": [record.model_dump() for record in context.approval_log],
            "outcome_metrics": context.outcome_metrics.model_dump(),
            "decision_analytics": context.decision_analytics.model_dump(),
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
                    "execution_plan": context.execution_plan.model_dump() if context.execution_plan else None,
                    "executed_steps": context.executed_steps,
                    "skipped_steps": context.skipped_steps,
                    "planner_reasoning": context.planner_reasoning,
                    "execution_metrics": context.execution_metrics.model_dump(),
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
                "role": "Builds structured Knowledge Packets from local enterprise evidence.",
                "status": "completed",
                "summary": f"Generated {len(context.knowledge_packets)} Knowledge Packet(s) from ranked enterprise evidence.",
                "confidence": self._retrieval_confidence([item.weighted_score for item in context.knowledge_packets]),
                "findings": {
                    "packets_found": len(context.knowledge_packets),
                    "knowledge_engine": context.llm_metadata.get("knowledge_engine", {}),
                    "constraints": [constraint for item in context.knowledge_packets for constraint in item.constraints],
                },
                "evidence": [item.model_dump() for item in context.knowledge_packets],
                "missing_information": [],
            },
            "memory": {
                "name": "Memory Agent",
                "role": "Retrieves organizational decision experience and produces Memory Packets.",
                "status": "completed",
                "summary": f"Generated {len(context.memory_packets)} Memory Packet(s) from organizational experience.",
                "confidence": round(context.memory_confidence * 100),
                "findings": {
                    "memory_packets": len(context.memory_packets),
                    "outcomes": [item.outcome for item in context.memory_packets],
                    "winning_patterns": [item.model_dump() for item in context.winning_patterns],
                    "failure_patterns": [item.model_dump() for item in context.failure_patterns],
                    "memory_engine": context.llm_metadata.get("memory_engine", {}),
                },
                "evidence": [item.model_dump() for item in context.memory_packets],
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
                "name": "Scenario Intelligence Agent",
                "role": "Generates, evaluates, and ranks future business scenarios.",
                "status": "completed",
                "summary": f"Generated {len(context.scenario_packets)} Scenario Packet(s).",
                "confidence": round(context.scenario_confidence * 100),
                "findings": {
                    "scenario_packets": [scenario.model_dump() for scenario in context.scenario_packets],
                    "scenario_ranking": context.scenario_ranking,
                    "scenario_metrics": context.scenario_metrics.model_dump(),
                    "rejected_scenarios": [scenario.model_dump() for scenario in context.rejected_scenarios],
                    "winning_scenario": context.winning_scenario.model_dump() if context.winning_scenario else None,
                    "decision_core_selected": recommendation.recommended_action.title if recommendation else None,
                },
                "evidence": [{"source": "Scenario Engine", "detail": [scenario.model_dump() for scenario in context.scenario_packets]}],
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

    def _normalized_outcome(self, outcome: str) -> str:
        normalized = outcome.strip().lower()
        if normalized in {"succeeded", "success", "won", "renewed", "stayed", "resolved", "completed"}:
            return "Succeeded"
        if normalized in {"failed", "lost", "resigned", "churned"}:
            return "Failed"
        if normalized in {"partial", "partially successful", "partially_successful"}:
            return "Partially Successful"
        if normalized in {"cancelled", "canceled"}:
            return "Cancelled"
        return "Unknown"

    def _success_score(self, outcome_status: str) -> int | None:
        return {
            "Succeeded": 100,
            "Partially Successful": 60,
            "Failed": 0,
            "Cancelled": 0,
            "Unknown": None,
        }.get(outcome_status)
