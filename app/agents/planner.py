from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.models import AgentResult
from app.utils import compact_text, contains_any


class PlannerAgent(BaseAgent):
    name = "Planner Agent"
    role = "Orchestrates the decision workflow and selects specialist agents."

    def run(self, decision_input: dict[str, Any], context: dict[str, Any], storage: Any) -> AgentResult:
        query = compact_text(decision_input)
        selected_agents = ["context", "knowledge", "memory", "risk"]
        reasoning = [
            "Context is required before recommendation.",
            "Knowledge retrieval is required to apply company policy.",
            "Memory retrieval is required to compare similar past cases.",
            "Risk analysis is required before human review.",
        ]

        if contains_any(query, ["renewal", "pricing", "discount", "competitor", "churn", "support"]):
            selected_agents.append("simulation")
            reasoning.append("Simulation is required because the request contains renewal, pricing, churn, or competitor signals.")

        if "simulation" not in selected_agents:
            selected_agents.append("simulation")
            reasoning.append("Simulation added because the platform must compare possible next best actions.")

        missing_information = []
        if "crm_record" not in decision_input or not decision_input.get("crm_record"):
            missing_information.append("CRM record is missing.")
        if "interaction_text" not in decision_input or not decision_input.get("interaction_text"):
            missing_information.append("Customer interaction text is missing.")

        return AgentResult(
            name=self.name,
            role=self.role,
            status="completed",
            summary="Execution plan created for the Decision Council.",
            confidence=88 if not missing_information else 74,
            findings={
                "intent": self._classify_intent(query),
                "selected_agents": selected_agents,
                "execution_order": selected_agents + ["decision_fusion"],
                "planning_reasoning": reasoning,
            },
            evidence=[],
            missing_information=missing_information,
        )

    def _classify_intent(self, query: str) -> str:
        if contains_any(query, ["renewal", "churn", "competitor"]):
            return "Customer renewal risk"
        if contains_any(query, ["pricing", "discount", "budget"]):
            return "Pricing objection"
        if contains_any(query, ["support", "ticket", "bug", "sla"]):
            return "Support escalation"
        return "General business decision"
