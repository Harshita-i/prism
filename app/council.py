from __future__ import annotations

from typing import Any

from app.decision_context import CouncilConsensus, DecisionContext


POSITIVE_OUTCOMES = {"renewed", "expanded", "retained", "stayed", "moved to procurement", "improved capacity", "sla protected"}
NEGATIVE_OUTCOMES = {"churned", "lost", "resigned", "sla breached", "escalated capacity risk"}


class DecisionCouncil:
    """Builds a dynamic council discussion from actual specialist outputs.

    This is not a static transcript. Every message is generated from the current
    Knowledge, Memory, Risk, and Simulation outputs.
    """

    def run(self, state: DecisionContext) -> DecisionContext:
        outputs = state.agent_outputs
        planner = outputs.get("planner")
        context = outputs.get("context")
        knowledge = outputs.get("knowledge")
        memory = outputs.get("memory")
        risk = outputs.get("risk")
        simulation = outputs.get("simulation")

        if planner:
            selected_agents = planner.findings.get("selected_agents", [])
            state.add_message(
                agent="Planner",
                role="Meeting facilitator",
                message_type="opening",
                message=(
                    f"I have enough inputs to open the Decision Council. "
                    f"The council will use {len(selected_agents)} specialist perspectives: {', '.join(selected_agents)}."
                ),
                references=["Planner execution plan"],
                confidence=planner.confidence,
            )

        if context:
            signals = context.findings.get("detected_signals") or context.findings.get("business_context", {}).get("business_signals", [])
            if not signals and "business_context" in context.findings:
                business_context = context.findings["business_context"]
                signals = [
                    *business_context.get("concerns", []),
                    *business_context.get("business_signals", []),
                ]
            signal_text = ", ".join(signals[:5]) if signals else "no explicit signals"
            state.add_message(
                agent="Context",
                role="Business context owner",
                message_type="finding",
                message=f"I framed the decision around {state.entity_name}. The strongest context signals are: {signal_text}.",
                references=["Structured context", "Business record"],
                confidence=context.confidence,
            )

        if knowledge:
            doc_titles = [str(item.get("title")) for item in knowledge.evidence[:3] if item.get("title")]
            rule_count = len(knowledge.findings.get("business_rules", []))
            state.add_message(
                agent="Knowledge",
                role="Policy and playbook expert",
                message_type="finding",
                message=(
                    f"I found {len(knowledge.evidence)} relevant knowledge source(s). "
                    f"{'The strongest sources are: ' + ', '.join(doc_titles) + '.' if doc_titles else 'No strong policy source was retrieved.'} "
                    f"{rule_count} business rule(s) should constrain the recommendation."
                ),
                references=doc_titles,
                confidence=knowledge.confidence,
            )

        if memory:
            successful = []
            failed = []
            for case in memory.evidence:
                outcome = str(case.get("outcome", "")).lower()
                if outcome in POSITIVE_OUTCOMES:
                    successful.append(case)
                elif outcome in NEGATIVE_OUTCOMES:
                    failed.append(case)

            best_success = successful[0] if successful else None
            strongest_failure = failed[0] if failed else None
            refs = [case.get("customer_name", "Historical case") for case in [best_success, strongest_failure] if case]
            memory_sentence = f"I found {len(memory.evidence)} similar historical case(s): {len(successful)} successful and {len(failed)} failed."
            if best_success:
                memory_sentence += f" A useful success pattern is '{best_success.get('recommendation')}' leading to '{best_success.get('outcome')}'."
            if strongest_failure:
                memory_sentence += f" A warning pattern is '{strongest_failure.get('recommendation')}' leading to '{strongest_failure.get('outcome')}'."
            state.add_message(
                agent="Memory",
                role="Historical outcomes expert",
                message_type="evidence",
                message=memory_sentence,
                references=refs,
                confidence=memory.confidence,
            )

        if risk:
            risk_level = risk.findings.get("risk_level", "Unknown")
            risk_score = risk.findings.get("risk_score", "Unknown")
            factors = risk.findings.get("risk_factors", [])
            factor_text = "; ".join(factors[:3]) if factors else "no major risk factors found"
            message_type = "challenge" if risk_level == "High" else "finding"
            state.add_message(
                agent="Risk",
                role="Risk and confidence challenger",
                message_type=message_type,
                message=(
                    f"I rate this as {risk_level} risk with score {risk_score}/100. "
                    f"The recommendation must address: {factor_text}."
                ),
                references=["Risk score", "Risk factors"],
                confidence=risk.confidence,
            )

        top_option: dict[str, Any] | None = None
        alternatives: list[dict[str, Any]] = []
        if simulation:
            options = simulation.findings.get("options", [])
            if options:
                top_option = options[0]
                alternatives = options[1:]
                alt_text = ", ".join(f"{item.get('action')} ({item.get('success_probability')}%)" for item in alternatives[:3])
                state.add_message(
                    agent="Simulation",
                    role="Scenario evaluator",
                    message_type="finding",
                    message=(
                        f"I compared {len(options)} option(s). The strongest option is "
                        f"'{top_option.get('action')}' at {top_option.get('success_probability')}% success. "
                        f"Alternatives considered: {alt_text or 'none'}."
                    ),
                    references=[item.get("action", "Option") for item in options[:3]],
                    confidence=simulation.confidence,
                )

        if top_option and risk:
            risk_level = risk.findings.get("risk_level", "Unknown")
            if risk_level == "High" and top_option.get("risk_level") in {"Low", "Medium"}:
                state.add_message(
                    agent="Risk",
                    role="Risk and confidence challenger",
                    message_type="challenge",
                    message=(
                        f"I support '{top_option.get('action')}' only if the owner is clear: "
                        f"{top_option.get('required_owner')}. The risk is high, so execution ownership matters."
                    ),
                    references=[top_option.get("required_owner", "Owner")],
                    confidence=risk.confidence,
                )

        if top_option and knowledge:
            evidence_titles = [str(item.get("title")) for item in knowledge.evidence[:2] if item.get("title")]
            state.add_message(
                agent="Knowledge",
                role="Policy and playbook expert",
                message_type="support",
                message=(
                    f"The proposed action '{top_option.get('action')}' is consistent with the retrieved guidance. "
                    f"The most relevant evidence is: {', '.join(evidence_titles) if evidence_titles else 'available policy context'}."
                ),
                references=evidence_titles,
                confidence=knowledge.confidence,
            )

        if top_option and memory:
            memory_refs = []
            support_count = 0
            warning_count = 0
            action_words = set(str(top_option.get("action", "")).lower().split())
            for case in memory.evidence:
                case_text = f"{case.get('recommendation', '')} {case.get('summary', '')}".lower()
                overlap = any(word in case_text for word in action_words if len(word) > 4)
                if overlap:
                    memory_refs.append(case.get("customer_name", "Historical case"))
                    if str(case.get("outcome", "")).lower() in POSITIVE_OUTCOMES:
                        support_count += 1
                    elif str(case.get("outcome", "")).lower() in NEGATIVE_OUTCOMES:
                        warning_count += 1
            state.add_message(
                agent="Memory",
                role="Historical outcomes expert",
                message_type="support" if support_count >= warning_count else "challenge",
                message=(
                    f"Historical memory gives {support_count} supporting pattern(s) and {warning_count} warning pattern(s) "
                    f"for actions similar to '{top_option.get('action')}'."
                ),
                references=memory_refs[:3],
                confidence=memory.confidence,
            )

        consensus = self._build_consensus(state, top_option, alternatives)
        state.set_consensus(consensus)
        state.add_message(
            agent="Planner",
            role="Meeting facilitator",
            message_type="consensus",
            message=(
                f"Consensus reached at {consensus.consensus_level} strength. "
                f"Forwarding '{consensus.recommended_action}' to the Decision Core."
            ),
            references=[consensus.recommended_action],
            confidence=consensus.confidence,
        )
        return state

    def _build_consensus(
        self,
        state: DecisionContext,
        top_option: dict[str, Any] | None,
        alternatives: list[dict[str, Any]],
    ) -> CouncilConsensus:
        outputs = state.agent_outputs
        risk = outputs.get("risk")
        knowledge = outputs.get("knowledge")
        memory = outputs.get("memory")

        if not top_option:
            return CouncilConsensus(
                recommended_action="Request more information",
                consensus_level="Weak",
                confidence=45,
                rationale=["Simulation did not produce a clear action."],
                open_questions=["Which action options should be evaluated?"],
            )

        confidence = int(top_option.get("success_probability", 60))
        rationale = [
            f"Simulation ranked '{top_option.get('action')}' highest.",
        ]
        conflicts = []
        open_questions = []

        if knowledge and knowledge.evidence:
            confidence += min(6, len(knowledge.evidence) * 2)
            rationale.append(f"Knowledge Agent retrieved {len(knowledge.evidence)} supporting source(s).")
        else:
            conflicts.append("Limited policy evidence.")

        if memory and memory.evidence:
            confidence += min(6, len(memory.evidence) * 2)
            rationale.append(f"Memory Agent found {len(memory.evidence)} comparable historical case(s).")
        else:
            conflicts.append("Limited historical memory.")

        if risk:
            risk_level = risk.findings.get("risk_level")
            if risk_level == "High":
                confidence -= 8
                conflicts.append("High risk requires clear owner and human review.")
            elif risk_level == "Low":
                confidence += 3
                rationale.append("Risk Agent did not identify severe blockers.")

            for item in risk.missing_information[:3]:
                open_questions.append(item)

        confidence = max(35, min(94, confidence))
        if confidence >= 85 and len(conflicts) <= 1:
            consensus_level = "Strong"
        elif confidence >= 70:
            consensus_level = "Moderate"
        else:
            consensus_level = "Weak"

        rejected = [
            {
                "action": item.get("action"),
                "success_probability": item.get("success_probability"),
                "reason": item.get("reasoning", "Lower expected impact than the recommended action."),
            }
            for item in alternatives
        ]

        return CouncilConsensus(
            recommended_action=str(top_option.get("action")),
            consensus_level=consensus_level,
            confidence=confidence,
            rationale=rationale,
            conflicts_resolved=conflicts,
            rejected_alternatives=rejected,
            open_questions=open_questions,
        )

