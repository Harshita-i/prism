from __future__ import annotations

import hashlib
from statistics import mean

from app.core.decision_context import (
    DecisionContext,
    ScenarioMetrics,
    ScenarioPacket,
    SimulationStrategy,
    WhatIfProjection,
)


RISK_VALUE = {"Low": 0.9, "Medium": 0.62, "High": 0.34, "Critical": 0.18}
COST_VALUE = {"Low": 0.9, "Medium": 0.62, "High": 0.34}
COMPLEXITY_VALUE = {"Low": 0.88, "Medium": 0.62, "High": 0.38}


class ScenarioEngine:
    """
    Generates and ranks plausible future business scenarios.

    It uses Prism-owned business logic only: structured context, persona action
    catalog, Knowledge Packets, Memory Packets, risk analysis, and planner state.
    No LLM calls happen here.
    """

    def generate(self, context: DecisionContext) -> DecisionContext:
        structured = context.structured_context
        if structured is None:
            raise ValueError("ScenarioEngine requires structured_context.")

        scenarios = [
            self._scenario_from_action(context, action, index)
            for index, action in enumerate(context.persona.get("actions", []), start=1)
        ]
        if not scenarios:
            scenarios = [self._fallback_scenario(context)]

        ranked = sorted(scenarios, key=lambda item: item.weighted_score, reverse=True)
        rejected = [
            scenario
            for scenario in ranked
            if scenario.rejection_reason is not None or scenario.weighted_score < 0.45
        ]
        accepted = [scenario for scenario in ranked if scenario not in rejected]
        final_ranking = accepted or ranked

        context.scenario_packets = final_ranking
        context.rejected_scenarios = rejected
        context.winning_scenario = final_ranking[0] if final_ranking else None
        context.scenario_confidence = round(max((item.confidence for item in final_ranking), default=0.0), 3)
        context.scenario_ranking = [
            {
                "id": item.id,
                "title": item.title,
                "weighted_score": item.weighted_score,
                "success_probability": item.success_probability,
                "risk": item.business_risk,
                "cost": item.financial_cost,
                "confidence": item.confidence,
            }
            for item in final_ranking
        ]
        context.scenario_metrics = ScenarioMetrics(
            generated=len(scenarios),
            ranked=len(final_ranking),
            rejected=len(rejected),
            average_confidence=round(mean([item.confidence for item in final_ranking]), 3) if final_ranking else 0.0,
            average_success=round(mean([item.success_probability for item in final_ranking]), 3) if final_ranking else 0.0,
        )
        context.simulations = [self._to_simulation_strategy(item) for item in final_ranking]
        return context

    def _scenario_from_action(self, context: DecisionContext, action: dict, index: int) -> ScenarioPacket:
        structured = context.structured_context
        assert structured is not None

        title = action["action"]
        knowledge_support, knowledge_ids = self._knowledge_support(context, action)
        historical_support, memory_ids = self._historical_support(context, action)
        planner_priority = self._planner_priority(context, action)
        risk_level = action.get("risk_level", "Medium")
        cost = self._cost(action)
        complexity = self._complexity(action)
        base_success = int(action.get("base_success", 55)) / 100
        risk_penalty = 1 - RISK_VALUE.get(risk_level, 0.62)
        support_bonus = (knowledge_support * 0.1) + (historical_support * 0.14) + (planner_priority * 0.06)
        success = max(0.05, min(0.96, base_success + support_bonus - risk_penalty * 0.08))
        confidence = max(0.35, min(0.97, 0.42 + knowledge_support * 0.22 + historical_support * 0.24 + planner_priority * 0.12))
        weighted = self._weighted_score(
            success=success,
            risk=risk_level,
            cost=cost,
            confidence=confidence,
            knowledge_support=knowledge_support,
            historical_support=historical_support,
            planner_priority=planner_priority,
            complexity=complexity,
        )
        rejection_reason = self._rejection_reason(action, context, weighted)
        scenario_id = self._scenario_id(context.metadata.decision_id, title)

        return ScenarioPacket(
            id=scenario_id,
            title=title,
            strategy_type=context.persona.get("decision_type", "Business Strategy"),
            description=action.get("reasoning", title),
            success_probability=round(success, 3),
            business_risk=risk_level,
            operational_risk=self._operational_risk(context, action),
            financial_cost=cost,
            implementation_complexity=complexity,
            expected_outcome=action.get("impact", "Business impact to be reviewed"),
            time_to_impact=self._time_to_impact(context, action),
            confidence=round(confidence, 3),
            weighted_score=weighted,
            knowledge_support=round(knowledge_support, 3),
            historical_support=round(historical_support, 3),
            planner_priority=round(planner_priority, 3),
            reason=self._reason(action, knowledge_support, historical_support, planner_priority),
            owner=action.get("owner", "Business Owner"),
            evidence=action.get("evidence", []),
            knowledge_packet_ids=knowledge_ids,
            memory_packet_ids=memory_ids,
            what_if=self._what_if(context, success, risk_level, cost),
            rejection_reason=rejection_reason,
        )

    def _knowledge_support(self, context: DecisionContext, action: dict) -> tuple[float, list[str]]:
        action_text = self._action_text(action)
        matched = []
        scores = []
        for packet in context.knowledge_packets:
            packet_text = " ".join([packet.title, packet.finding, " ".join(packet.supports)]).lower()
            if self._overlap(action_text, packet_text):
                matched.append(packet.id)
                scores.append(packet.confidence)
        if not scores:
            return 0.25 if context.knowledge_packets else 0.0, []
        return min(1.0, max(scores) + min(0.12, len(scores) * 0.03)), matched[:4]

    def _historical_support(self, context: DecisionContext, action: dict) -> tuple[float, list[str]]:
        action_name = action.get("action", "").lower()
        matched = []
        scores = []
        for packet in context.memory_packets:
            if self._overlap(action_name, packet.winning_strategy.lower()) or self._overlap(action_name, packet.reason.lower()):
                matched.append(packet.id)
                outcome = packet.outcome.lower()
                score = packet.confidence
                if any(term in outcome for term in ["won", "renewed", "stayed", "improved", "protected", "closed"]):
                    score += 0.12
                if any(term in outcome for term in ["lost", "churned", "resigned", "breached", "failed"]):
                    score -= 0.18
                scores.append(max(0.0, min(1.0, score)))
        if not scores:
            return 0.2 if context.memory_packets else 0.0, []
        return min(1.0, max(scores)), matched[:4]

    def _planner_priority(self, context: DecisionContext, action: dict) -> float:
        signal_text = " ".join(signal.label.lower() for signal in (context.structured_context.business_signals if context.structured_context else []))
        drivers = " ".join(action.get("decision_drivers", [])).lower()
        if self._overlap(signal_text, drivers):
            return 0.86
        if context.risk_analysis and context.risk_analysis.overall_level in {"High", "Critical"}:
            return 0.72
        return 0.55

    def _weighted_score(
        self,
        *,
        success: float,
        risk: str,
        cost: str,
        confidence: float,
        knowledge_support: float,
        historical_support: float,
        planner_priority: float,
        complexity: str,
    ) -> float:
        score = (
            success * 0.31
            + RISK_VALUE.get(risk, 0.62) * 0.16
            + COST_VALUE.get(cost, 0.62) * 0.1
            + confidence * 0.17
            + knowledge_support * 0.11
            + historical_support * 0.11
            + planner_priority * 0.08
            + COMPLEXITY_VALUE.get(complexity, 0.62) * 0.06
        )
        return round(max(0.0, min(1.0, score)), 4)

    def _cost(self, action: dict) -> str:
        text = " ".join([action.get("impact", ""), action.get("reasoning", ""), action.get("action", "")]).lower()
        if any(term in text for term in ["discount", "salary", "compensation", "expedite", "delay elective", "high cost", "margin loss"]):
            return "High"
        if any(term in text for term in ["workshop", "mentor", "meeting", "huddle", "validation"]):
            return "Low"
        return "Medium"

    def _complexity(self, action: dict) -> str:
        owner = action.get("owner", "")
        text = " ".join([owner, action.get("action", "")]).lower()
        if "+" in owner or any(term in text for term in ["vp", "finance", "specialist", "procurement", "clinical"]):
            return "High"
        if any(term in text for term in ["manager", "lead", "huddle"]):
            return "Medium"
        return "Low"

    def _operational_risk(self, context: DecisionContext, action: dict) -> str:
        if context.risk_analysis and context.risk_analysis.overall_level in {"High", "Critical"}:
            return "High" if action.get("risk_level") == "High" else "Medium"
        return action.get("risk_level", "Medium")

    def _time_to_impact(self, context: DecisionContext, action: dict) -> str:
        text = action.get("action", "").lower()
        if any(term in text for term in ["meeting", "huddle", "workshop", "validation"]):
            return "7 Days"
        if any(term in text for term in ["plan", "recovery", "mentor", "mobility"]):
            return "14 Days"
        if any(term in text for term in ["review", "transfer", "supplier"]):
            return "30 Days"
        return "2-4 Weeks"

    def _rejection_reason(self, action: dict, context: DecisionContext, weighted: float) -> str | None:
        signals = " ".join(signal.label.lower() for signal in (context.structured_context.business_signals if context.structured_context else []))
        for avoid in action.get("avoid_when", []):
            if self._overlap(avoid.lower(), signals):
                return f"Rejected because avoid condition matched: {avoid}."
        if weighted < 0.45:
            return "Rejected because scenario score is below Prism threshold."
        return None

    def _what_if(self, context: DecisionContext, success: float, risk: str, cost: str) -> list[WhatIfProjection]:
        return [
            WhatIfProjection(
                condition="Budget decreases",
                projected_change="Lower affordability for high-cost options.",
                success_delta=-10 if cost == "High" else -4,
                risk_delta="Financial risk increases",
                mitigation="Prefer lower-cost evidence-backed action before commercial concession.",
            ),
            WhatIfProjection(
                condition="Timeline compresses",
                projected_change="Fast interventions gain value over complex programs.",
                success_delta=-8 if success < 0.7 else -3,
                risk_delta="Execution risk increases",
                mitigation="Assign a clear owner and first checkpoint within seven days.",
            ),
            WhatIfProjection(
                condition="Stakeholder rejects first proposal",
                projected_change="Fallback path should use the next-ranked scenario.",
                success_delta=-12,
                risk_delta=f"{risk} risk may increase",
                mitigation="Use council evidence to switch to the next scenario.",
            ),
        ]

    def _reason(self, action: dict, knowledge_support: float, historical_support: float, planner_priority: float) -> str:
        return (
            f"{action.get('reasoning', 'Scenario is aligned with the persona action catalog.')} "
            f"Knowledge support={knowledge_support:.2f}, memory support={historical_support:.2f}, "
            f"planner priority={planner_priority:.2f}."
        )

    def _to_simulation_strategy(self, scenario: ScenarioPacket) -> SimulationStrategy:
        return SimulationStrategy(
            title=scenario.title,
            description=scenario.description,
            probability=round(scenario.success_probability * 100),
            risk=scenario.business_risk,
            expected_outcome=scenario.expected_outcome,
            reason=scenario.reason,
            owner=scenario.owner,
            evidence=[*scenario.evidence, *scenario.knowledge_packet_ids, *scenario.memory_packet_ids],
        )

    def _fallback_scenario(self, context: DecisionContext) -> ScenarioPacket:
        return ScenarioPacket(
            id=self._scenario_id(context.metadata.decision_id, "Request More Information"),
            title="Request more information",
            strategy_type=context.metadata.persona_label,
            description="Gather missing evidence before making a business recommendation.",
            success_probability=0.5,
            business_risk="Medium",
            expected_outcome="Improves decision quality before execution",
            time_to_impact="7 Days",
            confidence=0.55,
            weighted_score=0.5,
            reason="No configured action strategies were available.",
            owner="Business Owner",
        )

    def _scenario_id(self, decision_id: str, title: str) -> str:
        digest = hashlib.sha256(f"{decision_id}:{title}".encode("utf-8")).hexdigest()[:12]
        return f"scn-{digest}"

    def _action_text(self, action: dict) -> str:
        return " ".join(
            [
                action.get("action", ""),
                action.get("reasoning", ""),
                action.get("impact", ""),
                " ".join(action.get("decision_drivers", [])),
            ]
        ).lower()

    def _overlap(self, left: str, right: str) -> bool:
        left_terms = {term for term in left.replace("-", " ").split() if len(term) > 2}
        right_terms = {term for term in right.replace("-", " ").split() if len(term) > 2}
        return bool(left_terms.intersection(right_terms))
