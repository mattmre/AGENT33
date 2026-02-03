"""Embedding provider using Ollama /api/embeddings endpoint."""

from __future__ import annotations

import httpx

from agent33.config import settings

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "nomic-embed-text"
_DEFAULT_TIMEOUT = 60.0

# Global provider instance
_provider: "EmbeddingProvider | None" = None


async def get_embedding(text: str) -> list[float]:
    """Get embedding for a single text using the default provider.

    This is a convenience function for common use cases.
    """
    global _provider
    if _provider is None:
        _provider = EmbeddingProvider(
            base_url=settings.ollama_base_url,
            model="nomic-embed-text",
        )
    return await _provider.embed(text)


async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Get embeddings for multiple texts using the default provider."""
    global _provider
    if _provider is None:
        _provider = EmbeddingProvider(
            base_url=settings.ollama_base_url,
            model="nomic-embed-text",
        )
    return await _provider.embed_batch(texts)


class EmbeddingProvider:
    """Generates text embeddings via Ollama."""

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        model: str = _DEFAULT_MODEL,
        timeout: float = _DEFAULT_TIMEOUT,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text."""
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/api/embeddings",
                json={"model": self._model, "prompt": text},
            )
            response.raise_for_status()
            data = response.json()
        return data["embedding"]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts sequentially."""
        results: list[list[float]] = []
        for t in texts:
            results.append(await self.embed(t))
        return results
