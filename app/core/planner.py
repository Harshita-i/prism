from __future__ import annotations

from collections.abc import Iterable

from app.core.decision_context import DecisionContext
from app.core.decision_core import DecisionCore
from app.core.executive_council import ExecutiveCouncil
from app.core.interfaces import DecisionAgent


class Planner:
    """
    Meeting facilitator for the Prism decision council.

    Planner does not recommend and does not inspect business semantics. It
    controls execution order, routes the shared blackboard through agents,
    schedules council discussion, and sends the completed context to DecisionCore.
    """

    def __init__(
        self,
        agents: Iterable[DecisionAgent],
        council: ExecutiveCouncil | None = None,
        decision_core: DecisionCore | None = None,
    ) -> None:
        self.agents = list(agents)
        self.council = council or ExecutiveCouncil()
        self.decision_core = decision_core or DecisionCore()

    def run(self, context: DecisionContext) -> DecisionContext:
        context.metadata.lifecycle_stage = "Evidence Collection"

        for agent in self.agents:
            context = agent.analyze(context)

        context.metadata.lifecycle_stage = "Decision Council Discussion"
        context = self.council.discuss(context)

        context.metadata.lifecycle_stage = "Recommendation"
        context = self.decision_core.synthesize(context)

        return context
