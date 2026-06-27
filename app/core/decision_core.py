from __future__ import annotations

from app.core.decision_context import (
    DecisionContext,
    DecisionLifecycleEvent,
    DecisionVersion,
    EnterpriseDecisionCard,
    Recommendation,
    ScenarioPacket,
    SimulationStrategy,
)


class DecisionCore:
    """
    Synthesizes the final Decision Card from the shared DecisionContext.

    This class does not read raw user text. It only consumes structured
    context, specialist findings, council discussion, and consensus.
    """

    def synthesize(self, context: DecisionContext) -> DecisionContext:
        if not context.simulations:
            context.simulations = self._fallback_strategies(context)

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

        context.approval_status = "pending"
        if not context.decision_lifecycle:
            context.decision_lifecycle.append(
                DecisionLifecycleEvent(
                    stage="Draft",
                    status="completed",
                    actor="User",
                    notes="Decision was created from business input.",
                )
            )
        context.decision_lifecycle.extend(
            [
                DecisionLifecycleEvent(
                    stage="Executive Council",
                    status="completed",
                    actor="Prism",
                    notes="Specialist agents discussed evidence and produced consensus.",
                ),
                DecisionLifecycleEvent(
                    stage="Pending Approval",
                    status="active",
                    actor="Prism",
                    notes="Decision Card is ready for human review.",
                ),
            ]
        )

        context.decision_card = self._enterprise_decision_card(context, recommended, alternatives)
        context.decision_versions.append(
            DecisionVersion(
                version=1,
                actor="Decision Core",
                change_type="decision_card_created",
                change_log=[
                    "Generated enterprise Decision Card from council consensus.",
                    "Attached knowledge, memory, scenario, planner, and council references.",
                ],
                snapshot=context.decision_card.model_dump(),
            )
        )
        context.metadata.lifecycle_stage = "Human Review"
        return context

    def _select_strategy(self, context: DecisionContext) -> SimulationStrategy:
        if context.consensus and context.consensus.preferred_strategy:
            for strategy in context.simulations:
                if strategy.title == context.consensus.preferred_strategy:
                    return strategy
        return sorted(context.simulations, key=lambda item: item.probability, reverse=True)[0]

    def _fallback_strategies(self, context: DecisionContext) -> list[SimulationStrategy]:
        strategies: list[SimulationStrategy] = []
        for action in context.persona.get("actions", []):
            strategies.append(
                SimulationStrategy(
                    title=action["action"],
                    description=action.get("reasoning", action["action"]),
                    probability=int(action.get("base_success", 60)),
                    risk=action.get("risk_level", "Medium"),
                    expected_outcome=action.get("impact", "Business impact to be reviewed"),
                    reason=(
                        "Simulation was skipped by the adaptive planner; Decision Core used the persona action catalog "
                        "and council evidence to assemble a conservative recommendation."
                    ),
                    owner=action.get("owner", "Business Owner"),
                    evidence=action.get("evidence", []),
                )
            )
        if not strategies:
            strategies.append(
                SimulationStrategy(
                    title="Request more information",
                    description="Gather additional evidence before choosing a business action.",
                    probability=50,
                    risk="Medium",
                    expected_outcome="Improves decision quality before execution",
                    reason="No action catalog or simulation output was available.",
                    owner="Business Owner",
                    evidence=[],
                )
            )
        return sorted(strategies, key=lambda item: item.probability, reverse=True)

    def _executive_summary(self, context: DecisionContext, recommended: SimulationStrategy) -> str:
        structured = context.structured_context
        risk = context.risk_analysis
        problem = structured.primary_problem if structured else context.metadata.title
        risk_text = risk.overall_level if risk else recommended.risk
        return (
            f"Prism recommends {recommended.title} for {context.metadata.entity_name}. "
            f"The decision addresses {problem}, balances {risk_text} risk, and is backed by "
            f"{len(context.knowledge_packets)} Knowledge Packet(s), {len(context.memory_packets)} Memory Packet(s), "
            f"and {len(context.simulations)} simulated strategy path(s)."
        )

    def _decision_matrix(self, context: DecisionContext) -> list[dict[str, object]]:
        rows = []
        for strategy in sorted(context.simulations, key=lambda item: item.probability, reverse=True):
            scenario = next((item for item in context.scenario_packets if item.title == strategy.title), None)
            rows.append(
                {
                    "action": strategy.title,
                    "success": strategy.probability,
                    "impact": strategy.expected_outcome,
                    "risk": strategy.risk,
                    "owner": strategy.owner,
                    "evidence": strategy.evidence[:3],
                    "reason": strategy.reason,
                    "scenario_packet_id": scenario.id if scenario else None,
                    "scenario_score": scenario.weighted_score if scenario else None,
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
        for item in context.knowledge_packets:
            evidence.append(
                {
                    "agent": "Knowledge Agent",
                    "title": item.title,
                    "source_type": item.source_type,
                    "detail": item.finding,
                    "score": item.weighted_score,
                    "knowledge_packet_id": item.id,
                    "document_id": item.document_id,
                    "supports": item.supports,
                }
            )
        for item in context.memory_packets:
            evidence.append(
                {
                    "agent": "Memory Agent",
                    "title": item.title,
                    "source_type": "historical_decision",
                    "detail": item.reason,
                    "score": item.weighted_score,
                    "memory_packet_id": item.id,
                    "source_decision": item.source_decision,
                    "outcome": item.outcome,
                    "explainability": item.explainability,
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

    def _enterprise_decision_card(
        self,
        context: DecisionContext,
        recommended: SimulationStrategy,
        alternatives: list[SimulationStrategy],
    ) -> EnterpriseDecisionCard:
        scenario = self._scenario_for(context, recommended)
        confidence = context.recommendation.confidence if context.recommendation else self._confidence(context, recommended)

        return EnterpriseDecisionCard(
            decision_id=context.metadata.decision_id,
            decision_title=context.metadata.title,
            executive_summary=context.recommendation.executive_summary if context.recommendation else "",
            recommendation=self._strategy_payload(recommended, scenario),
            alternative_strategies=[
                self._strategy_payload(strategy, self._scenario_for(context, strategy)) for strategy in alternatives
            ],
            decision_matrix=context.recommendation.decision_matrix if context.recommendation else [],
            supporting_evidence=context.recommendation.evidence if context.recommendation else [],
            confidence=confidence,
            consensus_strength=context.consensus_strength,
            business_impact=recommended.expected_outcome,
            risk=recommended.risk,
            estimated_cost=scenario.financial_cost if scenario else "Medium",
            time_to_impact=scenario.time_to_impact if scenario else "To be confirmed",
            approval_status=context.approval_status,
            version=len(context.decision_versions) + 1,
            planner_reasoning=context.planner_reasoning,
            council_summary=context.consensus_explanation or (context.consensus.explanation if context.consensus else ""),
            knowledge_references=[item.id for item in context.knowledge_packets],
            memory_references=[item.id for item in context.memory_packets],
            scenario_references=[item.id for item in context.scenario_packets],
            why_selected=self._why_selected(context, recommended, scenario),
            why_alternatives_rejected=self._why_alternatives_rejected(context, alternatives),
            traceability=self._traceability(context, recommended, scenario),
        )

    def _strategy_payload(self, strategy: SimulationStrategy, scenario: ScenarioPacket | None) -> dict[str, object]:
        return {
            "action": strategy.title,
            "description": strategy.description,
            "success_probability": strategy.probability,
            "business_impact": strategy.expected_outcome,
            "risk_level": strategy.risk,
            "reasoning": strategy.reason,
            "required_owner": strategy.owner,
            "estimated_cost": scenario.financial_cost if scenario else "Medium",
            "time_to_impact": scenario.time_to_impact if scenario else "To be confirmed",
            "scenario_packet_id": scenario.id if scenario else None,
            "evidence": strategy.evidence,
        }

    def _scenario_for(self, context: DecisionContext, strategy: SimulationStrategy) -> ScenarioPacket | None:
        for scenario in context.scenario_packets:
            if scenario.title == strategy.title:
                return scenario
        return None

    def _why_selected(
        self,
        context: DecisionContext,
        recommended: SimulationStrategy,
        scenario: ScenarioPacket | None,
    ) -> list[str]:
        reasons = [
            recommended.reason,
            f"It has the strongest projected success path at {recommended.probability}%.",
        ]
        if context.consensus_explanation:
            reasons.append(context.consensus_explanation)
        if scenario:
            reasons.append(
                f"Scenario support: knowledge {round(scenario.knowledge_support * 100)}%, "
                f"memory {round(scenario.historical_support * 100)}%, confidence {round(scenario.confidence * 100)}%."
            )
        if context.risk_analysis:
            reasons.append(f"Risk was assessed as {context.risk_analysis.overall_level}, not ignored.")
        return list(dict.fromkeys(reason for reason in reasons if reason))

    def _why_alternatives_rejected(
        self,
        context: DecisionContext,
        alternatives: list[SimulationStrategy],
    ) -> list[str]:
        rejected = []
        rejected_by_title = {item.title: item.rejection_reason for item in context.rejected_scenarios}
        for strategy in alternatives:
            reason = rejected_by_title.get(strategy.title)
            if reason:
                rejected.append(f"{strategy.title}: {reason}")
            else:
                rejected.append(
                    f"{strategy.title}: lower projected success ({strategy.probability}%) or weaker evidence support."
                )
        rejected.extend(context.rejected_arguments[:3])
        return list(dict.fromkeys(item for item in rejected if item))

    def _traceability(
        self,
        context: DecisionContext,
        recommended: SimulationStrategy,
        scenario: ScenarioPacket | None,
    ) -> dict[str, object]:
        return {
            "decision_type": context.structured_context.decision_type if context.structured_context else None,
            "primary_problem": context.structured_context.primary_problem if context.structured_context else None,
            "business_signals": [
                signal.label for signal in context.structured_context.business_signals
            ]
            if context.structured_context
            else [],
            "selected_strategy": recommended.title,
            "knowledge_packet_ids": [item.id for item in context.knowledge_packets],
            "memory_packet_ids": [item.id for item in context.memory_packets],
            "scenario_packet_id": scenario.id if scenario else None,
            "council_message_turns": [item.turn for item in context.council_timeline],
            "planner_steps": context.executed_steps,
            "skipped_steps": context.skipped_steps,
            "open_questions": context.open_questions,
        }
