from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.models import AgentResult
from app.utils import compact_text, contains_any


class ContextAgent(BaseAgent):
    name = "Context Agent"
    role = "Builds the business situation before reasoning begins."

    def run(self, decision_input: dict[str, Any], context: dict[str, Any], storage: Any) -> AgentResult:
        crm = decision_input.get("crm_record") or {}
        support_history = decision_input.get("support_history") or []
        text = compact_text(decision_input)

        signals = []
        if contains_any(text, ["pricing", "expensive", "budget", "discount"]):
            signals.append("Pricing concern")
        if contains_any(text, ["competitor", "alternative", "evaluating"]):
            signals.append("Competitor evaluation")
        if contains_any(text, ["renewal", "contract"]):
            signals.append("Renewal conversation")
        if contains_any(text, ["ticket", "bug", "support", "sla"]):
            signals.append("Support concern")

        missing_information = []
        for field in ["health_score", "renewal_date", "contract_value", "industry", "segment"]:
            if field not in crm:
                missing_information.append(f"CRM field missing: {field}")

        findings = {
            "customer_name": decision_input.get("customer_name") or crm.get("customer_name", "Unknown Customer"),
            "industry": crm.get("industry", "Unknown"),
            "segment": crm.get("segment", "Unknown"),
            "renewal_date": crm.get("renewal_date", "Unknown"),
            "contract_value": crm.get("contract_value", "Unknown"),
            "health_score": crm.get("health_score", "Unknown"),
            "open_support_items": len(support_history),
            "detected_signals": signals,
        }

        confidence = 90 - min(30, len(missing_information) * 6)

        return AgentResult(
            name=self.name,
            role=self.role,
            status="completed",
            summary=f"Context built for {findings['customer_name']} with signals: {', '.join(signals) or 'none detected'}.",
            confidence=confidence,
            findings=findings,
            evidence=[
                {"source": "CRM", "detail": crm},
                {"source": "Support History", "detail": support_history},
            ],
            missing_information=missing_information,
        )