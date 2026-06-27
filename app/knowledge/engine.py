from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.decision_context import KnowledgePacket, StructuredContext
from app.knowledge.chunker import DocumentChunker
from app.knowledge.embeddings import EmbeddingProvider, create_embedding_provider
from app.knowledge.loaders import DocumentLoader
from app.knowledge.packet_generator import KnowledgePacketGenerator
from app.knowledge.ranker import EvidenceRanker
from app.knowledge.vector_store import VectorStore, create_vector_store


class KnowledgeEngine:
    def __init__(
        self,
        *,
        storage: Any,
        root: Path,
        embedding_provider: EmbeddingProvider | None = None,
        vector_store: VectorStore | None = None,
        loader: DocumentLoader | None = None,
        chunker: DocumentChunker | None = None,
        ranker: EvidenceRanker | None = None,
        packet_generator: KnowledgePacketGenerator | None = None,
    ) -> None:
        self.storage = storage
        self.root = root
        self.embedding_provider = embedding_provider or create_embedding_provider()
        self.vector_store = vector_store or create_vector_store(root / ".prism_knowledge" / "chroma")
        self.loader = loader or DocumentLoader()
        self.chunker = chunker or DocumentChunker()
        self.ranker = ranker or EvidenceRanker()
        self.packet_generator = packet_generator or KnowledgePacketGenerator()
        self._indexed = False
        self.metadata: dict[str, Any] = {}

    def retrieve_packets(
        self,
        context: StructuredContext,
        persona: dict,
        *,
        limit: int = 4,
        retrieval_limit: int = 12,
    ) -> list[KnowledgePacket]:
        self.ensure_indexed()
        query = self._query(context, persona)
        query_embedding = self.embedding_provider.embed([query])[0]
        where = {"domain": persona.get("domain")} if persona.get("domain") and self.vector_store.name == "chroma" else None
        retrieved = self.vector_store.query(query_embedding, limit=retrieval_limit, where=where)
        if not retrieved and where:
            retrieved = self.vector_store.query(query_embedding, limit=retrieval_limit, where=None)

        ranked = self.ranker.rank(retrieved, context, persona)
        packets = self.packet_generator.generate(ranked, context, persona, limit=limit)
        self.metadata = {
            "embedding_provider": type(self.embedding_provider).__name__,
            "vector_store": self.vector_store.name,
            "query": query,
            "retrieved_chunks": len(retrieved),
            "ranked_evidence": len(ranked),
            "packets": len(packets),
        }
        return packets

    def ensure_indexed(self) -> None:
        if self._indexed:
            return

        storage_docs = []
        if hasattr(self.storage, "list_knowledge_documents"):
            storage_docs = self.storage.list_knowledge_documents()
        folder_docs = self.loader.from_folder(self.root / "knowledge_base")
        documents = [
            *self.loader.from_storage_docs(storage_docs),
            *folder_docs,
        ]
        chunks = self.chunker.chunk(documents)
        if chunks:
            embeddings = self.embedding_provider.embed([chunk.text for chunk in chunks])
            self.vector_store.upsert(chunks, embeddings)
        self._indexed = True
        self.metadata = {
            "indexed_documents": len(documents),
            "indexed_chunks": len(chunks),
            "embedding_provider": type(self.embedding_provider).__name__,
            "vector_store": self.vector_store.name,
        }

    def _query(self, context: StructuredContext, persona: dict) -> str:
        parts = [
            persona.get("id", ""),
            persona.get("label", ""),
            persona.get("domain", ""),
            persona.get("decision_type", ""),
            context.primary_problem,
            context.decision_type,
            context.urgency,
            context.sentiment,
            *context.entities,
            *context.stakeholders,
            *[signal.label for signal in context.business_signals],
            *[signal.category for signal in context.business_signals],
        ]
        return " ".join(str(part) for part in parts if part)
