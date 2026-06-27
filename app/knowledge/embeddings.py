from __future__ import annotations

import hashlib
import math
import os
import re
from pathlib import Path
from typing import Protocol


class EmbeddingProvider(Protocol):
    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return normalized embeddings for text values."""


class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = int(self.model.get_sentence_embedding_dimension())

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [list(map(float, vector)) for vector in vectors]


class HashEmbeddingProvider:
    """
    Zero-dependency fallback.

    Chroma + sentence-transformers is preferred, but this keeps Prism working
    during demos if local ML dependencies are not installed yet.
    """

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def create_embedding_provider(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingProvider:
    if os.getenv("PRISM_KNOWLEDGE_EMBEDDINGS", "auto").lower() == "hash":
        return HashEmbeddingProvider()
    cache_root = Path(__file__).resolve().parents[2] / ".prism_knowledge" / "hf_cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(cache_root))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(cache_root))
    try:
        return SentenceTransformerEmbeddingProvider(model_name)
    except Exception:
        return HashEmbeddingProvider()
