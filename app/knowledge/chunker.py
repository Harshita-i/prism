from __future__ import annotations

import re

from app.knowledge.models import DocumentChunk, KnowledgeDocument


class DocumentChunker:
    def __init__(self, max_words: int = 150, overlap_words: int = 30) -> None:
        self.max_words = max_words
        self.overlap_words = overlap_words

    def chunk(self, documents: list[KnowledgeDocument]) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        for document in documents:
            words = self._words(document.content)
            if not words:
                continue

            step = max(1, self.max_words - self.overlap_words)
            index = 0
            for start in range(0, len(words), step):
                part = words[start : start + self.max_words]
                if not part:
                    continue
                chunk_id = f"{document.id}::chunk-{index}"
                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        document_id=document.id,
                        title=document.title,
                        source_type=document.source_type,
                        domain=document.domain,
                        tags=document.tags,
                        text=" ".join(part),
                        index=index,
                        version=document.version,
                        effective_date=document.effective_date,
                        expires_at=document.expires_at,
                        metadata=document.metadata,
                    )
                )
                index += 1
                if start + self.max_words >= len(words):
                    break
        return chunks

    def _words(self, text: str) -> list[str]:
        return re.findall(r"\S+", " ".join(text.split()))
