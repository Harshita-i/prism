from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from app.llm.errors import LLMConfigurationError, LLMError
from app.llm.provider import LLMRequest, LLMResponse
from app.llm.settings import LLMSettings


class GeminiProvider:
    provider_name = "gemini"

    def __init__(self, settings: LLMSettings) -> None:
        self.settings = settings

    def generate(self, request: LLMRequest) -> LLMResponse:
        issue = self.settings.config_issue()
        if issue:
            raise LLMConfigurationError(issue)

        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.settings.model}:generateContent?key={self.settings.api_key}"
        )
        payload = {
            "systemInstruction": {
                "parts": [{"text": request.system_prompt}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": self._combined_prompt(request),
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
                "responseMimeType": "application/json",
            },
        }

        body = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        started = time.perf_counter()
        try:
            with urllib.request.urlopen(http_request, timeout=self.settings.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise LLMError(f"Gemini HTTP error {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"Gemini network error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMError("Gemini request timed out.") from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        data = json.loads(raw)
        text = self._extract_text(data)
        usage = data.get("usageMetadata") or {}
        return LLMResponse(
            text=text,
            provider=self.provider_name,
            model=self.settings.model,
            latency_ms=latency_ms,
            token_usage=usage,
        )

    def _combined_prompt(self, request: LLMRequest) -> str:
        return "\n\n".join(
            [
                "Developer Instructions:",
                request.developer_prompt,
                "Task Context:",
                request.user_prompt,
            ]
        )

    def _extract_text(self, data: dict) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            raise LLMError("Gemini response contained no candidates.")
        parts = candidates[0].get("content", {}).get("parts") or []
        if not parts or "text" not in parts[0]:
            raise LLMError("Gemini response contained no text part.")
        return str(parts[0]["text"])
