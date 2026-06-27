from __future__ import annotations

from app.core.decision_context import DecisionContext
from app.core.decision_core import DecisionCore


class DecisionAgent:
    """
    Backwards-compatible wrapper around DecisionCore.

    New code should use app.core.decision_core.DecisionCore directly.
    """

    name = "Decision Core"

    def __init__(self, decision_core: DecisionCore | None = None) -> None:
        self.decision_core = decision_core or DecisionCore()

    def analyze(self, context: DecisionContext) -> DecisionContext:
        return self.decision_core.synthesize(context)
