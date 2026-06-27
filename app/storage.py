from __future__ import annotations

import json
import sqlite3
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

from app.models import utc_now
from app.seed import DEFAULT_KNOWLEDGE_DOCS, DEFAULT_MEMORY_CASES
from app.utils import compact_text, excerpt, score_text


class SQLiteStorage:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        if str(db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    customer_name TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    lifecycle_stage TEXT NOT NULL,
                    input_json TEXT NOT NULL,
                    card_json TEXT,
                    review_json TEXT,
                    outcome_json TEXT
                );

                CREATE TABLE IF NOT EXISTS knowledge_docs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    content TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memory_cases (
                    id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    industry TEXT NOT NULL,
                    segment TEXT NOT NULL,
                    problem TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    confidence INTEGER NOT NULL,
                    tags_json TEXT NOT NULL,
                    summary TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS decision_archive (
                    id TEXT PRIMARY KEY,
                    archived_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS decision_versions (
                    id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    change_type TEXT NOT NULL,
                    change_log_json TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS decision_lifecycle (
                    id TEXT PRIMARY KEY,
                    decision_id TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    notes TEXT NOT NULL
                );
                """
            )

    def seed_if_empty(self) -> None:
        with self.connect() as connection:
            connection.executemany(
                """
                INSERT OR REPLACE INTO knowledge_docs
                (id, title, source_type, domain, tags_json, content)
                VALUES (:id, :title, :source_type, :domain, :tags_json, :content)
                """,
                [
                    {
                        **doc,
                        "tags_json": json.dumps(doc["tags"]),
                    }
                    for doc in DEFAULT_KNOWLEDGE_DOCS
                ],
            )

            connection.executemany(
                """
                INSERT OR REPLACE INTO memory_cases
                (id, customer_name, industry, segment, problem, recommendation, outcome, confidence, tags_json, summary)
                VALUES (:id, :customer_name, :industry, :segment, :problem, :recommendation, :outcome, :confidence, :tags_json, :summary)
                """,
                [
                    {
                        **case,
                        "tags_json": json.dumps(case["tags"]),
                    }
                    for case in DEFAULT_MEMORY_CASES
                ],
            )

    def create_decision(self, payload: dict[str, Any]) -> dict[str, Any]:
        decision_id = str(uuid.uuid4())
        now = utc_now()
        record = {
            "id": decision_id,
            "created_at": now,
            "updated_at": now,
            "title": payload["title"],
            "customer_name": payload.get("customer_name") or payload.get("crm_record", {}).get("customer_name", "Unknown Entity"),
            "domain": payload.get("domain", "Business Operations"),
            "lifecycle_stage": "Draft",
            "input_json": json.dumps(payload),
            "card_json": None,
            "review_json": None,
            "outcome_json": None,
        }
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO decisions
                (id, created_at, updated_at, title, customer_name, domain, lifecycle_stage, input_json, card_json, review_json, outcome_json)
                VALUES
                (:id, :created_at, :updated_at, :title, :customer_name, :domain, :lifecycle_stage, :input_json, :card_json, :review_json, :outcome_json)
                """,
                record,
            )
        return self.get_decision(decision_id)

    def list_decisions(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM decisions ORDER BY created_at DESC").fetchall()
        return [self._decision_from_row(row) for row in rows]

    def get_decision(self, decision_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,)).fetchone()
        if row is None:
            return None
        return self._decision_from_row(row)

    def update_decision(
        self,
        decision_id: str,
        *,
        lifecycle_stage: str | None = None,
        card: dict[str, Any] | None = None,
        review: dict[str, Any] | None = None,
        outcome: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        current = self.get_decision(decision_id)
        if current is None:
            raise KeyError(f"Decision not found: {decision_id}")

        updates = {
            "updated_at": utc_now(),
            "lifecycle_stage": lifecycle_stage or current["lifecycle_stage"],
            "card_json": json.dumps(card) if card is not None else json.dumps(current["card"]) if current["card"] else None,
            "review_json": json.dumps(review) if review is not None else json.dumps(current["review"]) if current["review"] else None,
            "outcome_json": json.dumps(outcome) if outcome is not None else json.dumps(current["outcome"]) if current["outcome"] else None,
            "id": decision_id,
        }

        with self.connect() as connection:
            connection.execute(
                """
                UPDATE decisions
                SET updated_at = :updated_at,
                    lifecycle_stage = :lifecycle_stage,
                    card_json = :card_json,
                    review_json = :review_json,
                    outcome_json = :outcome_json
                WHERE id = :id
                """,
                updates,
            )
        return self.get_decision(decision_id)

    def add_lifecycle_event(
        self,
        decision_id: str,
        *,
        stage: str,
        status: str = "completed",
        actor: str = "Prism",
        notes: str = "",
    ) -> dict[str, Any]:
        event = {
            "id": str(uuid.uuid4()),
            "decision_id": decision_id,
            "stage": stage,
            "status": status,
            "timestamp": utc_now(),
            "actor": actor,
            "notes": notes,
        }
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO decision_lifecycle
                (id, decision_id, stage, status, timestamp, actor, notes)
                VALUES
                (:id, :decision_id, :stage, :status, :timestamp, :actor, :notes)
                """,
                event,
            )
        return event

    def list_lifecycle_events(self, decision_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, decision_id, stage, status, timestamp, actor, notes
                FROM decision_lifecycle
                WHERE decision_id = ?
                ORDER BY timestamp ASC
                """,
                (decision_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def next_decision_version(self, decision_id: str) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT MAX(version) AS version FROM decision_versions WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
        current = row["version"] if row and row["version"] is not None else 0
        return int(current) + 1

    def create_decision_version(
        self,
        decision_id: str,
        *,
        actor: str,
        change_type: str,
        snapshot: dict[str, Any],
        change_log: list[str] | None = None,
        version: int | None = None,
    ) -> dict[str, Any]:
        version_number = version or self.next_decision_version(decision_id)
        record = {
            "id": str(uuid.uuid4()),
            "decision_id": decision_id,
            "version": version_number,
            "created_at": utc_now(),
            "actor": actor,
            "change_type": change_type,
            "change_log_json": json.dumps(change_log or []),
            "snapshot_json": json.dumps(snapshot),
        }
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO decision_versions
                (id, decision_id, version, created_at, actor, change_type, change_log_json, snapshot_json)
                VALUES
                (:id, :decision_id, :version, :created_at, :actor, :change_type, :change_log_json, :snapshot_json)
                """,
                record,
            )
        return self._decision_version_from_record(record)

    def list_decision_versions(self, decision_id: str) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM decision_versions
                WHERE decision_id = ?
                ORDER BY version ASC
                """,
                (decision_id,),
            ).fetchall()
        return [self._decision_version_from_record(dict(row)) for row in rows]

    def search_decisions(
        self,
        *,
        persona_id: str | None = None,
        decision_type: str | None = None,
        outcome: str | None = None,
        min_confidence: int | None = None,
        decision_id: str | None = None,
        query: str | None = None,
    ) -> list[dict[str, Any]]:
        records = self.list_decisions()
        filtered = []
        for record in records:
            card = record.get("card") or {}
            input_payload = record.get("input") or {}
            structured = card.get("structured_context") or {}
            outcome_record = record.get("outcome") or {}
            searchable = compact_text(
                {
                    "id": record["id"],
                    "title": record["title"],
                    "customer_name": record["customer_name"],
                    "domain": record["domain"],
                    "persona_id": input_payload.get("persona_id"),
                    "decision_type": input_payload.get("decision_type") or structured.get("decision_type"),
                    "outcome": outcome_record.get("outcome"),
                    "summary": card.get("executive_summary"),
                    "recommendation": (card.get("recommendation") or {}).get("action"),
                }
            )

            if decision_id and record["id"] != decision_id:
                continue
            if persona_id and input_payload.get("persona_id") != persona_id:
                continue
            if decision_type:
                actual_type = input_payload.get("decision_type") or structured.get("decision_type") or ""
                if decision_type.lower() not in actual_type.lower():
                    continue
            if outcome:
                actual_outcome = outcome_record.get("outcome", "")
                if outcome.lower() not in actual_outcome.lower():
                    continue
            if min_confidence is not None and int(card.get("confidence") or 0) < min_confidence:
                continue
            if query and query.lower() not in searchable.lower():
                continue
            filtered.append(record)
        return filtered

    def decision_analytics(self) -> dict[str, Any]:
        records = self.list_decisions()
        confidence_values = []
        strategy_counter: Counter[str] = Counter()
        risk_counter: Counter[str] = Counter()
        success_by_persona: Counter[str] = Counter()
        total_by_persona: Counter[str] = Counter()
        completed = 0
        successful = 0

        for record in records:
            card = record.get("card") or {}
            input_payload = record.get("input") or {}
            persona_id = input_payload.get("persona_id", "unknown")
            total_by_persona[persona_id] += 1

            if card.get("confidence") is not None:
                confidence_values.append(int(card["confidence"]))

            recommendation = card.get("recommendation") or {}
            action = recommendation.get("action")
            if action:
                strategy_counter[action] += 1

            risk = card.get("enterprise_decision_card", {}).get("risk") or recommendation.get("risk_level")
            if risk:
                risk_counter[str(risk)] += 1

            outcome_status = self._normalized_outcome((record.get("outcome") or {}).get("outcome"))
            if outcome_status != "Pending":
                completed += 1
                if outcome_status == "Succeeded":
                    successful += 1
                    success_by_persona[persona_id] += 1

        persona_success = []
        for persona_id, total in total_by_persona.items():
            if total:
                persona_success.append(
                    {
                        "persona_id": persona_id,
                        "decisions": total,
                        "successful": success_by_persona[persona_id],
                        "success_rate": round(success_by_persona[persona_id] / total, 2),
                    }
                )

        return {
            "decision_success_rate": round(successful / completed, 2) if completed else 0.0,
            "average_confidence": round(sum(confidence_values) / len(confidence_values), 1) if confidence_values else 0.0,
            "top_strategies": [{"strategy": key, "count": value} for key, value in strategy_counter.most_common(5)],
            "most_common_risks": [{"risk": key, "count": value} for key, value in risk_counter.most_common(5)],
            "most_successful_personas": sorted(persona_success, key=lambda item: item["success_rate"], reverse=True)[:5],
            "decision_volume": len(records),
            "completed_decisions": completed,
        }

    def query_knowledge(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM knowledge_docs").fetchall()

        scored = []
        for row in rows:
            tags = json.loads(row["tags_json"])
            searchable = f"{row['title']} {row['domain']} {' '.join(tags)} {row['content']}"
            score = score_text(query, searchable)
            if score > 0:
                scored.append(
                    {
                        "id": row["id"],
                        "title": row["title"],
                        "source_type": row["source_type"],
                        "domain": row["domain"],
                        "tags": tags,
                        "excerpt": excerpt(row["content"]),
                        "score": score,
                    }
                )

        return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]

    def list_knowledge_documents(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM knowledge_docs").fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "source_type": row["source_type"],
                "domain": row["domain"],
                "tags": json.loads(row["tags_json"]),
                "content": row["content"],
            }
            for row in rows
        ]

    def query_memory(self, query: str, limit: int = 4) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM memory_cases").fetchall()

        scored = []
        for row in rows:
            tags = json.loads(row["tags_json"])
            searchable = compact_text(
                {
                    "customer": row["customer_name"],
                    "industry": row["industry"],
                    "segment": row["segment"],
                    "problem": row["problem"],
                    "recommendation": row["recommendation"],
                    "outcome": row["outcome"],
                    "tags": tags,
                    "summary": row["summary"],
                }
            )
            score = score_text(query, searchable)
            if score > 0:
                scored.append(
                    {
                        "id": row["id"],
                        "customer_name": row["customer_name"],
                        "industry": row["industry"],
                        "segment": row["segment"],
                        "problem": row["problem"],
                        "recommendation": row["recommendation"],
                        "outcome": row["outcome"],
                        "confidence": row["confidence"],
                        "tags": tags,
                        "summary": row["summary"],
                        "score": score,
                    }
                )

        return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]

    def list_legacy_memory_cases(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM memory_cases").fetchall()

        records = []
        for row in rows:
            tags = json.loads(row["tags_json"])
            records.append(
                {
                    "id": row["id"],
                    "title": row["problem"],
                    "persona_id": self._persona_from_tags(tags),
                    "persona_label": self._persona_from_tags(tags),
                    "domain": row["segment"],
                    "decision_type": row["problem"],
                    "entity_name": row["customer_name"],
                    "primary_problem": row["problem"],
                    "urgency": "Medium",
                    "sentiment": "Neutral",
                    "business_signals": tags,
                    "recommendation": row["recommendation"],
                    "alternatives": [],
                    "decision_matrix": [],
                    "evidence": [{"source": "Legacy Memory", "detail": row["summary"]}],
                    "confidence": row["confidence"],
                    "outcome": row["outcome"],
                    "outcome_notes": "",
                    "knowledge_references": [],
                    "simulation_results": [],
                    "planner_reasoning": [],
                    "council_consensus": {},
                    "created_at": "",
                    "updated_at": "",
                }
            )
        return records

    def archive_decision(self, archive_record: dict[str, Any]) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO decision_archive
                (id, archived_at, payload_json)
                VALUES (:id, :archived_at, :payload_json)
                """,
                {
                    "id": archive_record["id"],
                    "archived_at": utc_now(),
                    "payload_json": json.dumps(archive_record),
                },
            )

    def list_archived_decisions(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute("SELECT payload_json FROM decision_archive ORDER BY archived_at DESC").fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def insert_memory_case(self, case: dict[str, Any]) -> dict[str, Any]:
        case_id = case.get("id") or f"case-{uuid.uuid4()}"
        record = {
            "id": case_id,
            "customer_name": case["customer_name"],
            "industry": case.get("industry", "Unknown"),
            "segment": case.get("segment", "Unknown"),
            "problem": case["problem"],
            "recommendation": case["recommendation"],
            "outcome": case["outcome"],
            "confidence": int(case.get("confidence", 70)),
            "tags_json": json.dumps(case.get("tags", [])),
            "summary": case["summary"],
        }
        with self.connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO memory_cases
                (id, customer_name, industry, segment, problem, recommendation, outcome, confidence, tags_json, summary)
                VALUES
                (:id, :customer_name, :industry, :segment, :problem, :recommendation, :outcome, :confidence, :tags_json, :summary)
                """,
                record,
            )
        return {**case, "id": case_id}

    def _persona_from_tags(self, tags: list[str]) -> str:
        known = {"customer_success", "sales", "healthcare", "hr", "operations"}
        for tag in tags:
            normalized = str(tag).lower()
            if normalized in known:
                return normalized
        if any("hr" == str(tag).lower() for tag in tags):
            return "hr"
        return "customer_success"

    def _decision_version_from_record(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": record["id"],
            "decision_id": record["decision_id"],
            "version": record["version"],
            "created_at": record["created_at"],
            "actor": record["actor"],
            "change_type": record["change_type"],
            "change_log": json.loads(record["change_log_json"]),
            "snapshot": json.loads(record["snapshot_json"]),
        }

    def _normalized_outcome(self, outcome: str | None) -> str:
        if not outcome:
            return "Pending"
        normalized = outcome.strip().lower()
        if normalized in {"succeeded", "success", "won", "renewed", "stayed", "resolved", "completed"}:
            return "Succeeded"
        if normalized in {"failed", "lost", "resigned", "churned"}:
            return "Failed"
        if normalized in {"partial", "partially successful", "partially_successful"}:
            return "Partially Successful"
        if normalized in {"cancelled", "canceled"}:
            return "Cancelled"
        return "Unknown"

    def _decision_from_row(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "title": row["title"],
            "customer_name": row["customer_name"],
            "domain": row["domain"],
            "lifecycle_stage": row["lifecycle_stage"],
            "input": json.loads(row["input_json"]),
            "card": json.loads(row["card_json"]) if row["card_json"] else None,
            "review": json.loads(row["review_json"]) if row["review_json"] else None,
            "outcome": json.loads(row["outcome_json"]) if row["outcome_json"] else None,
            "version_history": self.list_decision_versions(row["id"]),
            "lifecycle_history": self.list_lifecycle_events(row["id"]),
        }
