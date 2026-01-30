"""Jina Embeddings API provider."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from agent33.config import settings

logger = logging.getLogger(__name__)

_JINA_EMBED_URL = "https://api.jina.ai/v1/embeddings"


class JinaEmbeddingProvider:
    """Generate embeddings via the Jina Embeddings API."""

    def __init__(self, model: str = "jina-embeddings-v3") -> None:
        self.model = model

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.jina_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def embed(self, text: str) -> list[float]:
        """Embed a single text string."""
        result = await self.embed_batch([text])
        return result[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts in a single API call."""
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                _JINA_EMBED_URL,
                headers=self._headers(),
                json={"model": self.model, "input": texts},
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            # Sort by index to preserve order
            embeddings = sorted(data["data"], key=lambda x: x["index"])
            return [e["embedding"] for e in embeddings]
