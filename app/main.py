from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.orchestrator import DecisionOrchestrator
from app.storage import SQLiteStorage


logging.basicConfig(level=os.getenv("PRISM_LOG_LEVEL", "INFO"))

ROOT = Path(__file__).resolve().parents[1]
storage = SQLiteStorage(ROOT / "decisionos.db")
storage.seed_if_empty()
orchestrator = DecisionOrchestrator(storage)

app = FastAPI(
    title="Prism API",
    description="Collaborative DecisionContext backend for enterprise decision intelligence.",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateDecisionRequest(BaseModel):
    title: str = Field(..., examples=["Senior engineer retention risk"])
    customer_name: str = Field(..., examples=["Harshita"])
    domain: str = "People Operations"
    persona_id: str = "hr"
    decision_type: str = "Retention Risk"
    interaction_text: str
    crm_record: dict[str, Any] = Field(default_factory=dict)
    support_history: list[dict[str, Any]] = Field(default_factory=list)


class ReviewRequest(BaseModel):
    action: str = Field(..., examples=["approve"])
    reviewer: str = Field(..., examples=["Business Decision Owner"])
    notes: str = ""
    modified_action: str | None = None


class OutcomeRequest(BaseModel):
    outcome: str = Field(..., examples=["Stayed"])
    notes: str = ""


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/decisions")
def list_decisions() -> list[dict[str, Any]]:
    return storage.list_decisions()


@app.post("/decisions")
def create_decision(payload: CreateDecisionRequest) -> dict[str, Any]:
    return storage.create_decision(payload.model_dump())


@app.get("/decisions/{decision_id}")
def get_decision(decision_id: str) -> dict[str, Any]:
    decision = storage.get_decision(decision_id)
    if decision is None:
        raise HTTPException(status_code=404, detail="Decision not found")
    return decision


@app.post("/decisions/{decision_id}/run")
def run_decision(decision_id: str) -> dict[str, Any]:
    try:
        return orchestrator.run_decision(decision_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/decisions/{decision_id}/review")
def review_decision(decision_id: str, payload: ReviewRequest) -> dict[str, Any]:
    try:
        return orchestrator.record_review(
            decision_id,
            action=payload.action,
            reviewer=payload.reviewer,
            notes=payload.notes,
            modified_action=payload.modified_action,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/decisions/{decision_id}/outcome")
def record_outcome(decision_id: str, payload: OutcomeRequest) -> dict[str, Any]:
    try:
        return orchestrator.record_outcome(decision_id, outcome=payload.outcome, notes=payload.notes)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
