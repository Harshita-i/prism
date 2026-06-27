from __future__ import annotations

from typing import Any

from app.agents.base import BaseAgent
from app.models import AgentResult
from app.utils import clamp, compact_text, contains_any


class RiskAgent(BaseAgent):
    name = "Risk Agent"
    role = "Identifies churn, revenue, support, and confidence risks."

    def run(self, decision_input: dict[str, Any], context: dict[str, Any], storage: Any) -> AgentResult:
        crm = decision_input.get("crm_record") or {}
        support_history = decision_input.get("support_history") or []
        text = compact_text(decision_input)

        risk_score = 25
        risk_factors = []
        opportunity_signals = []

        if contains_any(text, ["pricing", "expensive", "budget", "discount"]):
            risk_score += 18
            risk_factors.append("Pricing objection detected.")
        if contains_any(text, ["competitor", "alternative", "evaluating"]):
            risk_score += 22
            risk_factors.append("Customer is evaluating competitors.")
        if contains_any(text, ["renewal", "contract"]):
            risk_score += 10
            risk_factors.append("Decision is close to renewal.")
        if support_history:
            risk_score += min(16, len(support_history) * 4)
            risk_factors.append(f"{len(support_history)} support item(s) may affect renewal confidence.")

        health_score = crm.get("health_score")
        if isinstance(health_score, (int, float)):
            if health_score < 60:
                risk_score += 18
                risk_factors.append("Customer health score is below 60.")
            elif health_score >= 75:
                risk_score -= 8
                opportunity_signals.append("Health score indicates enough adoption to defend value.")

        usage = crm.get("usage_trend")
        if usage == "up":
            risk_score -= 8
            opportunity_signals.append("Usage trend is increasing.")
        elif usage == "down":
            risk_score += 12
            risk_factors.append("Usage trend is decreasing.")

        risk_score = clamp(int(risk_score), 0, 100)
        risk_level = "High" if risk_score >= 70 else "Medium" if risk_score >= 40 else "Low"

        missing_information = []
        if "contract_value" not in crm:
            missing_information.append("Contract value is missing, so revenue impact is uncertain.")
        if "executive_sponsor" not in crm:
            missing_information.append("Executive sponsor is unknown.")

        return AgentResult(
            name=self.name,
            role=self.role,
            status="completed",
            summary=f"{risk_level} risk detected with score {risk_score}/100.",
            confidence=84 if risk_factors else 72,
            findings={
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "opportunity_signals": opportunity_signals,
            },
            evidence=[
                {"source": "CRM health score", "detail": health_score},
                {"source": "Support history count", "detail": len(support_history)},
            ],
            missing_information=missing_information,
        )