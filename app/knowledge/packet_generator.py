from __future__ import annotations

import re
from collections import defaultdict

from app.core.decision_context import KnowledgePacket, StructuredContext
from app.knowledge.models import RankedEvidence


class KnowledgePacketGenerator:
    def generate(
        self,
        ranked: list[RankedEvidence],
        context: StructuredContext,
        persona: dict,
        limit: int = 4,
    ) -> list[KnowledgePacket]:
        grouped: dict[str, list[RankedEvidence]] = defaultdict(list)
        for item in ranked:
            grouped[item.chunk.document_id].append(item)

        packets: list[KnowledgePacket] = []
        for document_id, items in grouped.items():
            best = items[0]
            combined_excerpt = " ".join(item.chunk.text for item in items[:2])
            supports = self._supports(combined_excerpt, context, persona)
            packet = KnowledgePacket(
                id=f"kp-{document_id}",
                title=best.chunk.title,
                finding=self._finding(combined_excerpt, supports, context),
                importance=max(item.business_importance for item in items),
                confidence=round(max(item.confidence for item in items), 3),
                relevance=round(max(item.relevance for item in items), 3),
                policy_priority=max(item.policy_priority for item in items),
                freshness=max(item.freshness for item in items),
                duplicate_score=round(sum(item.duplicate_score for item in items) / max(1, len(items)), 3),
                weighted_score=round(max(item.weighted_score for item in items), 4),
                supports=supports,
                constraints=self._constraints(combined_excerpt),
                source=best.chunk.title,
                source_type=best.chunk.source_type,
                domain=best.chunk.domain,
                document_id=document_id,
                chunk_ids=[item.chunk.id for item in items[:3]],
                evidence_excerpt=self._excerpt(combined_excerpt),
            )
            packets.append(packet)

        return sorted(packets, key=lambda item: item.weighted_score, reverse=True)[:limit]

    def _supports(self, text: str, context: StructuredContext, persona: dict) -> list[str]:
        normalized = text.lower()
        supports: list[str] = []

        for signal in context.business_signals:
            terms = [term for term in signal.label.lower().replace("-", " ").split() if len(term) > 2]
            if signal.label.lower() in normalized or any(term in normalized for term in terms):
                supports.append(signal.label)

        for action in persona.get("actions", []):
            action_name = action.get("action", "")
            drivers = action.get("decision_drivers", [])
            if any(driver.lower() in normalized for driver in drivers):
                supports.append(action_name)

        return list(dict.fromkeys(supports))[:5]

    def _finding(self, text: str, supports: list[str], context: StructuredContext) -> str:
        sentences = self._sentences(text)
        priority_terms = ["must", "should", "require", "before", "policy", "approval", "recommend"]
        for sentence in sentences:
            lowered = sentence.lower()
            if any(term in lowered for term in priority_terms):
                return sentence
        if supports:
            return f"Evidence supports {supports[0]} for {context.decision_type}."
        return sentences[0] if sentences else f"Relevant evidence found for {context.decision_type}."

    def _constraints(self, text: str) -> list[str]:
        constraints = []
        for sentence in self._sentences(text):
            lowered = sentence.lower()
            if any(term in lowered for term in ["must", "require", "approval", "should", "before", "only when"]):
                constraints.append(sentence)
        return constraints[:3]

    def _sentences(self, text: str) -> list[str]:
        clean = " ".join(text.split())
        return [item.strip() for item in re.split(r"(?<=[.!?])\s+", clean) if item.strip()]

    def _excerpt(self, text: str, max_chars: int = 360) -> str:
        clean = " ".join(text.split())
        if len(clean) <= max_chars:
            return clean
        return clean[: max_chars - 3].rstrip() + "..."
