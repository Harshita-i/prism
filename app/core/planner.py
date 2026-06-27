from __future__ import annotations

from collections.abc import Iterable

from app.core.decision_context import DecisionContext
from app.core.decision_core import DecisionCore
from app.core.executive_council import ExecutiveCouncil
from app.core.interfaces import DecisionAgent
from app.core.workflow_planner import WorkflowPlanner


class Planner:
    """
    Adaptive workflow orchestrator.

    Context extraction always runs first. After structured context exists,
    WorkflowPlanner generates an execution graph and this Planner executes that
    graph instead of a hardcoded specialist sequence.
    """

    def __init__(
        self,
        agents: Iterable[DecisionAgent],
        council: ExecutiveCouncil | None = None,
        decision_core: DecisionCore | None = None,
        workflow_planner: WorkflowPlanner | None = None,
    ) -> None:
        self.agents = {self._agent_key(agent): agent for agent in agents}
        self.council = council or ExecutiveCouncil()
        self.decision_core = decision_core or DecisionCore()
        self.workflow_planner = workflow_planner or WorkflowPlanner()

    def run(self, context: DecisionContext) -> DecisionContext:
        context.metadata.lifecycle_stage = "Evidence Collection"

        context_agent = self.agents.get("context")
        if context_agent is None:
            raise ValueError("Planner requires a Context Agent.")
        context = context_agent.analyze(context)
        self.workflow_planner.mark_executed(
            context,
            "context",
            "Context extraction must run before adaptive planning.",
            confidence=context.structured_context.confidence if context.structured_context else None,
        )

        plan = self.workflow_planner.create_plan(context)

        for step in plan.steps:
            context = self._execute_step(context, step)
            if self.workflow_planner.should_retry(context, step):
                context = self._retry_step(context, step)

        for step in list(plan.skip):
            should_run, reason = self.workflow_planner.should_run_conditional(context, step)
            if should_run:
                context = self._execute_step(context, step, reason=reason)
            elif step not in context.executed_steps:
                self.workflow_planner.mark_skipped(
                    context,
                    step,
                    self._skip_reason(plan, step),
                )

        self.workflow_planner.finalize_metrics(context)

        context.metadata.lifecycle_stage = "Decision Council Discussion"
        context = self.council.discuss(context)

        context.metadata.lifecycle_stage = "Recommendation"
        context = self.decision_core.synthesize(context)

        return context

    def _execute_step(self, context: DecisionContext, step: str, reason: str | None = None) -> DecisionContext:
        agent = self.agents.get(step)
        if agent is None:
            self.workflow_planner.mark_skipped(context, step, f"No registered agent found for {step}.")
            return context
        context = agent.analyze(context)
        confidence = self.workflow_planner.step_confidence(context, step)
        self.workflow_planner.mark_executed(
            context,
            step,
            reason or f"{step} executed from adaptive execution plan.",
            confidence=confidence,
        )
        return context

    def _retry_step(self, context: DecisionContext, step: str) -> DecisionContext:
        agent = self.agents.get(step)
        if agent is None:
            return context
        context = agent.analyze(context)
        confidence = self.workflow_planner.step_confidence(context, step)
        self.workflow_planner.mark_retry(
            context,
            step,
            f"{step} retried because confidence was below threshold.",
            confidence=confidence,
        )
        return context

    def _skip_reason(self, plan, step: str) -> str:
        for item in plan.reasoning:
            if step in item.lower() and "skipped" in item.lower():
                return item
        return f"{step} skipped by adaptive execution plan."

    def _agent_key(self, agent: DecisionAgent) -> str:
        name = getattr(agent, "name", agent.__class__.__name__).lower()
        if "context" in name:
            return "context"
        if "knowledge" in name:
            return "knowledge"
        if "memory" in name:
            return "memory"
        if "risk" in name:
            return "risk"
        if "simulation" in name:
            return "simulation"
        return name.replace(" agent", "").replace(" ", "_")
