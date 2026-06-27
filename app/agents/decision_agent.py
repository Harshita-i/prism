from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.models import AgentResult, DecisionCard, utc_now
from app.utils import clamp


class DecisionAgent(BaseAgent):
    name = "Decision Agent"
    role = "Fuses all agent findings into one explainable Decision Card."

    def run(self, decision_input: dict[str, Any], context: dict[str, Any], storage: Any) -> AgentResult:
        raise RuntimeError("Use create_decision_card for the final fusion step.")

    def create_decision_card(
        self,
        decision: dict[str, Any],
        council_outputs: dict[str, AgentResult],
    ) -> dict[str, Any]:
        simulation = council_outputs["simulation"]
        risk = council_outputs["risk"]
        knowledge = council_outputs["knowledge"]
        memory = council_outputs["memory"]

        options = simulation.findings["options"]
        recommendation = options[0]
        alternatives = options[1:]

        risk_level = risk.findings["risk_level"]
        base_confidence = recommendation["success_probability"]
        evidence_bonus = min(10, len(knowledge.evidence) * 2 + len(memory.evidence) * 2)
        risk_penalty = 8 if risk_level == "High" else 3 if risk_level == "Medium" else 0
        confidence = clamp(base_confidence + evidence_bonus - risk_penalty, maximum=94)

        evidence = []

        evidence.extend(
            {
                "agent": "Knowledge Agent",
                "source": item["title"],
                "detail": item["excerpt"],
                "score": item["score"],
            }
            for item in knowledge.evidence
        )

        evidence.extend(
            {
                "agent": "Memory Agent",
                "source": item["customer_name"],
                "detail": f"{item['problem']} -> {item['recommendation']} -> {item['outcome']}",
                "score": item["score"],
            }
            for item in memory.evidence
        )

        missing_information = []
        for result in council_outputs.values():
            missing_information.extend(result.missing_information)

        reasoning = [
            f"The strongest simulated option is '{recommendation['action']}' with {recommendation['success_probability']} percent success probability.",
            f"Risk Agent classified this as {risk_level} risk.",
            "Knowledge Agent found company policy and playbook evidence supporting the recommendation.",
            "Memory Agent found similar historical cases that make the recommendation explainable.",
            "Human review is required before any action is executed.",
        ]

        card = DecisionCard(
            decision_id=decision["id"],
            title=decision["title"],
            customer_name=decision["customer_name"],
            domain=decision["domain"],
            lifecycle_stage="Recommendation",
            executive_summary=(
                f"DecisionOS recommends: {recommendation['action']}. "
                f"The recommendation balances renewal risk, company policy, similar historical outcomes, and simulated business impact."
            ),
            recommendation=recommendation,
            confidence=confidence,
            alternatives=alternatives,
            council_outputs={key: value.to_dict() for key, value in council_outputs.items()},
            evidence=evidence,
            risks=risk.findings["risk_factors"],
            missing_information=sorted(set(missing_information)),
            business_reasoning=reasoning,
            human_review={
                "status": "pending",
                "available_actions": ["approve", "reject", "modify", "request_more_information"],
            },
            created_at=utc_now(),
        )

        return card.to_dict()