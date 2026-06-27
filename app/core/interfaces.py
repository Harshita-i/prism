from __future__ import annotations

from typing import Protocol

from app.core.decision_context import DecisionContext


class DecisionAgent(Protocol):
    name: str

    def analyze(self, context: DecisionContext) -> DecisionContext:
        """Read and update the shared DecisionContext blackboard."""
        ...
