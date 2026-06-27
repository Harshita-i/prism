from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Protocol

from app.knowledge.models import DocumentChunk, RetrievedChunk


class VectorStore(Protocol):
    name: str

    def upsert(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Store chunk embeddings."""

    def query(self, embedding: list[float], limit: int = 8, where: dict[str, Any] | None = None) -> list[RetrievedChunk]:
        """Return semantically similar chunks."""


class ChromaVectorStore:
    name = "chroma"

    def __init__(self, path: Path, collection_name: str = "prism_knowledge") -> None:
        import chromadb
        from chromadb.config import Settings

        self.client = chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(collection_name)

    def upsert(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.text for chunk in chunks],
            metadatas=[self._metadata(chunk) for chunk in chunks],
        )

    def query(self, embedding: list[float], limit: int = 8, where: dict[str, Any] | None = None) -> list[RetrievedChunk]:
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        chunks: list[RetrievedChunk] = []
        ids = result.get("ids", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        documents = result.get("documents", [[]])[0]
        distances = result.get("distances", [[]])[0]

        for index, chunk_id in enumerate(ids):
            metadata = metadatas[index] or {}
            distance = float(distances[index] or 0.0)
            relevance = max(0.0, min(1.0, 1.0 - distance))
            chunk = DocumentChunk(
                id=chunk_id,
                document_id=str(metadata.get("document_id", "")),
                title=str(metadata.get("title", "Knowledge Document")),
                source_type=str(metadata.get("source_type", "document")),
                domain=str(metadata.get("domain", "Business")),
                tags=str(metadata.get("tags", "")).split("|") if metadata.get("tags") else [],
                text=str(documents[index] or ""),
                index=int(metadata.get("index", 0)),
                version=str(metadata.get("version", "v1")),
                effective_date=metadata.get("effective_date") or None,
                expires_at=metadata.get("expires_at") or None,
                metadata={"source_path": metadata.get("source_path")},
            )
            chunks.append(RetrievedChunk(chunk=chunk, relevance=relevance))
        return chunks

    def _metadata(self, chunk: DocumentChunk) -> dict[str, Any]:
        return {
            "document_id": chunk.document_id,
            "title": chunk.title,
            "source_type": chunk.source_type,
            "domain": chunk.domain,
            "tags": "|".join(chunk.tags),
            "index": chunk.index,
            "version": chunk.version,
            "effective_date": chunk.effective_date or "",
            "expires_at": chunk.expires_at or "",
            "source_path": chunk.metadata.get("source_path") or "",
        }


class InMemoryVectorStore:
    name = "in_memory"

    def __init__(self) -> None:
        self.items: dict[str, tuple[DocumentChunk, list[float]]] = {}

    def upsert(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        for chunk, embedding in zip(chunks, embeddings):
            self.items[chunk.id] = (chunk, embedding)

    def query(self, embedding: list[float], limit: int = 8, where: dict[str, Any] | None = None) -> list[RetrievedChunk]:
        scored = []
        for chunk, stored_embedding in self.items.values():
            if where and not self._matches_where(chunk, where):
                continue
            scored.append(
                RetrievedChunk(
                    chunk=chunk,
                    relevance=max(0.0, min(1.0, self._cosine(embedding, stored_embedding))),
                )
            )
        return sorted(scored, key=lambda item: item.relevance, reverse=True)[:limit]

    def _matches_where(self, chunk: DocumentChunk, where: dict[str, Any]) -> bool:
        domain = where.get("domain")
        if isinstance(domain, str) and domain != chunk.domain:
            return False
        return True

    def _cosine(self, left: list[float], right: list[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left)) or 1.0
        right_norm = math.sqrt(sum(b * b for b in right)) or 1.0
        return dot / (left_norm * right_norm)


def create_vector_store(path: Path) -> VectorStore:
    try:
        return ChromaVectorStore(path)
    except Exception:
        return InMemoryVectorStore()
