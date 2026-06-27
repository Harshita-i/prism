from __future__ import annotations

from typing import Protocol

from app.core.decision_context import Consensus, DecisionContext, SimulationStrategy
from app.llm.service import LLMService


class CouncilGenerator(Protocol):
    def discuss(self, context: DecisionContext) -> DecisionContext:
        """Generate council messages and consensus from completed specialist work."""


class ExecutiveCouncil:
    """
    Dynamic council layer.

    Phase 2 tries Gemini or another provider through LLMService. If that layer
    is disabled or fails, this class falls back to the local structured council.
    """

    def __init__(self, llm_service: LLMService | None = None) -> None:
        self.llm_service = llm_service or LLMService.from_env()

    def discuss(self, context: DecisionContext) -> DecisionContext:
        context.council_messages.clear()
        llm_result = self.llm_service.facilitate_council(context)
        context.llm_metadata["executive_council"] = llm_result.metadata
        if llm_result.value is not None:
            context.council_messages = llm_result.value["messages"]
            context.consensus = llm_result.value["consensus"]
            return context

        context.add_message(
            agent="Planner",
            message_type="clarification",
            message="AI reasoning temporarily unavailable. Showing rule-based reasoning.",
            references=[],
            confidence=70,
        )

        self._knowledge_turn(context)
        self._memory_turn(context)
        self._risk_turn(context)
        self._simulation_turn(context)
        self._challenge_turn(context)
        self._consensus_turn(context)
        return context

    def _knowledge_turn(self, context: DecisionContext) -> None:
        if not context.retrieved_knowledge:
            context.add_message(
                agent="Knowledge Agent",
                message_type="question",
                message="No policy evidence was retrieved, so the council needs human confirmation before treating any action as policy-aligned.",
                references=[],
                confidence=58,
            )
            context.open_questions.append("Confirm which policy or playbook governs this decision.")
            return

        top = context.retrieved_knowledge[0]
        constraints = ", ".join(top.constraints[:2]) if top.constraints else top.excerpt
        context.add_message(
            agent="Knowledge Agent",
            message_type="finding",
            message=f"{top.title} is the strongest knowledge source. It points the council toward: {constraints}",
            references=[top.id],
            confidence=round(min(96, 70 + top.score * 20)),
        )

    def _memory_turn(self, context: DecisionContext) -> None:
        if not context.historical_memory:
            context.add_message(
                agent="Memory Agent",
                message_type="clarification",
                message="No close historical case was found, so the council should rely more heavily on policy and simulation evidence.",
                references=[],
                confidence=60,
            )
            return

        successful = [case for case in context.historical_memory if self._positive_outcome(case.outcome)]
        failed = [case for case in context.historical_memory if not self._positive_outcome(case.outcome)]
        strongest = context.historical_memory[0]
        context.add_message(
            agent="Memory Agent",
            message_type="support" if successful else "challenge",
            message=(
                f"Historical memory found {len(context.historical_memory)} similar case(s): "
                f"{len(successful)} successful and {len(failed)} risky. The closest lesson is: "
                f"{strongest.lesson or strongest.summary}"
            ),
            references=[case.id for case in context.historical_memory[:3]],
            confidence=round(min(94, 66 + strongest.relevance * 22)),
        )

    def _risk_turn(self, context: DecisionContext) -> None:
        risk = context.risk_analysis
        if risk is None:
            context.add_message(
                agent="Risk Agent",
                message_type="question",
                message="Risk analysis is missing, so the council cannot safely move to a final decision.",
                references=[],
                confidence=50,
            )
            context.open_questions.append("Run risk analysis before final recommendation.")
            return

        risk_count = sum(
            len(group)
            for group in [
                risk.business_risks,
                risk.financial_risks,
                risk.operational_risks,
                risk.execution_risks,
                risk.confidence_risks,
            ]
        )
        message_type = "challenge" if risk.overall_level in {"High", "Critical"} else "support"
        context.add_message(
            agent="Risk Agent",
            message_type=message_type,
            message=(
                f"Overall risk is {risk.overall_level} at {risk.score}/100 with {risk_count} risk signal(s). "
                f"The council should avoid strategies that increase execution risk without resolving the main business signals."
            ),
            references=[finding.label for finding in self._all_risks(context)[:4]],
            confidence=84,
        )

        for question in risk.missing_information:
            if question not in context.open_questions:
                context.open_questions.append(question)

    def _simulation_turn(self, context: DecisionContext) -> None:
        if not context.simulations:
            context.add_message(
                agent="Simulation Agent",
                message_type="question",
                message="No strategy simulation exists, so the council cannot compare action paths.",
                references=[],
                confidence=55,
            )
            context.open_questions.append("Generate strategy simulations before decision core synthesis.")
            return

        top = self._top_strategy(context.simulations)
        runner_up = [item for item in context.simulations if item.title != top.title]
        comparison = ""
        if runner_up:
            second = self._top_strategy(runner_up)
            comparison = f" It outperforms {second.title} by {top.probability - second.probability} point(s)."
        context.add_message(
            agent="Simulation Agent",
            message_type="finding",
            message=(
                f"The strongest simulated option is {top.title} at {top.probability}% expected success. "
                f"Reason: {top.reason}.{comparison}"
            ),
            references=[strategy.title for strategy in context.simulations],
            confidence=86,
        )

    def _challenge_turn(self, context: DecisionContext) -> None:
        top = self._top_strategy(context.simulations) if context.simulations else None
        risk = context.risk_analysis
        if top is None or risk is None:
            return

        if top.risk in {"High", "Critical"} and risk.overall_level in {"High", "Critical"}:
            context.add_message(
                agent="Planner",
                message_type="challenge",
                message=(
                    f"{top.title} has strong upside but also {top.risk} strategy risk. "
                    "The council should only forward it if evidence shows the risk is controlled."
                ),
                references=[top.title, risk.overall_level],
                confidence=78,
            )
        elif context.open_questions:
            context.add_message(
                agent="Planner",
                message_type="clarification",
                message=(
                    f"The council has {len(context.open_questions)} open question(s), but available evidence is sufficient "
                    "for a human-review recommendation rather than automatic execution."
                ),
                references=context.open_questions[:3],
                confidence=76,
            )
        else:
            context.add_message(
                agent="Planner",
                message_type="support",
                message="Policy, memory, risk, and simulation findings are aligned enough to ask Decision Core for synthesis.",
                references=[],
                confidence=82,
            )

    def _consensus_turn(self, context: DecisionContext) -> None:
        top = self._top_strategy(context.simulations) if context.simulations else None
        risk = context.risk_analysis
        rationale = []
        disagreements = []

        if context.retrieved_knowledge:
            rationale.append(f"Knowledge source supports the decision path: {context.retrieved_knowledge[0].title}.")
        if context.historical_memory:
            rationale.append(f"Historical memory contributes {len(context.historical_memory)} comparable outcome(s).")
        if risk:
            rationale.append(f"Risk analysis sets overall risk at {risk.overall_level}.")
        if top:
            rationale.append(f"Simulation ranks {top.title} highest at {top.probability}%.")

        if risk and top and top.risk != risk.overall_level:
            disagreements.append(
                f"Strategy risk is {top.risk}, while overall decision risk is {risk.overall_level}; Decision Core should explain this difference."
            )
        if context.open_questions:
            disagreements.append("Some information remains missing and should be visible during human review.")

        confidence = 70
        if top:
            confidence = int((top.probability * 0.55) + ((100 - len(context.open_questions) * 8) * 0.2) + 20)
        confidence = max(50, min(94, confidence))

        context.consensus = Consensus(
            status="Needs More Information" if not top else "Reached",
            level="Strong" if confidence >= 84 and not disagreements else "Moderate" if confidence >= 68 else "Weak",
            preferred_strategy=top.title if top else None,
            rationale=rationale,
            disagreements=disagreements,
            open_questions=context.open_questions,
            confidence=confidence,
        )
        context.add_message(
            agent="Executive Council",
            message_type="consensus",
            message=(
                f"Consensus status: {context.consensus.status}. Preferred strategy: "
                f"{context.consensus.preferred_strategy or 'not ready'}. Confidence: {context.consensus.confidence}%."
            ),
            references=context.consensus.rationale,
            confidence=context.consensus.confidence,
        )

    def _top_strategy(self, strategies: list[SimulationStrategy]) -> SimulationStrategy:
        return sorted(strategies, key=lambda item: item.probability, reverse=True)[0]

    def _positive_outcome(self, outcome: str) -> bool:
        normalized = outcome.lower()
        positive_terms = ["renew", "stayed", "improved", "protected", "closed", "procurement", "success"]
        negative_terms = ["churn", "resign", "lost", "breach", "failed", "escalated"]
        if any(term in normalized for term in negative_terms):
            return False
        return any(term in normalized for term in positive_terms)

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
