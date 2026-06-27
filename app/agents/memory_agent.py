from __future__ import annotations

from typing import Any

from app.core.decision_context import DecisionContext, MemoryFinding


class MemoryAgent:
    name = "Memory Agent"

    def __init__(self, storage: Any, limit: int = 4) -> None:
        self.storage = storage
        self.limit = limit

    def analyze(self, context: DecisionContext) -> DecisionContext:
        structured = self._structured(context)
        query = f"{context.metadata.persona_id} {context.metadata.domain} {structured.retrieval_query()}"
        cases = self.storage.query_memory(query, limit=self.limit)

        context.historical_memory = [
            MemoryFinding(
                id=case["id"],
                entity_name=case["customer_name"],
                problem=case["problem"],
                recommendation=case["recommendation"],
                outcome=case["outcome"],
                summary=case["summary"],
                relevance=float(case.get("score", 0)),
                lesson=self._lesson(case),
            )
            for case in cases
        ]
        return context

    def _structured(self, context: DecisionContext):
        if context.structured_context is None:
            raise ValueError("MemoryAgent requires structured_context.")
        return context.structured_context

    def _lesson(self, case: dict[str, Any]) -> str:
        outcome = str(case.get("outcome", ""))
        recommendation = str(case.get("recommendation", ""))
        summary = str(case.get("summary", ""))
        return f"Past recommendation '{recommendation}' led to outcome '{outcome}'. {summary}"
