from __future__ import annotations

from app.llm.gemini_provider import GeminiProvider
from app.llm.provider import LLMProvider
from app.llm.settings import LLMSettings


def create_provider(settings: LLMSettings) -> LLMProvider:
    if settings.provider == "gemini":
        return GeminiProvider(settings)
    return GeminiProvider(settings)
