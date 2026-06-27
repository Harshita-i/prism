from __future__ import annotations

import json
from typing import Any

from app.llm.errors import LLMResponseError


def strip_json_markdown(text: str) -> str:
    clean = text.strip()
    if clean.startswith("```json"):
        clean = clean.removeprefix("```json").strip()
    if clean.startswith("```"):
        clean = clean.removeprefix("```").strip()
    if clean.endswith("```"):
        clean = clean.removesuffix("```").strip()
    return clean.strip()


def parse_json_object(text: str) -> dict[str, Any]:
    clean = strip_json_markdown(text)
    try:
        value = json.loads(clean)
    except json.JSONDecodeError:
        start = clean.find("{")
        end = clean.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LLMResponseError("LLM response did not contain a JSON object.")
        try:
            value = json.loads(clean[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMResponseError(f"LLM response JSON could not be parsed: {exc}") from exc

    if not isinstance(value, dict):
        raise LLMResponseError("LLM response must be a JSON object.")
    return value
