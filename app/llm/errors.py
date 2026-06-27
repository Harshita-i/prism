from __future__ import annotations


class LLMError(RuntimeError):
    """Base error for the provider-independent LLM layer."""


class LLMConfigurationError(LLMError):
    """Raised when the selected provider is missing required configuration."""


class LLMResponseError(LLMError):
    """Raised when a provider returns malformed or unusable output."""

