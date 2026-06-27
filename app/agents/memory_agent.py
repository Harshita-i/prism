from __future__ import annotations

from typing import Any

from app.core.decision_context import DecisionContext, MemoryFinding
from app.memory.engine import MemoryEngine


class MemoryAgent:
    name = "Memory Agent"

    def __init__(self, storage: Any, limit: int = 5, engine: MemoryEngine | None = None) -> None:
        self.storage = storage
        self.limit = limit
        self.engine = engine or MemoryEngine(storage)
        self.expanded = False

    def analyze(self, context: DecisionContext) -> DecisionContext:
        structured = self._structured(context)
        packets, metadata = self.engine.retrieve_packets(
            structured,
            context.persona,
            limit=self.limit,
            expanded=self.expanded,
        )
        context = self.engine.update_context(context, packets, metadata)
        context.historical_memory = [
            MemoryFinding(
                id=packet.id,
                entity_name=packet.title,
                problem=packet.decision_type,
                recommendation=packet.winning_strategy,
                outcome=packet.outcome,
                summary=packet.reason,
                relevance=packet.similarity,
                lesson=packet.explainability,
            )
            for packet in packets
        ]
        self.expanded = True
        return context

    def _structured(self, context: DecisionContext):
        if context.structured_context is None:
            raise ValueError("MemoryAgent requires structured_context.")
        return context.structured_context
