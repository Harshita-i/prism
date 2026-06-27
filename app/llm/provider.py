from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMRequest:
    system_prompt: str
    developer_prompt: str
    user_prompt: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    latency_ms: int
    token_usage: dict[str, Any] = field(default_factory=dict)


class LLMProvider(Protocol):
    provider_name: str

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate one response from the selected provider."""

