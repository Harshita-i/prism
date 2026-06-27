from __future__ import annotations

from typing import Any

from app.agents import (
    ContextAgent,
    DecisionAgent,
    KnowledgeAgent,
    MemoryAgent,
    PlannerAgent,
    RiskAgent,
    SimulationAgent,
)
from app.models import AgentResult, utc_now


class DecisionOrchestrator:
    def __init__(self, storage: Any):
        self.storage = storage
        self.planner = PlannerAgent()
        self.agents = {
            "context": ContextAgent(),
            "knowledge": KnowledgeAgent(),
            "memory": MemoryAgent(),
            "risk": RiskAgent(),
            "simulation": SimulationAgent(),
        }
        self.decision_agent = DecisionAgent()

    def run_decision(self, decision_id: str) -> dict[str, Any]:
        decision = self.storage.get_decision(decision_id)
        if decision is None:
            raise KeyError(f"Decision not found: {decision_id}")

        decision_input = decision["input"]
        planner_result = self.planner.run(decision_input, {}, self.storage)
        selected_agents = planner_result.findings["selected_agents"]

        council_outputs: dict[str, AgentResult] = {
            "planner": planner_result,
        }

        self.storage.update_decision(decision_id, lifecycle_stage="Evidence Collection")

        for agent_key in selected_agents:
            if agent_key not in self.agents:
                continue
            if agent_key == "simulation":
                self.storage.update_decision(decision_id, lifecycle_stage="Simulation")
            else:
                self.storage.update_decision(decision_id, lifecycle_stage="Decision Council Discussion")

            result = self.agents[agent_key].run(decision_input, council_outputs, self.storage)
            council_outputs[agent_key] = result

        card = self.decision_agent.create_decision_card(decision, council_outputs)
        updated = self.storage.update_decision(
            decision_id,
            lifecycle_stage="Human Review",
            card=card,
            review=card["human_review"],
        )
        return updated

    def record_review(self, decision_id: str, action: str, reviewer: str, notes: str = "", modified_action: str | None = None) -> dict[str, Any]:
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
                "industry": crm.get("industry", "Unknown"),
                "segment": crm.get("segment", "Unknown"),
                "problem": decision["title"],
                "recommendation": recommendation,
                "outcome": outcome,
                "confidence": card["confidence"],
                "tags": ["learned", decision["domain"].lower(), outcome.lower()],
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
