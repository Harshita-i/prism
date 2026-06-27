from __future__ import annotations

import json
import sqlite3
import uuid
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
                """
            )

    def seed_if_empty(self) -> None:
        with self.connect() as connection:
            knowledge_count = connection.execute("SELECT COUNT(*) FROM knowledge_docs").fetchone()[0]
            memory_count = connection.execute("SELECT COUNT(*) FROM memory_cases").fetchone()[0]

            if knowledge_count == 0:
                connection.executemany(
                    """
                    INSERT INTO knowledge_docs
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

            if memory_count == 0:
                connection.executemany(
                    """
                    INSERT INTO memory_cases
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
            "customer_name": payload.get("customer_name") or payload.get("crm_record", {}).get("customer_name", "Unknown Customer"),
            "domain": payload.get("domain", "B2B SaaS Customer Success"),
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

    def query_memory(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
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
        }
