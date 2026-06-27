from __future__ import annotations

from typing import Any

from app.core.decision_context import DecisionContext, MemoryPacket, StructuredContext
from app.memory.models import ArchivedDecision, RetrievedMemory
from app.memory.packet_generator import MemoryPacketGenerator
from app.memory.ranker import MemoryRanker
from app.utils import score_text


class MemoryEngine:
    def __init__(
        self,
        storage: Any,
        ranker: MemoryRanker | None = None,
        packet_generator: MemoryPacketGenerator | None = None,
    ) -> None:
        self.storage = storage
        self.ranker = ranker or MemoryRanker()
        self.packet_generator = packet_generator or MemoryPacketGenerator()
        self.metadata: dict[str, Any] = {}

    def retrieve_packets(
        self,
        context: StructuredContext,
        persona: dict,
        *,
        limit: int = 5,
        expanded: bool = False,
    ) -> tuple[list[MemoryPacket], dict[str, Any]]:
        candidates = self._load_candidates()
        query = self._query(context, persona, expanded=expanded)
        retrieved = self._similar(candidates, query, persona, expanded=expanded)
        ranked = self.ranker.rank(retrieved, context, persona)
        packets = self.packet_generator.generate(ranked, context, limit=limit)
        winning, failure = self.packet_generator.patterns(packets)
        confidence = max((packet.confidence for packet in packets), default=0.0)
        coverage = min(1.0, len(packets) / max(1, limit))
        metadata = {
            "query": query,
            "candidate_count": len(candidates),
            "retrieved_count": len(retrieved),
            "packet_count": len(packets),
            "confidence": round(confidence, 3),
            "coverage": round(coverage, 3),
            "expanded": expanded,
            "winning_patterns": [item.model_dump() for item in winning],
            "failure_patterns": [item.model_dump() for item in failure],
        }
        self.metadata = metadata
        return packets, metadata

    def update_context(self, context: DecisionContext, packets: list[MemoryPacket], metadata: dict[str, Any]) -> DecisionContext:
        winning, failure = self.packet_generator.patterns(packets)
        context.memory_packets = packets
        context.winning_patterns = winning
        context.failure_patterns = failure
        context.historical_evidence = [packet.model_dump() for packet in packets]
        context.memory_confidence = float(metadata.get("confidence", 0.0))
        context.llm_metadata["memory_engine"] = metadata
        return context

    def archive_decision(self, decision: dict[str, Any]) -> None:
        if not hasattr(self.storage, "archive_decision"):
            return
        card = decision.get("card") or {}
        input_payload = decision.get("input") or {}
        structured_context = card.get("structured_context") or {}
        recommendation = card.get("recommendation") or {}
        consensus = card.get("consensus") or {}
        knowledge_packets = card.get("knowledge_packets") or []
        archive_record = {
            "id": decision["id"],
            "title": decision["title"],
            "persona_id": input_payload.get("persona_id", "unknown"),
            "persona_label": input_payload.get("persona_id", "unknown"),
            "domain": decision["domain"],
            "decision_type": input_payload.get("decision_type", structured_context.get("decision_type", "")),
            "entity_name": decision["customer_name"],
            "primary_problem": structured_context.get("primary_problem", decision["title"]),
            "urgency": structured_context.get("urgency", "Medium"),
            "sentiment": structured_context.get("sentiment", "Neutral"),
            "business_signals": [signal.get("label", "") for signal in structured_context.get("business_signals", [])],
            "recommendation": recommendation.get("action", ""),
            "alternatives": card.get("alternatives", []),
            "decision_matrix": card.get("decision_matrix", []),
            "evidence": card.get("evidence", []),
            "confidence": card.get("confidence", 0),
            "outcome": (decision.get("outcome") or {}).get("outcome", "Pending"),
            "outcome_notes": (decision.get("outcome") or {}).get("notes", ""),
            "knowledge_references": [packet.get("id", "") for packet in knowledge_packets],
            "simulation_results": card.get("decision_matrix", []),
            "planner_reasoning": card.get("planner_reasoning", []),
            "council_consensus": consensus,
            "created_at": decision.get("created_at", ""),
            "updated_at": decision.get("updated_at", ""),
        }
        self.storage.archive_decision(archive_record)

    def _load_candidates(self) -> list[ArchivedDecision]:
        records: list[dict[str, Any]] = []
        if hasattr(self.storage, "list_archived_decisions"):
            records.extend(self.storage.list_archived_decisions())
        if hasattr(self.storage, "list_legacy_memory_cases"):
            records.extend(self.storage.list_legacy_memory_cases())

        candidates: list[ArchivedDecision] = []
        for record in records:
            try:
                candidates.append(ArchivedDecision.model_validate(record))
            except Exception:
                continue
        return candidates

    def _query(self, context: StructuredContext, persona: dict, *, expanded: bool) -> str:
        parts = [
            persona.get("id", ""),
            persona.get("domain", ""),
            persona.get("decision_type", ""),
            context.primary_problem,
            context.decision_type,
            context.urgency,
            context.sentiment,
            *context.entities,
            *[signal.label for signal in context.business_signals],
        ]
        if expanded:
            parts.extend(context.stakeholders)
        return " ".join(str(part) for part in parts if part)

    def _similar(
        self,
        candidates: list[ArchivedDecision],
        query: str,
        persona: dict,
        *,
        expanded: bool,
    ) -> list[RetrievedMemory]:
        retrieved: list[RetrievedMemory] = []
        for decision in candidates:
            if not expanded and decision.persona_id != persona.get("id"):
                continue
            similarity = score_text(query, decision.searchable_text())
            if decision.persona_id == persona.get("id"):
                similarity += 0.12
            if decision.decision_type == persona.get("decision_type"):
                similarity += 0.08
            similarity = round(min(1.0, similarity), 4)
            if similarity > 0.08:
                retrieved.append(RetrievedMemory(decision=decision, similarity=similarity))
        return sorted(retrieved, key=lambda item: item.similarity, reverse=True)[:10]
