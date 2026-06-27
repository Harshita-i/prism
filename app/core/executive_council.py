from __future__ import annotations

from typing import Protocol

from app.core.consensus_engine import ConsensusEngine
from app.core.decision_context import DecisionContext
from app.llm.service import LLMService


class CouncilGenerator(Protocol):
    def discuss(self, context: DecisionContext) -> DecisionContext:
        """Generate collaborative council messages and consensus."""


class ExecutiveCouncil:
    """
    Collaborative executive council.

    The council behaves like a moderated meeting. Specialists respond to prior
    messages, challenge assumptions, update confidence, and then ConsensusEngine
    computes agreement strength.
    """

    def __init__(
        self,
        llm_service: LLMService | None = None,
        consensus_engine: ConsensusEngine | None = None,
    ) -> None:
        self.llm_service = llm_service or LLMService.from_env()
        self.consensus_engine = consensus_engine or ConsensusEngine()

    def discuss(self, context: DecisionContext) -> DecisionContext:
        context.council_messages.clear()
        context.council_timeline.clear()
        context.planner_actions.clear()

        llm_result = self.llm_service.facilitate_council(context)
        context.llm_metadata["executive_council"] = llm_result.metadata
        if llm_result.value is not None:
            context.council_messages = llm_result.value["messages"]
            context.council_timeline = list(context.council_messages)
            context.consensus = self.consensus_engine.evaluate(context)
            self._append_consensus_message(context)
            return context

        context.add_message(
            agent="Planner",
            message_type="clarification",
            message="AI reasoning temporarily unavailable. Running collaborative local council.",
            references=[],
            confidence=70,
            confidence_before=70,
            confidence_after=70,
        )
        context.planner_actions.append("Opened fallback collaborative council because LLM council was unavailable.")

        self._knowledge_opens(context)
        self._risk_challenges(context)
        self._memory_responds(context)
        self._scenario_revises(context)
        self._planner_moderates(context)
        context.consensus = self.consensus_engine.evaluate(context)
        self._append_consensus_message(context)
        return context

    def _knowledge_opens(self, context: DecisionContext) -> None:
        if not context.knowledge_packets:
            context.open_questions.append("Confirm which policy or playbook governs this decision.")
            context.add_message(
                agent="Knowledge Agent",
                message_type="question",
                message="I do not have a Knowledge Packet strong enough to ground the decision. Which policy should govern this?",
                confidence=52,
                confidence_before=60,
                confidence_after=52,
            )
            return

        top = context.knowledge_packets[0]
        confidence = round(top.confidence * 100)
        context.add_message(
            agent="Knowledge Agent",
            message_type="evidence",
            message=(
                f"I am grounding the council in {top.title}. Finding: {top.finding} "
                f"This supports {', '.join(top.supports[:3]) or 'the leading decision path'}."
            ),
            references=[top.id],
            evidence_references=[top.id, *top.chunk_ids[:2]],
            supports=top.supports[:3],
            confidence=confidence,
            confidence_before=max(40, confidence - 8),
            confidence_after=confidence,
        )

    def _risk_challenges(self, context: DecisionContext) -> None:
        risk = context.risk_analysis
        winning = context.winning_scenario
        if risk is None:
            context.open_questions.append("Risk analysis is missing.")
            context.add_message(
                agent="Risk Agent",
                message_type="question",
                message="I cannot validate council safety because risk analysis is missing.",
                confidence=50,
                confidence_before=60,
                confidence_after=50,
            )
            return

        challenge_refs = [finding.label for finding in self._all_risks(context)[:4]]
        if winning and risk.overall_level in {"High", "Critical"} and winning.business_risk in {"Low", "Medium"}:
            message = (
                f"I challenge the council to explain why overall risk is {risk.overall_level} while the leading scenario "
                f"({winning.title}) has {winning.business_risk} scenario risk. The recommendation must show mitigation."
            )
        else:
            message = (
                f"Risk is {risk.overall_level} with score {risk.score}/100. I am watching execution and confidence risk, "
                "but I do not see a blocker if mitigation is explicit."
            )
        confidence = max(55, min(92, 100 - risk.score + 35))
        context.add_message(
            agent="Risk Agent",
            message_type="challenge" if risk.overall_level in {"High", "Critical"} else "clarification",
            message=message,
            references=challenge_refs,
            challenges=[winning.id] if winning else [],
            confidence=confidence,
            confidence_before=max(40, confidence - 10),
            confidence_after=confidence,
        )

    def _memory_responds(self, context: DecisionContext) -> None:
        if not context.memory_packets:
            context.add_message(
                agent="Memory Agent",
                message_type="clarification",
                message="I do not have close organizational memory, so I will not overstate historical support.",
                confidence=58,
                confidence_before=65,
                confidence_after=58,
                reply_to=2 if len(context.council_messages) >= 2 else None,
            )
            return

        top = context.memory_packets[0]
        failure_note = f" I also see a failure caution: {context.failure_patterns[0].summary}" if context.failure_patterns else ""
        confidence = round(top.confidence * 100)
        context.add_message(
            agent="Memory Agent",
            message_type="support",
            message=(
                f"I respond to Risk with historical experience: {top.title} had outcome '{top.outcome}'. "
                f"Lesson: {top.reason}.{failure_note}"
            ),
            references=[top.id, top.source_decision],
            evidence_references=[top.id, top.source_decision],
            supports=[context.winning_scenario.id] if context.winning_scenario else [],
            challenges=[context.rejected_scenarios[0].id] if context.rejected_scenarios else [],
            confidence=confidence,
            confidence_before=max(40, confidence - 9),
            confidence_after=confidence,
            reply_to=2 if len(context.council_messages) >= 2 else None,
        )

    def _scenario_revises(self, context: DecisionContext) -> None:
        winning = context.winning_scenario
        if winning is None:
            context.open_questions.append("Scenario ranking is missing.")
            context.add_message(
                agent="Simulation Agent",
                message_type="question",
                message="I need Scenario Packets before I can compare future outcomes.",
                confidence=50,
                confidence_before=60,
                confidence_after=50,
            )
            return

        rejected = context.rejected_scenarios[0] if context.rejected_scenarios else None
        confidence = round(winning.confidence * 100)
        revision = (
            f"I updated the projection around {winning.title}: success {round(winning.success_probability * 100)}%, "
            f"cost {winning.financial_cost}, time to impact {winning.time_to_impact}. "
        )
        if rejected:
            revision += f"I reject {rejected.title} because {rejected.rejection_reason or 'its weighted score was weaker'}."
        context.add_message(
            agent="Simulation Agent",
            message_type="revision",
            message=revision,
            references=[winning.id, *( [rejected.id] if rejected else [] )],
            evidence_references=[winning.id],
            supports=[winning.id],
            challenges=[rejected.id] if rejected else [],
            confidence=confidence,
            confidence_before=max(40, confidence - 6),
            confidence_after=confidence,
            reply_to=len(context.council_messages),
        )

    def _planner_moderates(self, context: DecisionContext) -> None:
        open_count = len(context.open_questions)
        action = (
            "Planner requested human-visible caveats for open questions."
            if open_count
            else "Planner closed discussion and sent evidence to Consensus Engine."
        )
        context.planner_actions.append(action)
        context.add_message(
            agent="Planner",
            message_type="clarification" if open_count else "support",
            message=(
                f"I have heard Knowledge, Risk, Memory, and Simulation. Open questions: {open_count}. "
                "I am forwarding the discussion to Consensus Engine for agreement scoring."
            ),
            references=context.open_questions[:3],
            supports=[context.winning_scenario.id] if context.winning_scenario else [],
            confidence=78 if open_count else 86,
            confidence_before=72,
            confidence_after=78 if open_count else 86,
            reply_to=len(context.council_messages),
        )

    def _append_consensus_message(self, context: DecisionContext) -> None:
        consensus = context.consensus
        if consensus is None:
            return
        context.add_message(
            agent="Consensus Engine",
            message_type="consensus",
            message=(
                f"Consensus {consensus.status}. Strength={consensus.strength}. "
                f"Agreement score={consensus.agreement_score}/100. Preferred strategy: "
                f"{consensus.preferred_strategy or 'not ready'}. {consensus.explanation}"
            ),
            references=consensus.rationale[:4],
            evidence_references=context.supporting_evidence,
            supports=[context.winning_scenario.id] if context.winning_scenario else [],
            challenges=context.rejected_arguments[:3],
            confidence=consensus.confidence,
            confidence_before=max(40, consensus.confidence - 5),
            confidence_after=consensus.confidence,
            reply_to=len(context.council_messages) if context.council_messages else None,
        )

    def _all_risks(self, context: DecisionContext):
        if context.risk_analysis is None:
            return []
        return [
            *context.risk_analysis.business_risks,
            *context.risk_analysis.financial_risks,
            *context.risk_analysis.operational_risks,
            *context.risk_analysis.execution_risks,
            *context.risk_analysis.confidence_risks,
        ]
