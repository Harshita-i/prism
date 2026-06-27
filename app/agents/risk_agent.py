from __future__ import annotations

from typing import Any

from app.core.decision_context import DecisionContext, RiskAnalysis, RiskFinding
from app.utils import clamp


class RiskAgent:
    name = "Risk Agent"

    URGENCY_SCORE = {
        "Low": 8,
        "Medium": 18,
        "High": 30,
        "Critical": 44,
    }

    SEVERITY_SCORE = {
        "Low": 5,
        "Medium": 10,
        "High": 18,
        "Critical": 28,
    }

    def analyze(self, context: DecisionContext) -> DecisionContext:
        structured = self._structured(context)
        score = self.URGENCY_SCORE.get(structured.urgency, 18)
        score += 10 if structured.sentiment == "Negative" else 6 if structured.sentiment == "Mixed" else 0
        score += min(24, sum(self.SEVERITY_SCORE.get(signal.severity, 10) for signal in structured.business_signals))
        score += min(12, len(structured.required_context) * 3)
        score = clamp(score, 0, 100)

        overall_level = self._risk_level(score)
        business_risks = [
            RiskFinding(
                label=signal.label,
                level=signal.severity,
                rationale=f"{signal.label} affects {context.metadata.persona_label} decision quality.",
                evidence=signal.evidence,
            )
            for signal in structured.business_signals
        ]

        operational_risks = self._operational_risks(context)
        financial_risks = self._financial_risks(context)
        execution_risks = self._execution_risks(context)
        confidence_risks = [
            RiskFinding(
                label=missing,
                level="Medium",
                rationale="Missing information may lower confidence during human review.",
            )
            for missing in structured.required_context
        ]

        context.risk_analysis = RiskAnalysis(
            overall_level=overall_level,
            score=score,
            business_risks=business_risks,
            financial_risks=financial_risks,
            operational_risks=operational_risks,
            execution_risks=execution_risks,
            confidence_risks=confidence_risks,
            missing_information=structured.required_context,
        )
        return context

    def _structured(self, context: DecisionContext):
        if context.structured_context is None:
            raise ValueError("RiskAgent requires structured_context.")
        return context.structured_context

    def _risk_level(self, score: int) -> str:
        if score >= 86:
            return "Critical"
        if score >= 62:
            return "High"
        if score >= 36:
            return "Medium"
        return "Low"

    def _operational_risks(self, context: DecisionContext) -> list[RiskFinding]:
        risks = []
        if not context.retrieved_knowledge:
            risks.append(
                RiskFinding(
                    label="Limited policy grounding",
                    level="Medium",
                    rationale="No knowledge source was retrieved for this decision.",
                )
            )
        return risks

    def _financial_risks(self, context: DecisionContext) -> list[RiskFinding]:
        risks = []
        actions = context.persona.get("actions", [])
        high_cost_actions = [action for action in actions if "cost" in str(action.get("impact", "")).lower() or "margin loss" in str(action.get("impact", "")).lower()]
        if high_cost_actions:
            risks.append(
                RiskFinding(
                    label="Commercial impact possible",
                    level="Medium",
                    rationale="Some available actions may create direct cost, revenue, margin, or capacity impact.",
                    evidence=", ".join(action["action"] for action in high_cost_actions[:2]),
                )
            )
        return risks

    def _execution_risks(self, context: DecisionContext) -> list[RiskFinding]:
        risks = []
        if context.historical_memory:
            failed = [case for case in context.historical_memory if self._negative_outcome(case.outcome)]
            if failed:
                risks.append(
                    RiskFinding(
                        label="Historical failure pattern",
                        level="High" if len(failed) > 1 else "Medium",
                        rationale=f"{len(failed)} similar historical case(s) had weak outcomes.",
                        evidence=", ".join(case.outcome for case in failed[:3]),
                    )
                )
        return risks

    def _negative_outcome(self, outcome: str) -> bool:
        normalized = outcome.lower()
        return any(term in normalized for term in ["churn", "resign", "lost", "breach", "failed", "escalated"])
