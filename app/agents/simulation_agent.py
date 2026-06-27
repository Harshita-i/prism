from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.models import ActionOption, AgentResult
from app.utils import clamp, compact_text, contains_any


class SimulationAgent(BaseAgent):
    name = "Simulation Agent"
    role = "Compares possible actions before the platform recommends one."

    def run(self, decision_input: dict[str, Any], context: dict[str, Any], storage: Any) -> AgentResult:
        text = compact_text(decision_input)
        risk = context.get("risk")
        risk_score = 50
        if risk:
            risk_score = risk.findings.get("risk_score", 50)

        memory = context.get("memory")
        similar_cases = memory.evidence if memory else []

        workshop_success = sum(
            1 for case in similar_cases
            if "workshop" in case["recommendation"].lower()
            and case["outcome"].lower() in {"renewed", "expanded"}
        )

        discount_success = sum(
            1 for case in similar_cases
            if "discount" in case["recommendation"].lower()
            and case["outcome"].lower() in {"renewed", "expanded"}
        )

        pricing_signal = contains_any(text, ["pricing", "expensive", "budget", "discount"])
        competitor_signal = contains_any(text, ["competitor", "alternative", "evaluating"])
        support_signal = contains_any(text, ["support", "ticket", "bug", "sla"])

        options = [
            ActionOption(
                action="Schedule executive value workshop",
                success_probability=clamp(
                    68 + workshop_success * 7 + (8 if pricing_signal else 0) + (7 if competitor_signal else 0),
                    maximum=92,
                ),
                revenue_impact="High retention, low margin loss",
                risk_level="Low",
                reasoning="Addresses pricing by proving value before changing commercial terms.",
                required_owner="Customer Success Manager + Account Executive",
                evidence=[
                    "Pricing policy prefers value alignment before discounts.",
                    "Similar successful cases used executive workshops.",
                ],
            ),
            ActionOption(
                action="Offer targeted renewal discount",
                success_probability=clamp(
                    56 + discount_success * 6 + (8 if pricing_signal else 0) - (8 if risk_score > 75 else 0),
                    maximum=84,
                ),
                revenue_impact="Medium retention, direct margin loss",
                risk_level="Medium",
                reasoning="May reduce buying friction, but can train the customer to negotiate before value is confirmed.",
                required_owner="Account Executive + Finance Approval",
                evidence=[
                    "Discounts above policy threshold require approval.",
                    "Discount works best when budget reduction is confirmed.",
                ],
            ),
            ActionOption(
                action="Launch technical success recovery plan",
                success_probability=clamp(
                    57 + (18 if support_signal else 0) + (8 if risk_score >= 70 else 0),
                    maximum=86,
                ),
                revenue_impact="Medium retention, operational cost",
                risk_level="Medium",
                reasoning="Useful when technical blockers or support issues are the main cause of renewal risk.",
                required_owner="Solutions Engineer + Support Lead",
                evidence=[
                    "Support escalation guidelines require a named owner and customer-visible recovery plan.",
                ],
            ),
        ]

        sorted_options = sorted(options, key=lambda option: option.success_probability, reverse=True)

        return AgentResult(
            name=self.name,
            role=self.role,
            status="completed",
            summary=f"Simulated {len(sorted_options)} next best actions.",
            confidence=86,
            findings={
                "options": [option.to_dict() for option in sorted_options],
                "best_action": sorted_options[0].action,
            },
            evidence=[
                {"source": "Simulation", "detail": option.to_dict()}
                for option in sorted_options
            ],
            missing_information=[],
        )