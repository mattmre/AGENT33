"""Retrieval-Augmented Generation pipeline.

Supports both vector-only and hybrid (BM25 + vector) retrieval modes.
When a :class:`HybridSearcher` is provided, the pipeline uses Reciprocal
Rank Fusion for higher-quality retrieval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.memory.embeddings import EmbeddingProvider
    from agent33.memory.hybrid import HybridSearcher
    from agent33.memory.long_term import LongTermMemory


@dataclass
class RAGResult:
    """Result of a RAG query."""

    augmented_prompt: str
    sources: list[RAGSource]


@dataclass
class RAGSource:
    """A single source document from RAG retrieval."""

    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)
    retrieval_method: str = "vector"


class RAGPipeline:
    """Query long-term memory and produce augmented context.

    Parameters
    ----------
    embedding_provider:
        Used to embed queries for vector search.
    long_term_memory:
        The pgvector-backed semantic memory store.
    top_k:
        Number of results to retrieve (default 5).
    similarity_threshold:
        Minimum score to include a result (default 0.3).
        Applied to vector scores in vector-only mode; in hybrid mode
        all RRF results above 0 are included.
    hybrid_searcher:
        Optional hybrid searcher.  When provided, the pipeline uses
        hybrid BM25 + vector retrieval instead of vector-only.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        long_term_memory: LongTermMemory,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
        hybrid_searcher: HybridSearcher | None = None,
    ) -> None:
        self._embedder = embedding_provider
        self._memory = long_term_memory
        self._top_k = top_k
        self._threshold = similarity_threshold
        self._hybrid = hybrid_searcher

    async def query(self, text: str) -> RAGResult:
        """Embed *text*, search memory, and return augmented context."""
        if self._hybrid is not None:
            return await self._query_hybrid(text)
        return await self._query_vector(text)

    # ── Vector-only retrieval ────────────────────────────────────────

    async def _query_vector(self, text: str) -> RAGResult:
        """Original vector-only retrieval path."""
        query_embedding = await self._embedder.embed(text)
        results = await self._memory.search(query_embedding, top_k=self._top_k)

        relevant = [r for r in results if r.score >= self._threshold]
        if not relevant:
            return RAGResult(augmented_prompt=text, sources=[])

        sources = [
            RAGSource(
                text=r.text,
                score=r.score,
                metadata=r.metadata,
                retrieval_method="vector",
            )
            for r in relevant
        ]
        return RAGResult(
            augmented_prompt=self._format_prompt(text, sources),
            sources=sources,
        )

    # ── Hybrid retrieval ─────────────────────────────────────────────

    async def _query_hybrid(self, text: str) -> RAGResult:
        """Hybrid BM25 + vector retrieval path."""
        assert self._hybrid is not None
        results = await self._hybrid.search(text, top_k=self._top_k)

        if not results:
            return RAGResult(augmented_prompt=text, sources=[])

        sources = [
            RAGSource(
                text=r.text,
                score=r.score,
                metadata=r.metadata,
                retrieval_method="hybrid",
            )
            for r in results
        ]
        return RAGResult(
            augmented_prompt=self._format_prompt(text, sources),
            sources=sources,
        )

    # ── Prompt formatting ────────────────────────────────────────────

    @staticmethod
    def _format_prompt(question: str, sources: list[RAGSource]) -> str:
        """Build the augmented prompt with context block."""
        context_parts: list[str] = []
        for i, src in enumerate(sources, 1):
            context_parts.append(f"[Source {i}] {src.text}")

        context_block = "\n\n".join(context_parts)
        return (
            f"Use the following context to answer the question.\n\n"
            f"---Context---\n{context_block}\n---End Context---\n\n"
            f"Question: {question}"
        )
