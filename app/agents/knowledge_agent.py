from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.decision_context import DecisionContext, KnowledgeFinding
from app.knowledge.engine import KnowledgeEngine


class KnowledgeAgent:
    name = "Knowledge Agent"

    def __init__(self, storage: Any, limit: int = 4, engine: KnowledgeEngine | None = None) -> None:
        self.storage = storage
        self.limit = limit
        root = Path(__file__).resolve().parents[2]
        self.engine = engine or KnowledgeEngine(storage=storage, root=root)

    def analyze(self, context: DecisionContext) -> DecisionContext:
        structured = self._structured(context)
        packets = self.engine.retrieve_packets(structured, context.persona, limit=self.limit)
        context.knowledge_packets = packets

        context.retrieved_knowledge = [
            KnowledgeFinding(
                id=packet.id,
                title=packet.title,
                source_type=packet.source_type,
                domain=packet.domain,
                excerpt=packet.finding,
                score=packet.weighted_score,
                constraints=packet.constraints,
            )
            for packet in packets
        ]
        context.llm_metadata["knowledge_engine"] = self.engine.metadata
        return context

    def _structured(self, context: DecisionContext):
        if context.structured_context is None:
            raise ValueError("KnowledgeAgent requires structured_context.")
        return context.structured_context
