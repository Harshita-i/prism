from __future__ import annotations

from datetime import datetime, timezone

from app.core.decision_context import StructuredContext
from app.knowledge.models import RankedEvidence, RetrievedChunk


SOURCE_PRIORITY = {
    "policy": 100,
    "sop": 92,
    "playbook": 88,
    "guideline": 78,
    "process": 74,
    "pdf": 70,
    "docx": 68,
    "md": 62,
    "txt": 56,
    "document": 55,
}


class EvidenceRanker:
    def rank(
        self,
        retrieved: list[RetrievedChunk],
        context: StructuredContext,
        persona: dict,
    ) -> list[RankedEvidence]:
        ranked: list[RankedEvidence] = []
        seen_titles: dict[str, int] = {}
        signals = [signal.label.lower() for signal in context.business_signals]
        persona_terms = [
            str(persona.get("id", "")).lower(),
            str(persona.get("domain", "")).lower(),
            str(persona.get("decision_type", "")).lower(),
        ]

        for item in retrieved:
            chunk = item.chunk
            duplicate_score = self._duplicate_score(chunk.title, seen_titles)
            business_importance = self._business_importance(chunk.text, signals, persona_terms)
            policy_priority = SOURCE_PRIORITY.get(chunk.source_type.lower(), 55)
            freshness = self._freshness(chunk.effective_date, chunk.expires_at)
            confidence = self._confidence(item.relevance, business_importance, policy_priority, freshness)
            weighted = self._weighted_score(
                relevance=item.relevance,
                business_importance=business_importance,
                confidence=confidence,
                policy_priority=policy_priority,
                freshness=freshness,
                duplicate_score=duplicate_score,
            )
            ranked.append(
                RankedEvidence(
                    chunk=chunk,
                    relevance=item.relevance,
                    business_importance=business_importance,
                    confidence=confidence,
                    policy_priority=policy_priority,
                    freshness=freshness,
                    duplicate_score=duplicate_score,
                    weighted_score=weighted,
                )
            )

        return sorted(ranked, key=lambda item: item.weighted_score, reverse=True)

    def _business_importance(self, text: str, signals: list[str], persona_terms: list[str]) -> int:
        normalized = text.lower()
        score = 45
        for signal in signals:
            signal_terms = [term for term in signal.replace("-", " ").split() if len(term) > 2]
            if signal in normalized:
                score += 12
            elif signal_terms and any(term in normalized for term in signal_terms):
                score += 6

        for term in persona_terms:
            if term and term in normalized:
                score += 5

        if any(term in normalized for term in ["must", "require", "policy", "approval", "should", "before"]):
            score += 8
        return max(0, min(100, score))

    def _duplicate_score(self, title: str, seen_titles: dict[str, int]) -> float:
        key = title.lower().strip()
        count = seen_titles.get(key, 0)
        seen_titles[key] = count + 1
        return min(1.0, count * 0.25)

    def _freshness(self, effective_date: str | None, expires_at: str | None) -> int:
        now = datetime.now(timezone.utc)
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                if expiry < now:
                    return 20
            except ValueError:
                pass

        if not effective_date:
            return 70
        try:
            effective = datetime.fromisoformat(effective_date.replace("Z", "+00:00"))
        except ValueError:
            return 70
        age_days = max(0, (now - effective).days)
        if age_days <= 180:
            return 95
        if age_days <= 730:
            return 82
        return 62

    def _confidence(self, relevance: float, importance: int, priority: int, freshness: int) -> float:
        value = (relevance * 0.42) + ((importance / 100) * 0.28) + ((priority / 100) * 0.2) + ((freshness / 100) * 0.1)
        return round(max(0.0, min(1.0, value)), 3)

    def _weighted_score(
        self,
        *,
        relevance: float,
        business_importance: int,
        confidence: float,
        policy_priority: int,
        freshness: int,
        duplicate_score: float,
    ) -> float:
        weighted = (
            relevance * 0.34
            + (business_importance / 100) * 0.25
            + confidence * 0.2
            + (policy_priority / 100) * 0.14
            + (freshness / 100) * 0.07
        )
        weighted -= duplicate_score * 0.12
        return round(max(0.0, min(1.0, weighted)), 4)
