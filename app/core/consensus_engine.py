from __future__ import annotations

from app.core.decision_context import Consensus, DecisionContext


class ConsensusEngine:
    def evaluate(self, context: DecisionContext) -> Consensus:
        knowledge = self._knowledge_confidence(context)
        memory = round(context.memory_confidence * 100)
        scenario = round(context.scenario_confidence * 100)
        risk = self._risk_confidence(context)
        planner = round(context.execution_metrics.average_confidence * 100) if context.execution_metrics else 70

        agreement_score = round(
            knowledge * 0.22
            + memory * 0.2
            + scenario * 0.24
            + risk * 0.2
            + planner * 0.14
        )
        strength = "Strong" if agreement_score >= 82 else "Moderate" if agreement_score >= 64 else "Weak"

        open_questions = list(dict.fromkeys(context.open_questions))
        rejected_arguments = self._rejected_arguments(context)
        minority_opinions = self._minority_opinions(context)
        supporting_evidence = self._supporting_evidence(context)
        preferred_strategy = context.winning_scenario.title if context.winning_scenario else None

        if context.risk_analysis and context.risk_analysis.overall_level in {"High", "Critical"} and scenario < 60:
            open_questions.append("Scenario confidence is low while decision risk is high.")

        explanation = (
            f"Consensus strength is {strength} with agreement score {agreement_score}/100. "
            f"Knowledge={knowledge}%, Memory={memory}%, Scenario={scenario}%, Risk={risk}%, Planner={planner}%."
        )

        context.consensus_score = agreement_score
        context.consensus_strength = strength
        context.rejected_arguments = rejected_arguments
        context.supporting_evidence = supporting_evidence
        context.minority_opinions = minority_opinions
        context.consensus_explanation = explanation

        return Consensus(
            status="Needs More Information" if open_questions and agreement_score < 70 else "Reached",
            level=strength,
            strength=strength,
            preferred_strategy=preferred_strategy,
            rationale=[
                *supporting_evidence[:4],
                explanation,
            ],
            disagreements=rejected_arguments,
            open_questions=open_questions,
            confidence=max(45, min(96, agreement_score)),
            agreement_score=agreement_score,
            minority_opinions=minority_opinions,
            rejected_arguments=rejected_arguments,
            explanation=explanation,
        )

    def _knowledge_confidence(self, context: DecisionContext) -> int:
        if not context.knowledge_packets:
            return 45
        return round(max(packet.confidence for packet in context.knowledge_packets) * 100)

    def _risk_confidence(self, context: DecisionContext) -> int:
        if context.risk_analysis is None:
            return 50
        safety = 100 - context.risk_analysis.score
        if context.risk_analysis.overall_level in {"High", "Critical"} and context.winning_scenario:
            if context.winning_scenario.business_risk in {"Low", "Medium"}:
                safety += 12
        return max(35, min(94, safety))

    def _rejected_arguments(self, context: DecisionContext) -> list[str]:
        rejected = []
        for scenario in context.rejected_scenarios:
            rejected.append(
                scenario.rejection_reason
                or f"{scenario.title} lost because its scenario score was {scenario.weighted_score}."
            )
        if context.risk_analysis:
            for finding in context.risk_analysis.execution_risks[:2]:
                rejected.append(f"Risk challenge: {finding.label} - {finding.rationale}")
        return list(dict.fromkeys(rejected))[:5]

    def _minority_opinions(self, context: DecisionContext) -> list[str]:
        opinions = []
        if context.rejected_scenarios:
            best_rejected = sorted(context.rejected_scenarios, key=lambda item: item.weighted_score, reverse=True)[0]
            opinions.append(
                f"Simulation minority view: {best_rejected.title} had upside but was rejected because {best_rejected.rejection_reason or 'its score was weaker'}."
            )
        if context.failure_patterns:
            opinions.append(f"Memory caution: {context.failure_patterns[0].summary}")
        return opinions[:4]

    def _supporting_evidence(self, context: DecisionContext) -> list[str]:
        evidence = []
        if context.knowledge_packets:
            evidence.append(f"Knowledge: {context.knowledge_packets[0].title} supports the leading strategy.")
        if context.memory_packets:
            evidence.append(f"Memory: {context.memory_packets[0].title} is the closest historical pattern.")
        if context.winning_scenario:
            evidence.append(f"Scenario: {context.winning_scenario.title} is ranked highest.")
        if context.risk_analysis:
            evidence.append(f"Risk: overall risk is {context.risk_analysis.overall_level}.")
        return evidence
