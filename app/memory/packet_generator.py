from __future__ import annotations

from collections import Counter, defaultdict

from app.core.decision_context import MemoryInsight, MemoryPacket, StructuredContext
from app.memory.models import RankedMemory
from app.memory.ranker import NEGATIVE_OUTCOMES, POSITIVE_OUTCOMES


class MemoryPacketGenerator:
    def generate(self, ranked: list[RankedMemory], context: StructuredContext, limit: int = 5) -> list[MemoryPacket]:
        packets: list[MemoryPacket] = []
        for item in ranked[:limit]:
            decision = item.decision
            packets.append(
                MemoryPacket(
                    id=f"mp-{decision.id}",
                    title=decision.title,
                    similarity=round(item.similarity, 3),
                    outcome=decision.outcome,
                    outcome_quality=item.outcome_quality,
                    winning_strategy=decision.recommendation or "Unknown strategy",
                    confidence=item.confidence,
                    recency=item.recency,
                    business_importance=item.business_importance,
                    evidence_strength=item.evidence_strength,
                    weighted_score=item.weighted_score,
                    reason=self._reason(item, context),
                    source_decision=decision.id,
                    persona_id=decision.persona_id,
                    decision_type=decision.decision_type,
                    business_signals=decision.business_signals,
                    knowledge_references=decision.knowledge_references,
                    simulation_references=[str(row.get("action", "")) for row in decision.simulation_results[:3]],
                    explainability=self._explainability(item, context),
                )
            )
        return packets

    def patterns(self, packets: list[MemoryPacket]) -> tuple[list[MemoryInsight], list[MemoryInsight]]:
        wins = [packet for packet in packets if self._positive(packet.outcome)]
        failures = [packet for packet in packets if self._negative(packet.outcome)]
        return self._strategy_patterns(wins, "Winning pattern"), self._strategy_patterns(failures, "Failure pattern")

    def _strategy_patterns(self, packets: list[MemoryPacket], label: str) -> list[MemoryInsight]:
        grouped: dict[str, list[MemoryPacket]] = defaultdict(list)
        for packet in packets:
            grouped[packet.winning_strategy].append(packet)

        insights: list[MemoryInsight] = []
        for strategy, items in grouped.items():
            insights.append(
                MemoryInsight(
                    label=strategy,
                    count=len(items),
                    evidence=[item.source_decision for item in items],
                    summary=f"{label}: {strategy} appeared in {len(items)} similar historical decision(s).",
                )
            )
        return sorted(insights, key=lambda item: item.count, reverse=True)[:4]

    def _reason(self, item: RankedMemory, context: StructuredContext) -> str:
        signal_overlap = set(signal.lower() for signal in item.decision.business_signals).intersection(
            signal.label.lower() for signal in context.business_signals
        )
        if signal_overlap:
            return f"Matched business signal(s): {', '.join(sorted(signal_overlap))}."
        return f"Matched persona, decision type, and structured business context with similarity {item.similarity:.2f}."

    def _explainability(self, item: RankedMemory, context: StructuredContext) -> str:
        return (
            f"Remembered because it shares persona '{item.decision.persona_id}', decision type "
            f"'{item.decision.decision_type}', outcome '{item.decision.outcome}', and similar business signals."
        )

    def _positive(self, outcome: str) -> bool:
        normalized = outcome.lower()
        return any(term in normalized for term in POSITIVE_OUTCOMES)

    def _negative(self, outcome: str) -> bool:
        normalized = outcome.lower()
        return any(term in normalized for term in NEGATIVE_OUTCOMES)
