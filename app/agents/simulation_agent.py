from __future__ import annotations

from app.core.decision_context import DecisionContext, SimulationStrategy
from app.utils import clamp


class SimulationAgent:
    name = "Simulation Agent"

    RISK_ADJUSTMENT = {
        "Low": 4,
        "Medium": -2,
        "High": -8,
        "Critical": -16,
    }

    def analyze(self, context: DecisionContext) -> DecisionContext:
        structured = self._structured(context)
        signals = {signal.label.lower() for signal in structured.business_signals}
        memory_actions = {case.recommendation.lower(): case for case in context.historical_memory}
        strategies = []

        for action in context.persona.get("actions", []):
            probability = int(action.get("base_success", 55))
            matched_drivers = self._matched_drivers(action, signals)
            avoided_conflicts = self._matched_avoidance(action, signals)

            probability += len(matched_drivers) * 7
            probability -= len(avoided_conflicts) * 10
            probability += self._knowledge_alignment(action, context)
            probability += self._memory_alignment(action, memory_actions)

            if context.risk_analysis:
                probability += self.RISK_ADJUSTMENT.get(action.get("risk_level", "Medium"), -2)
                if context.risk_analysis.overall_level in {"High", "Critical"} and action.get("risk_level") == "High":
                    probability -= 8

            max_success = int(action.get("max_success", 90))
            probability = clamp(probability, 25, max_success)
            reason = self._reason(action, matched_drivers, avoided_conflicts, context)

            strategies.append(
                SimulationStrategy(
                    title=action["action"],
                    description=action.get("reasoning", action["action"]),
                    probability=probability,
                    risk=action.get("risk_level", "Medium"),
                    expected_outcome=action.get("impact", "Business impact to be reviewed"),
                    reason=reason,
                    owner=action.get("owner", "Business Owner"),
                    evidence=action.get("evidence", []),
                )
            )

        context.simulations = sorted(strategies, key=lambda item: item.probability, reverse=True)
        return context

    def _structured(self, context: DecisionContext):
        if context.structured_context is None:
            raise ValueError("SimulationAgent requires structured_context.")
        return context.structured_context

    def _matched_drivers(self, action: dict, signals: set[str]) -> list[str]:
        matches = []
        for driver in action.get("decision_drivers", []):
            driver_terms = {term for term in driver.lower().replace("-", " ").split() if len(term) > 2}
            if driver.lower() in signals or any(driver.lower() in signal for signal in signals):
                matches.append(driver)
            elif driver_terms and any(driver_terms.issubset(set(signal.split())) for signal in signals):
                matches.append(driver)
        return matches

    def _matched_avoidance(self, action: dict, signals: set[str]) -> list[str]:
        conflicts = []
        for avoid in action.get("avoid_when", []):
            avoid_terms = {term for term in avoid.lower().replace("-", " ").split() if len(term) > 2}
            if avoid.lower() in signals or any(avoid.lower() in signal for signal in signals):
                conflicts.append(avoid)
            elif avoid_terms and any(avoid_terms.issubset(set(signal.split())) for signal in signals):
                conflicts.append(avoid)
        return conflicts

    def _knowledge_alignment(self, action: dict, context: DecisionContext) -> int:
        evidence_text = " ".join(item.title + " " + item.excerpt for item in context.retrieved_knowledge).lower()
        points = 0
        for driver in action.get("decision_drivers", []):
            if driver.lower() in evidence_text:
                points += 3
        return min(points, 9)

    def _memory_alignment(self, action: dict, memory_actions: dict) -> int:
        action_name = action["action"].lower()
        points = 0
        for previous_action, case in memory_actions.items():
            if previous_action in action_name or action_name in previous_action:
                outcome = case.outcome.lower()
                if any(term in outcome for term in ["renew", "stayed", "improved", "protected", "procurement", "closed"]):
                    points += 8
                elif any(term in outcome for term in ["churn", "resigned", "lost", "breach"]):
                    points -= 8
        return points

    def _reason(
        self,
        action: dict,
        matched_drivers: list[str],
        avoided_conflicts: list[str],
        context: DecisionContext,
    ) -> str:
        parts = [action.get("reasoning", "Strategy aligns with the configured persona playbook.")]
        if matched_drivers:
            parts.append(f"Matches structured signal(s): {', '.join(matched_drivers[:3])}.")
        if avoided_conflicts:
            parts.append(f"Risk warning: also matches avoid condition(s): {', '.join(avoided_conflicts[:2])}.")
        if context.retrieved_knowledge:
            parts.append(f"Grounded by {len(context.retrieved_knowledge)} retrieved knowledge source(s).")
        if context.historical_memory:
            parts.append(f"Compared with {len(context.historical_memory)} historical memory case(s).")
        return " ".join(parts)
