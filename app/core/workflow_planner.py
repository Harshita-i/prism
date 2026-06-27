from __future__ import annotations

from app.core.decision_context import (
    DecisionContext,
    ExecutionCondition,
    ExecutionMetrics,
    ExecutionNode,
    ExecutionPlan,
    PlannerTimelineEvent,
)


class WorkflowPlanner:
    """
    Adaptive execution planner.

    It does not perform specialist work. It decides which specialists are
    needed, monitors confidence, and records why steps were executed, retried,
    or skipped.
    """

    MIN_KNOWLEDGE_CONFIDENCE = 0.72
    MIN_MEMORY_CONFIDENCE = 0.55

    def create_plan(self, context: DecisionContext) -> ExecutionPlan:
        structured = context.structured_context
        if structured is None:
            raise ValueError("WorkflowPlanner requires structured_context.")

        signal_text = " ".join(signal.label.lower() for signal in structured.business_signals)
        steps: list[str] = []
        optional: list[str] = []
        skip: list[str] = []
        conditional: list[ExecutionCondition] = []
        reasoning: list[str] = []

        steps.append("knowledge")
        reasoning.append("Knowledge selected because every enterprise decision needs policy, playbook, or guideline grounding.")

        memory_needed = self._memory_needed(context, signal_text)
        if memory_needed:
            steps.append("memory")
            reasoning.append("Memory selected because the decision benefits from historical cases and outcome patterns.")
        else:
            optional.append("memory")
            skip.append("memory")
            reasoning.append("Memory skipped because the decision appears routine and structured confidence is high.")

        risk_needed = self._risk_needed(context, signal_text)
        if risk_needed:
            steps.append("risk")
            reasoning.append("Risk selected because urgency, sentiment, or business signals indicate meaningful downside.")
        else:
            optional.append("risk")
            skip.append("risk")
            reasoning.append("Risk skipped because urgency is low and no high-severity signals were detected.")

        simulation_needed = self._simulation_needed(context, signal_text)
        if simulation_needed:
            steps.append("simulation")
            reasoning.append("Simulation selected because the decision may require comparing multiple action paths.")
        else:
            optional.append("simulation")
            skip.append("simulation")
            reasoning.append("Simulation initially skipped because risk is low or one action path is sufficient.")

        conditional.extend(
            [
                ExecutionCondition(
                    condition="knowledge.confidence < 0.72",
                    execute="knowledge_retry",
                    reason="Retrieve more evidence when Knowledge Packet confidence is weak.",
                ),
                ExecutionCondition(
                    condition="memory.confidence < 0.55 and memory was executed",
                    execute="memory_retry",
                    reason="Expand memory search when historical relevance is weak.",
                ),
                ExecutionCondition(
                    condition="risk.level in ['High', 'Critical'] and simulation not executed",
                    execute="simulation",
                    reason="Run simulation when risk analysis reveals high downside.",
                ),
            ]
        )

        graph = self._graph(steps, optional, conditional)
        plan = ExecutionPlan(
            steps=steps,
            optional=optional,
            conditional=conditional,
            skip=skip,
            graph=graph,
            reasoning=reasoning,
        )
        context.execution_plan = plan
        context.planner_reasoning = reasoning
        for node in graph:
            context.planner_timeline.append(
                PlannerTimelineEvent(step=node.id, status="planned", reason=node.reason)
            )
        return plan

    def should_retry(self, context: DecisionContext, step: str) -> bool:
        if step == "knowledge":
            confidence = self.knowledge_confidence(context)
            return 0 < confidence < self.MIN_KNOWLEDGE_CONFIDENCE
        if step == "memory":
            confidence = self.memory_confidence(context)
            return 0 < confidence < self.MIN_MEMORY_CONFIDENCE
        return False

    def should_run_conditional(self, context: DecisionContext, step: str) -> tuple[bool, str]:
        if step == "simulation" and "simulation" in context.skipped_steps:
            risk = context.risk_analysis
            if risk and risk.overall_level in {"High", "Critical"}:
                return True, "Simulation added because risk analysis returned high or critical risk."
        return False, ""

    def mark_executed(self, context: DecisionContext, step: str, reason: str, confidence: float | None = None) -> None:
        if step not in context.executed_steps:
            context.executed_steps.append(step)
        if step in context.skipped_steps:
            context.skipped_steps.remove(step)
        context.planner_timeline.append(
            PlannerTimelineEvent(step=step, status="executed", reason=reason, confidence=confidence)
        )
        if confidence is not None:
            context.confidence_timeline.append({"step": step, "confidence": confidence})

    def mark_retry(self, context: DecisionContext, step: str, reason: str, confidence: float | None = None) -> None:
        retry_step = f"{step}_retry"
        context.executed_steps.append(retry_step)
        context.planner_timeline.append(
            PlannerTimelineEvent(step=retry_step, status="retried", reason=reason, confidence=confidence)
        )
        if confidence is not None:
            context.confidence_timeline.append({"step": retry_step, "confidence": confidence})

    def mark_skipped(self, context: DecisionContext, step: str, reason: str) -> None:
        if step not in context.skipped_steps:
            context.skipped_steps.append(step)
        context.planner_timeline.append(
            PlannerTimelineEvent(step=step, status="skipped", reason=reason)
        )

    def finalize_metrics(self, context: DecisionContext) -> None:
        confidences = [
            float(item["confidence"])
            for item in context.confidence_timeline
            if item.get("confidence") is not None
        ]
        retries = len([step for step in context.executed_steps if step.endswith("_retry")])
        context.execution_metrics = ExecutionMetrics(
            planned_steps=len(context.execution_plan.graph) if context.execution_plan else 0,
            executed_steps=len(context.executed_steps),
            skipped_steps=len(context.skipped_steps),
            retries=retries,
            average_confidence=round(sum(confidences) / len(confidences), 3) if confidences else 0.0,
        )

    def step_confidence(self, context: DecisionContext, step: str) -> float | None:
        if step == "knowledge":
            return self.knowledge_confidence(context)
        if step == "memory":
            return self.memory_confidence(context)
        if step == "risk":
            return self.risk_confidence(context)
        if step == "simulation":
            return self.simulation_confidence(context)
        return None

    def knowledge_confidence(self, context: DecisionContext) -> float:
        if not context.knowledge_packets:
            return 0.0
        return max(packet.confidence for packet in context.knowledge_packets)

    def memory_confidence(self, context: DecisionContext) -> float:
        return context.memory_confidence

    def risk_confidence(self, context: DecisionContext) -> float:
        if context.risk_analysis is None:
            return 0.0
        missing_penalty = min(0.25, len(context.risk_analysis.missing_information) * 0.04)
        return round(max(0.45, 0.86 - missing_penalty), 3)

    def simulation_confidence(self, context: DecisionContext) -> float:
        if not context.simulations:
            return 0.0
        return round(max(strategy.probability for strategy in context.simulations) / 100, 3)

    def _memory_needed(self, context: DecisionContext, signal_text: str) -> bool:
        structured = context.structured_context
        assert structured is not None
        return (
            structured.confidence < 0.86
            or structured.urgency in {"High", "Critical"}
            or any(term in signal_text for term in ["renewal", "retention", "supplier", "deal", "capacity"])
        )

    def _risk_needed(self, context: DecisionContext, signal_text: str) -> bool:
        structured = context.structured_context
        assert structured is not None
        return (
            structured.urgency in {"Medium", "High", "Critical"}
            or structured.sentiment in {"Negative", "Mixed"}
            or any(signal.severity in {"High", "Critical"} for signal in structured.business_signals)
        )

    def _simulation_needed(self, context: DecisionContext, signal_text: str) -> bool:
        structured = context.structured_context
        assert structured is not None
        return (
            structured.urgency in {"High", "Critical"}
            or any(term in signal_text for term in ["competitor", "external", "budget", "sla", "capacity", "workload"])
        )

    def _graph(
        self,
        steps: list[str],
        optional: list[str],
        conditional: list[ExecutionCondition],
    ) -> list[ExecutionNode]:
        graph: list[ExecutionNode] = []
        previous = "context"
        for step in steps:
            graph.append(
                ExecutionNode(
                    id=step,
                    agent=step,
                    required=True,
                    depends_on=[previous],
                    reason=f"{step} selected by adaptive workflow plan.",
                )
            )
            previous = step
        for step in optional:
            graph.append(
                ExecutionNode(
                    id=step,
                    agent=step,
                    required=False,
                    depends_on=["context"],
                    reason=f"{step} is optional for this decision and may be skipped or conditionally executed.",
                )
            )
        for item in conditional:
            graph.append(
                ExecutionNode(
                    id=item.execute,
                    agent=item.execute.replace("_retry", ""),
                    required=False,
                    depends_on=[item.execute.replace("_retry", "")],
                    retry_of=item.execute.replace("_retry", "") if item.execute.endswith("_retry") else None,
                    reason=item.reason,
                )
            )
        return graph
