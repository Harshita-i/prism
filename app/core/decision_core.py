from __future__ import annotations

from app.core.decision_context import DecisionContext, Recommendation, SimulationStrategy


class DecisionCore:
    """
    Synthesizes the final Decision Card from the shared DecisionContext.

    This class does not read raw user text. It only consumes structured
    context, specialist findings, council discussion, and consensus.
    """

    def synthesize(self, context: DecisionContext) -> DecisionContext:
        if not context.simulations:
            raise ValueError("DecisionCore requires at least one simulated strategy.")

        recommended = self._select_strategy(context)
        alternatives = [strategy for strategy in context.simulations if strategy.title != recommended.title]
        evidence = self._evidence(context)
        reasoning = self._reasoning(context, recommended)

        context.recommendation = Recommendation(
            executive_summary=self._executive_summary(context, recommended),
            recommended_action=recommended,
            alternatives=alternatives,
            decision_matrix=self._decision_matrix(context),
            confidence=self._confidence(context, recommended),
            reasoning=reasoning,
            evidence=evidence,
        )
        context.metadata.lifecycle_stage = "Human Review"
        return context

    def _select_strategy(self, context: DecisionContext) -> SimulationStrategy:
        if context.consensus and context.consensus.preferred_strategy:
            for strategy in context.simulations:
                if strategy.title == context.consensus.preferred_strategy:
                    return strategy
        return sorted(context.simulations, key=lambda item: item.probability, reverse=True)[0]

    def _executive_summary(self, context: DecisionContext, recommended: SimulationStrategy) -> str:
        structured = context.structured_context
        risk = context.risk_analysis
        problem = structured.primary_problem if structured else context.metadata.title
        risk_text = risk.overall_level if risk else recommended.risk
        return (
            f"Prism recommends {recommended.title} for {context.metadata.entity_name}. "
            f"The decision addresses {problem}, balances {risk_text} risk, and is backed by "
            f"{len(context.retrieved_knowledge)} knowledge source(s), {len(context.historical_memory)} memory case(s), "
            f"and {len(context.simulations)} simulated strategy path(s)."
        )

    def _decision_matrix(self, context: DecisionContext) -> list[dict[str, object]]:
        rows = []
        for strategy in sorted(context.simulations, key=lambda item: item.probability, reverse=True):
            rows.append(
                {
                    "action": strategy.title,
                    "success": strategy.probability,
                    "impact": strategy.expected_outcome,
                    "risk": strategy.risk,
                    "owner": strategy.owner,
                    "evidence": strategy.evidence[:3],
                    "reason": strategy.reason,
                }
            )
        return rows

    def _reasoning(self, context: DecisionContext, recommended: SimulationStrategy) -> list[str]:
        reasoning = [
            recommended.reason,
        ]

        if context.consensus:
            reasoning.extend(context.consensus.rationale[:3])
            reasoning.extend(context.consensus.disagreements[:2])

        if context.risk_analysis:
            reasoning.append(
                f"Risk Agent assessed overall risk as {context.risk_analysis.overall_level} with score {context.risk_analysis.score}/100."
            )

        if context.structured_context:
            signals = ", ".join(signal.label for signal in context.structured_context.business_signals[:4])
            if signals:
                reasoning.append(f"Structured context signals considered by downstream agents: {signals}.")

        return list(dict.fromkeys(reasoning))

    def _evidence(self, context: DecisionContext) -> list[dict[str, object]]:
        evidence: list[dict[str, object]] = []
        for item in context.retrieved_knowledge:
            evidence.append(
                {
                    "agent": "Knowledge Agent",
                    "title": item.title,
                    "source_type": item.source_type,
                    "detail": item.excerpt,
                    "score": item.score,
                }
            )
        for item in context.historical_memory:
            evidence.append(
                {
                    "agent": "Memory Agent",
                    "title": item.entity_name,
                    "source_type": "historical_decision",
                    "detail": item.summary,
                    "score": item.relevance,
                }
            )
        return evidence

    def _confidence(self, context: DecisionContext, recommended: SimulationStrategy) -> int:
        confidence = recommended.probability
        if context.consensus:
            confidence = int((confidence * 0.65) + (context.consensus.confidence * 0.35))
        if context.open_questions:
            confidence -= min(12, len(context.open_questions) * 3)
        if context.risk_analysis and context.risk_analysis.overall_level == "Critical":
            confidence -= 8
        return max(45, min(96, confidence))
