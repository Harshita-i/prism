from __future__ import annotations

from datetime import datetime, timezone

from app.core.decision_context import StructuredContext
from app.memory.models import RankedMemory, RetrievedMemory


POSITIVE_OUTCOMES = ["won", "renewed", "stayed", "improved", "protected", "closed", "success", "procurement"]
NEGATIVE_OUTCOMES = ["lost", "churned", "resigned", "breached", "failed", "escalated"]


class MemoryRanker:
    def rank(self, retrieved: list[RetrievedMemory], context: StructuredContext, persona: dict) -> list[RankedMemory]:
        ranked: list[RankedMemory] = []
        signal_count = max(1, len(context.business_signals))
        context_signals = {signal.label.lower() for signal in context.business_signals}

        for item in retrieved:
            decision = item.decision
            overlap = len(context_signals.intersection({signal.lower() for signal in decision.business_signals}))
            business_importance = min(100, 50 + overlap * 12 + (12 if decision.persona_id == persona.get("id") else 0))
            outcome_quality = self._outcome_quality(decision.outcome)
            recency = self._recency(decision.updated_at or decision.created_at)
            evidence_strength = min(100, 40 + len(decision.evidence) * 8 + len(decision.knowledge_references) * 8)
            confidence = self._confidence(item.similarity, outcome_quality, recency, evidence_strength)
            weighted = (
                item.similarity * 0.36
                + (outcome_quality / 100) * 0.22
                + confidence * 0.18
                + (recency / 100) * 0.1
                + (business_importance / 100) * 0.08
                + (evidence_strength / 100) * 0.06
            )
            ranked.append(
                RankedMemory(
                    decision=decision,
                    similarity=item.similarity,
                    outcome_quality=outcome_quality,
                    confidence=confidence,
                    recency=recency,
                    business_importance=business_importance,
                    evidence_strength=evidence_strength,
                    weighted_score=round(max(0.0, min(1.0, weighted)), 4),
                )
            )

        return sorted(ranked, key=lambda item: item.weighted_score, reverse=True)

    def _outcome_quality(self, outcome: str) -> int:
        normalized = outcome.lower()
        if any(term in normalized for term in POSITIVE_OUTCOMES):
            return 92
        if any(term in normalized for term in NEGATIVE_OUTCOMES):
            return 28
        if normalized and normalized != "pending":
            return 62
        return 45

    def _recency(self, date_value: str) -> int:
        if not date_value:
            return 60
        try:
            timestamp = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
        except ValueError:
            return 60
        age_days = max(0, (datetime.now(timezone.utc) - timestamp).days)
        if age_days <= 30:
            return 96
        if age_days <= 180:
            return 86
        if age_days <= 730:
            return 72
        return 55

    def _confidence(self, similarity: float, outcome_quality: int, recency: int, evidence_strength: int) -> float:
        value = (
            similarity * 0.42
            + (outcome_quality / 100) * 0.26
            + (recency / 100) * 0.16
            + (evidence_strength / 100) * 0.16
        )
        return round(max(0.0, min(1.0, value)), 3)
