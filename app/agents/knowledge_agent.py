from __future__ import annotations

from typing import Any

from app.core.decision_context import DecisionContext, KnowledgeFinding


class KnowledgeAgent:
    name = "Knowledge Agent"

    def __init__(self, storage: Any, limit: int = 3) -> None:
        self.storage = storage
        self.limit = limit

    def analyze(self, context: DecisionContext) -> DecisionContext:
        structured = self._structured(context)
        query = f"{context.metadata.persona_id} {context.metadata.domain} {structured.retrieval_query()}"
        docs = self.storage.query_knowledge(query, limit=self.limit)

        context.retrieved_knowledge = [
            KnowledgeFinding(
                id=doc["id"],
                title=doc["title"],
                source_type=doc["source_type"],
                domain=doc["domain"],
                excerpt=doc["excerpt"],
                score=float(doc.get("score", 0)),
                constraints=self._constraints_from(doc),
            )
            for doc in docs
        ]
        return context

    def _structured(self, context: DecisionContext):
        if context.structured_context is None:
            raise ValueError("KnowledgeAgent requires structured_context.")
        return context.structured_context

    def _constraints_from(self, doc: dict[str, Any]) -> list[str]:
        excerpt = doc.get("excerpt", "")
        sentences = [item.strip() for item in excerpt.split(".") if item.strip()]
        return sentences[:2]
