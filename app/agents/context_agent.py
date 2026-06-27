from __future__ import annotations

from app.core.context_extractor import ContextExtractor, LLMContextExtractor
from app.core.decision_context import DecisionContext


class ContextAgent:
    name = "Context Agent"

    def __init__(self, extractor: ContextExtractor | None = None) -> None:
        self.extractor = extractor or LLMContextExtractor()

    def analyze(self, context: DecisionContext) -> DecisionContext:
        context.structured_context = self.extractor.extract(context.user_input, context.persona)
        context.llm_metadata["context_extraction"] = getattr(self.extractor, "last_metadata", {})
        context.add_message(
            agent=self.name,
            message_type="finding",
            message=(
                f"Structured context created for {context.metadata.entity_name}: "
                f"{context.structured_context.primary_problem} with {context.structured_context.urgency} urgency."
            ),
            references=[signal.label for signal in context.structured_context.business_signals[:4]],
            confidence=round(context.structured_context.confidence * 100),
        )
        context.user_input = {
            "raw_input_scrubbed": True,
            "decision_type": context.structured_context.decision_type,
            "entity_name": context.metadata.entity_name,
            "persona_id": context.metadata.persona_id,
        }
        return context
