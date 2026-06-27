from __future__ import annotations

from typing import Any, Protocol

from app.core.decision_context import ContextSignal, StructuredContext
from app.llm.service import LLMService


class ContextExtractor(Protocol):
    def extract(self, user_input: dict[str, Any], persona: dict[str, Any]) -> StructuredContext:
        """Convert raw user input into structured business facts."""


class LLMContextExtractor:
    """
    Phase 2 extractor.

    This remains the only component allowed to inspect raw transcript text.
    It delegates intelligence to the LLM service when enabled, and falls back
    to LocalContextExtractor when the provider is unavailable.
    """

    def __init__(
        self,
        llm_service: LLMService | None = None,
        fallback: "LocalContextExtractor | None" = None,
    ) -> None:
        self.llm_service = llm_service or LLMService.from_env()
        self.fallback = fallback or LocalContextExtractor()
        self.last_metadata: dict[str, Any] = {}

    def extract(self, user_input: dict[str, Any], persona: dict[str, Any]) -> StructuredContext:
        result = self.llm_service.extract_context(user_input, persona)
        self.last_metadata = result.metadata
        if result.value is not None:
            self.last_metadata = {**self.last_metadata, "fallback_used": False}
            return result.value

        fallback_context = self.fallback.extract(user_input, persona)
        self.last_metadata = {
            **self.last_metadata,
            "fallback_used": True,
            "fallback_message": "AI reasoning temporarily unavailable. Showing rule-based reasoning.",
            "error": result.error,
        }
        return fallback_context


class LocalContextExtractor:
    """
    Deterministic extractor used for Phase 1.

    This is the only class in the pipeline that reads free text. In Phase 2,
    replace this implementation with Gemini/OpenAI while keeping the same
    ContextExtractor interface.
    """

    SEVERITY_BY_URGENCY = {
        "Low": "Low",
        "Medium": "Medium",
        "High": "High",
        "Critical": "Critical",
    }

    CONCEPT_ALIASES = {
        "high workload": ["weekend", "burnout", "overloaded", "overworked", "stress", "too much work"],
        "career stagnation": ["career growth", "promotion", "no growth", "stuck", "learning"],
        "growth concern": ["career growth", "promotion", "no growth", "stuck", "learning"],
        "external offer": ["another company", "recruiter", "new offer", "market offer", "reached out"],
        "pricing concern": ["expensive", "price", "budget", "commercial", "discount"],
        "competitor evaluation": ["competitor", "alternative", "other vendor", "evaluating"],
        "support risk": ["support ticket", "bug", "sla", "outage", "technical issue"],
        "security concern": ["security review", "compliance", "privacy", "data residency"],
        "high occupancy": ["overcrowded", "capacity", "full beds", "bed shortage"],
        "discharge delay": ["discharge queue", "transport delay", "documentation delay"],
        "supplier delay": ["late shipment", "delayed shipment", "vendor delay"],
        "sla exposure": ["deadline", "penalty", "customer impact", "sla breach"],
        "low inventory buffer": ["stockout", "shortage", "low stock", "inventory risk"],
    }

    def extract(self, user_input: dict[str, Any], persona: dict[str, Any]) -> StructuredContext:
        record = user_input.get("crm_record") or {}
        text = " ".join(
            str(value)
            for value in [
                user_input.get("title", ""),
                user_input.get("interaction_text", ""),
                record,
                user_input.get("support_history", ""),
            ]
            if value
        )
        normalized = text.lower()

        signals = self._infer_signals(normalized, persona, record)
        urgency = self._infer_urgency(signals, persona, record)
        sentiment = self._infer_sentiment(normalized, urgency)
        entity_name = user_input.get("customer_name") or record.get("customer_name") or record.get("entity_name")
        missing = [
            field
            for field in persona.get("required_fields", [])
            if record.get(field) in [None, ""]
        ]

        metrics = {**record}
        metrics["signal_count"] = len(signals)

        summary = self._build_summary(user_input, persona, signals, urgency)
        confidence = 0.78 if signals else 0.55
        if missing:
            confidence = max(0.45, confidence - min(0.2, len(missing) * 0.04))

        return StructuredContext(
            primary_problem=self._primary_problem(persona, signals),
            decision_type=user_input.get("decision_type") or persona.get("decision_type", "Business Decision"),
            urgency=urgency,
            sentiment=sentiment,
            entities=[str(entity_name)] if entity_name else [],
            stakeholders=self._stakeholders_for(persona),
            business_signals=signals,
            required_context=missing,
            extracted_metrics=metrics,
            summary=summary,
            confidence=round(confidence, 2),
        )

    def _infer_signals(self, normalized: str, persona: dict[str, Any], record: dict[str, Any]) -> list[ContextSignal]:
        signals: list[ContextSignal] = []

        for action in persona.get("actions", []):
            for driver in action.get("decision_drivers", []):
                if self._concept_present(driver, normalized, record):
                    self._add_signal(signals, driver, "Decision Driver", "High")

        for threshold in persona.get("risk_thresholds", []):
            if self._threshold_matches(record.get(threshold["metric"]), threshold):
                self._add_signal(
                    signals,
                    threshold["label"],
                    "Metric Threshold",
                    threshold.get("severity", "High"),
                    f"{threshold['metric']}={record.get(threshold['metric'])}",
                )

        if not signals:
            self._add_signal(
                signals,
                persona.get("decision_type", "Business Decision"),
                "Default Decision Context",
                "Medium",
            )

        return signals

    def _concept_present(self, concept: str, normalized: str, record: dict[str, Any]) -> bool:
        concept_terms = {term for term in concept.lower().replace("-", " ").split() if len(term) > 2}
        if concept.lower() in normalized:
            return True
        for alias in self.CONCEPT_ALIASES.get(concept.lower(), []):
            if alias in normalized:
                return True
        if concept_terms and all(term in normalized for term in concept_terms):
            return True

        metric_text = " ".join(str(value).lower() for value in record.values())
        if concept.lower() in metric_text:
            return True
        if any(alias in metric_text for alias in self.CONCEPT_ALIASES.get(concept.lower(), [])):
            return True
        return bool(concept_terms and all(term in metric_text for term in concept_terms))

    def _add_signal(
        self,
        signals: list[ContextSignal],
        label: str,
        category: str,
        severity: str,
        evidence: str = "",
    ) -> None:
        if any(signal.label.lower() == label.lower() for signal in signals):
            return
        signals.append(
            ContextSignal(
                label=label,
                category=category,
                severity=severity,  # type: ignore[arg-type]
                evidence=evidence,
            )
        )

    def _infer_urgency(self, signals: list[ContextSignal], persona: dict[str, Any], record: dict[str, Any]) -> str:
        if any(signal.severity == "Critical" for signal in signals):
            return "Critical"
        if any(signal.severity == "High" for signal in signals):
            return "High"

        for threshold in persona.get("risk_thresholds", []):
            if threshold.get("severity") in {"High", "Critical"} and self._threshold_matches(record.get(threshold["metric"]), threshold):
                return "High"
        return "Medium"

    def _infer_sentiment(self, normalized: str, urgency: str) -> str:
        negative_terms = ["risk", "concern", "blocked", "delay", "resign", "churn", "angry", "frustrated", "overloaded", "breach"]
        positive_terms = ["renew", "improved", "ready", "approved", "healthy", "positive"]
        negative_count = sum(1 for term in negative_terms if term in normalized)
        positive_count = sum(1 for term in positive_terms if term in normalized)
        if negative_count and positive_count:
            return "Mixed"
        if negative_count or urgency in {"High", "Critical"}:
            return "Negative"
        if positive_count:
            return "Positive"
        return "Neutral"

    def _primary_problem(self, persona: dict[str, Any], signals: list[ContextSignal]) -> str:
        if signals and signals[0].category != "Default Decision Context":
            return f"{persona.get('decision_type', 'Decision')} involving {signals[0].label}"
        return persona.get("decision_type", "Business Decision")

    def _stakeholders_for(self, persona: dict[str, Any]) -> list[str]:
        owners = []
        for action in persona.get("actions", []):
            owner = action.get("owner")
            if owner:
                owners.extend(part.strip() for part in owner.replace("+", ",").split(","))
        return list(dict.fromkeys(owners))[:4]

    def _build_summary(
        self,
        user_input: dict[str, Any],
        persona: dict[str, Any],
        signals: list[ContextSignal],
        urgency: str,
    ) -> str:
        entity = user_input.get("customer_name") or "The business entity"
        signal_text = ", ".join(signal.label for signal in signals[:4])
        return (
            f"{entity} has a {persona.get('decision_type', 'business decision')} in "
            f"{persona.get('domain', 'the business domain')}. Urgency is {urgency}. "
            f"Detected signals: {signal_text}."
        )

    def _threshold_matches(self, metric_value: Any, threshold: dict[str, Any]) -> bool:
        try:
            actual = float(metric_value)
            expected = float(threshold["value"])
        except (TypeError, ValueError):
            return False

        operator = threshold["operator"]
        if operator == "lt":
            return actual < expected
        if operator == "lte":
            return actual <= expected
        if operator == "gt":
            return actual > expected
        if operator == "gte":
            return actual >= expected
        if operator == "eq":
            return actual == expected
        return False
