from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class LLMSettings:
    enabled: bool
    provider: str
    model: str
    api_key: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    max_retries: int
    cache_enabled: bool
    cache_path: Path

    @classmethod
    def from_env(cls, root: Path | None = None) -> "LLMSettings":
        root_path = root or Path(__file__).resolve().parents[2]
        _load_env_file(root_path / ".env")
        _load_env_file(root_path / ".env.local")
        provider = os.getenv("PRISM_LLM_PROVIDER", "gemini").strip().lower()
        model = (
            os.getenv("PRISM_LLM_MODEL")
            or os.getenv("GEMINI_MODEL")
            or ""
        ).strip()
        api_key = (
            os.getenv("PRISM_LLM_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or ""
        ).strip()
        cache_path = Path(os.getenv("PRISM_LLM_CACHE_PATH", str(root_path / ".prism_cache" / "llm_cache.json")))

        return cls(
            enabled=_truthy(os.getenv("PRISM_LLM_ENABLED")),
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=float(os.getenv("PRISM_LLM_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("PRISM_LLM_MAX_TOKENS", "4096")),
            timeout_seconds=float(os.getenv("PRISM_LLM_TIMEOUT_SECONDS", "25")),
            max_retries=int(os.getenv("PRISM_LLM_MAX_RETRIES", "0")),
            cache_enabled=not _truthy(os.getenv("PRISM_LLM_CACHE_DISABLED")),
            cache_path=cache_path,
        )

    def config_issue(self) -> str | None:
        if not self.enabled:
            return "LLM disabled by PRISM_LLM_ENABLED."
        if self.provider != "gemini":
            return f"Unsupported LLM provider: {self.provider}."
        if not self.model:
            return "Missing PRISM_LLM_MODEL or GEMINI_MODEL."
        if not self.api_key:
            return "Missing GEMINI_API_KEY or PRISM_LLM_API_KEY."
        return None
