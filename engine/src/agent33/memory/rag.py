"""Retrieval-Augmented Generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from agent33.memory.embeddings import EmbeddingProvider
from agent33.memory.long_term import LongTermMemory, SearchResult


@dataclass
class RAGResult:
    """Result of a RAG query."""

    augmented_prompt: str
    sources: list[SearchResult]


class RAGPipeline:
    """Query long-term memory and produce augmented context."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        long_term_memory: LongTermMemory,
        top_k: int = 5,
        similarity_threshold: float = 0.3,
    ) -> None:
        self._embedder = embedding_provider
        self._memory = long_term_memory
        self._top_k = top_k
        self._threshold = similarity_threshold

    async def query(self, text: str) -> RAGResult:
        """Embed *text*, search memory, and return augmented context."""
        query_embedding = await self._embedder.embed(text)
        results = await self._memory.search(query_embedding, top_k=self._top_k)

        # Filter by similarity threshold.
        relevant = [r for r in results if r.score >= self._threshold]

        if not relevant:
            return RAGResult(augmented_prompt=text, sources=[])

        context_parts: list[str] = []
        for i, r in enumerate(relevant, 1):
            context_parts.append(f"[Source {i}] {r.text}")

        context_block = "\n\n".join(context_parts)
        augmented = (
            f"Use the following context to answer the question.\n\n"
            f"---Context---\n{context_block}\n---End Context---\n\n"
            f"Question: {text}"
        )
        return RAGResult(augmented_prompt=augmented, sources=relevant)
