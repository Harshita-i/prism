from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar

from pydantic import ValidationError

from app.core.decision_context import (
    Consensus,
    ContextSignal,
    CouncilMessage,
    DecisionContext,
    StructuredContext,
)
from app.llm.cache import LLMResponseCache, deterministic_key
from app.llm.errors import LLMError, LLMResponseError
from app.llm.factory import create_provider
from app.llm.json_utils import parse_json_object
from app.llm.logger import log_llm_event
from app.llm.prompt_builder import PromptBuilder, PromptParts
from app.llm.provider import LLMProvider, LLMRequest
from app.llm.schemas import LLMCouncilResponse, LLMContextExtractionResponse
from app.llm.settings import LLMSettings


T = TypeVar("T")


@dataclass
class LLMOperationResult(Generic[T]):
    value: T | None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class LLMService:
    def __init__(
        self,
        settings: LLMSettings,
        provider: LLMProvider | None = None,
        cache: LLMResponseCache | None = None,
        prompt_builder: PromptBuilder | None = None,
    ) -> None:
        self.settings = settings
        self.provider = provider or create_provider(settings)
        self.cache = cache or LLMResponseCache(settings.cache_path, enabled=settings.cache_enabled)
        self.prompt_builder = prompt_builder or PromptBuilder()

    @classmethod
    def from_env(cls) -> "LLMService":
        settings = LLMSettings.from_env()
        return cls(settings=settings)

    def extract_context(self, user_input: dict[str, Any], persona: dict[str, Any]) -> LLMOperationResult[StructuredContext]:
        prompt = self.prompt_builder.context_extraction(user_input, persona)
        cache_payload = {
            "call": "context_extraction",
            "provider": self.settings.provider,
            "model": self.settings.model,
            "persona": persona.get("id"),
            "transcript": user_input.get("interaction_text"),
            "title": user_input.get("title"),
            "entity": user_input.get("customer_name"),
            "metadata": user_input.get("crm_record", {}),
        }

        raw_result = self._generate_json("context_extraction", prompt, cache_payload)
        if raw_result.value is None:
            return LLMOperationResult(value=None, metadata=raw_result.metadata, error=raw_result.error)

        try:
            parsed = LLMContextExtractionResponse.model_validate(raw_result.value)
            structured = self._to_structured_context(parsed, user_input, persona)
        except (ValidationError, ValueError) as exc:
            metadata = {**raw_result.metadata, "validation_error": str(exc)}
            log_llm_event("validation_failure", call="context_extraction", error=str(exc))
            return LLMOperationResult(value=None, metadata=metadata, error=str(exc))

        return LLMOperationResult(value=structured, metadata=raw_result.metadata)

    def facilitate_council(self, context: DecisionContext) -> LLMOperationResult[dict[str, Any]]:
        prompt = self.prompt_builder.executive_council(context)
        cache_payload = {
            "call": "executive_council",
            "provider": self.settings.provider,
            "model": self.settings.model,
            "persona": context.metadata.persona_id,
            "structured_context": context.structured_context.model_dump() if context.structured_context else {},
            "knowledge_version": [(item.id, item.weighted_score, item.document_id) for item in context.knowledge_packets],
            "memory_version": [(item.id, item.outcome, item.weighted_score, item.source_decision) for item in context.memory_packets],
            "risk_version": context.risk_analysis.model_dump() if context.risk_analysis else {},
            "scenario_version": [(item.id, item.weighted_score, item.success_probability, item.business_risk) for item in context.scenario_packets],
        }

        raw_result = self._generate_json("executive_council", prompt, cache_payload)
        if raw_result.value is None:
            return LLMOperationResult(value=None, metadata=raw_result.metadata, error=raw_result.error)

        try:
            parsed = LLMCouncilResponse.model_validate(raw_result.value)
            if not parsed.discussion:
                raise LLMResponseError("Council response must include at least one discussion message.")
            council = self._to_council(parsed, context)
        except (ValidationError, ValueError, LLMResponseError) as exc:
            metadata = {**raw_result.metadata, "validation_error": str(exc)}
            log_llm_event("validation_failure", call="executive_council", error=str(exc))
            return LLMOperationResult(value=None, metadata=metadata, error=str(exc))

        return LLMOperationResult(value=council, metadata=raw_result.metadata)

    def _generate_json(
        self,
        call_name: str,
        prompt: PromptParts,
        cache_payload: dict[str, Any],
    ) -> LLMOperationResult[dict[str, Any]]:
        config_issue = self.settings.config_issue()
        base_metadata = {
            "call": call_name,
            "provider": self.settings.provider,
            "model": self.settings.model,
            "enabled": self.settings.enabled,
        }
        if config_issue:
            metadata = {**base_metadata, "mode": "fallback", "reason": config_issue}
            log_llm_event("skipped", **metadata)
            return LLMOperationResult(value=None, metadata=metadata, error=config_issue)

        cache_key = deterministic_key(cache_payload)
        cached = self.cache.get(cache_key)
        if cached is not None:
            metadata = {**base_metadata, "cache_hit": True, "mode": "llm"}
            log_llm_event("cache_hit", call=call_name, provider=self.settings.provider, model=self.settings.model)
            return LLMOperationResult(value=cached, metadata=metadata)

        started = time.perf_counter()
        attempts = max(1, self.settings.max_retries + 1)
        last_error: str | None = None

        for attempt in range(1, attempts + 1):
            try:
                request = LLMRequest(
                    system_prompt=prompt.system_prompt,
                    developer_prompt=prompt.developer_prompt,
                    user_prompt=prompt.user_prompt(),
                    temperature=self.settings.temperature,
                    max_tokens=self.settings.max_tokens,
                )
                response = self.provider.generate(request)
                parsed = parse_json_object(response.text)
                self.cache.set(cache_key, parsed)
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                metadata = {
                    **base_metadata,
                    "mode": "llm",
                    "cache_hit": False,
                    "latency_ms": response.latency_ms,
                    "elapsed_ms": elapsed_ms,
                    "attempts": attempt,
                    "token_usage": response.token_usage,
                }
                log_llm_event("success", **metadata)
                return LLMOperationResult(value=parsed, metadata=metadata)
            except (LLMError, LLMResponseError, ValueError) as exc:
                last_error = str(exc)
                log_llm_event("failure", call=call_name, attempt=attempt, error=last_error)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        metadata = {
            **base_metadata,
            "mode": "fallback",
            "cache_hit": False,
            "elapsed_ms": elapsed_ms,
            "attempts": attempts,
            "error": last_error,
        }
        return LLMOperationResult(value=None, metadata=metadata, error=last_error)

    def _to_structured_context(
        self,
        parsed: LLMContextExtractionResponse,
        user_input: dict[str, Any],
        persona: dict[str, Any],
    ) -> StructuredContext:
        record = user_input.get("crm_record") or {}
        extracted_metrics = {**record, **parsed.extracted_metrics}
        return StructuredContext(
            primary_problem=parsed.primary_problem,
            decision_type=parsed.decision_type or user_input.get("decision_type") or persona.get("decision_type", "Business Decision"),
            urgency=parsed.urgency,
            sentiment=parsed.sentiment,
            entities=parsed.entities or [user_input.get("customer_name", "")],
            stakeholders=parsed.stakeholders,
            business_signals=[
                ContextSignal(
                    label=signal.label,
                    category=signal.category,
                    severity=signal.severity,
                    evidence=signal.evidence,
                )
                for signal in parsed.business_signals
            ],
            required_context=parsed.required_context,
            extracted_metrics=extracted_metrics,
            summary=parsed.summary,
            confidence=parsed.confidence,
        )

    def _to_council(self, parsed: LLMCouncilResponse, context: DecisionContext) -> dict[str, Any]:
        messages = [
            CouncilMessage(
                turn=index,
                agent=message.agent,
                message_type=message.message_type,
                message=message.message,
                references=message.references,
                confidence=message.confidence,
                reply_to=message.reply_to,
                supports=message.supports,
                challenges=message.challenges,
                evidence_references=message.references,
            )
            for index, message in enumerate(parsed.discussion, start=1)
        ]

        simulation_titles = {strategy.title for strategy in context.simulations}
        scenario_titles = {scenario.title for scenario in context.scenario_packets}
        available_titles = scenario_titles or simulation_titles
        preferred = parsed.consensus.preferred_strategy
        disagreements = list(parsed.consensus.disagreements)
        if preferred and preferred not in available_titles:
            disagreements.append(
                f"LLM consensus referenced '{preferred}', which is not an available scenario strategy."
            )
            preferred = context.winning_scenario.title if context.winning_scenario else context.simulations[0].title if context.simulations else None

        consensus = Consensus(
            status=parsed.consensus.status,
            level=parsed.consensus.level,
            preferred_strategy=preferred,
            rationale=[*parsed.consensus.rationale, *parsed.supporting_points],
            disagreements=disagreements,
            open_questions=parsed.consensus.open_questions,
            confidence=parsed.consensus.confidence,
        )
        return {
            "messages": messages,
            "consensus": consensus,
        }
