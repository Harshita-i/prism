from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


RiskLevel = Literal["Low", "Medium", "High", "Critical"]
Sentiment = Literal["Positive", "Neutral", "Negative", "Mixed"]
MessageType = Literal[
    "finding",
    "question",
    "challenge",
    "support",
    "clarification",
    "disagreement",
    "evidence",
    "revision",
    "consensus",
]


class LLMContextSignal(BaseModel):
    label: str
    category: str = "Business Signal"
    severity: RiskLevel = "Medium"
    evidence: str = ""


class LLMContextExtractionResponse(BaseModel):
    primary_problem: str
    decision_type: str | None = None
    urgency: RiskLevel = "Medium"
    sentiment: Sentiment = "Neutral"
    entities: list[str] = Field(default_factory=list)
    stakeholders: list[str] = Field(default_factory=list)
    business_signals: list[LLMContextSignal] = Field(default_factory=list)
    required_context: list[str] = Field(default_factory=list)
    extracted_metrics: dict[str, Any] = Field(default_factory=dict)
    summary: str = ""
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    @field_validator("business_signals", mode="before")
    @classmethod
    def normalize_signals(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return []
        normalized = []
        for item in value:
            if isinstance(item, str):
                normalized.append({"label": item})
            elif isinstance(item, dict):
                normalized.append(item)
        return normalized


class LLMCouncilMessage(BaseModel):
    agent: str
    message_type: MessageType = "finding"
    message: str
    references: list[str] = Field(default_factory=list)
    confidence: int | None = Field(default=None, ge=0, le=100)
    reply_to: int | None = None
    supports: list[str] = Field(default_factory=list)
    challenges: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def accept_category_alias(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        transformed = dict(value)
        if "category" in transformed and "message_type" not in transformed:
            transformed["message_type"] = str(transformed["category"]).lower()
        return transformed

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: Any) -> int | None:
        if value is None:
            return None
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return None
        if 0 <= numeric <= 1:
            return round(numeric * 100)
        return round(numeric)

    @field_validator("references", "supports", "challenges", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]


class LLMCouncilConsensus(BaseModel):
    status: Literal["Reached", "Needs More Information"] = "Reached"
    level: Literal["Weak", "Moderate", "Strong"] = "Moderate"
    preferred_strategy: str | None = None
    rationale: list[str] = Field(default_factory=list)
    disagreements: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    confidence: int = Field(default=70, ge=0, le=100)

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, value: Any) -> int:
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 70
        if 0 <= numeric <= 1:
            return round(numeric * 100)
        return round(numeric)

    @model_validator(mode="before")
    @classmethod
    def accept_spec_aliases(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        transformed = dict(value)
        if "title" in transformed and "preferred_strategy" not in transformed:
            transformed["preferred_strategy"] = transformed.get("title")
        if "reason" in transformed and "rationale" not in transformed:
            transformed["rationale"] = [str(transformed.get("reason"))]
        return transformed

    @field_validator("rationale", "disagreements", "open_questions", mode="before")
    @classmethod
    def normalize_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]


class LLMCouncilResponse(BaseModel):
    discussion: list[LLMCouncilMessage] = Field(default_factory=list)
    consensus: LLMCouncilConsensus
    supporting_points: list[str] = Field(default_factory=list)

    @field_validator("supporting_points", mode="before")
    @classmethod
    def normalize_supporting_points(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return [str(value)]
