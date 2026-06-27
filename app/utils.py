from __future__ import annotations

import re
from collections import Counter
from typing import Iterable


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "our",
    "that",
    "the",
    "their",
    "they",
    "this",
    "to",
    "was",
    "we",
    "with",
    "you",
}


def clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(maximum, value))


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [word for word in words if word not in STOPWORDS and len(word) > 2]


def score_text(query: str, text: str) -> float:
    query_tokens = tokenize(query)
    text_tokens = tokenize(text)
    if not query_tokens or not text_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    text_counts = Counter(text_tokens)
    overlap = sum(min(query_counts[token], text_counts[token]) for token in query_counts)
    coverage = overlap / max(1, len(query_counts))
    density = overlap / max(1, len(text_counts))
    return round((coverage * 0.75) + (density * 0.25), 4)


def compact_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(f"{key}: {compact_text(item)}" for key, item in value.items())
    if isinstance(value, Iterable):
        return " ".join(compact_text(item) for item in value)
    return str(value)


def excerpt(text: str, max_chars: int = 260) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean
    return clean[: max_chars - 3].rstrip() + "..."


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)
