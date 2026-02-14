"""Ollama LLM provider."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from agent33.llm.base import ChatMessage, LLMResponse

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "http://localhost:11434"
_MAX_ATTEMPTS = 3
_BACKOFF_BASE = 1.0
_DEFAULT_TIMEOUT = 120.0


class OllamaProvider:
    """LLM provider that talks to a local or remote Ollama instance."""

    def __init__(
        self,
        base_url: str = _DEFAULT_BASE_URL,
        default_model: str = "llama3.2",
        timeout: float = _DEFAULT_TIMEOUT,
        max_connections: int = 20,
        max_keepalive_connections: int = 10,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._default_model = default_model
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            ),
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    # -- helpers ----------------------------------------------------------

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST with exponential-backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = await self._client.post(
                    f"{self._base_url}{path}", json=payload
                )
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = _BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "ollama request failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        _MAX_ATTEMPTS,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
        raise RuntimeError(
            f"Ollama request to {path} failed after {_MAX_ATTEMPTS} attempts"
        ) from last_exc

    async def _get(self, path: str) -> dict[str, Any]:
        """GET with exponential-backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = await self._client.get(f"{self._base_url}{path}")
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = _BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "ollama GET failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        _MAX_ATTEMPTS,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
        raise RuntimeError(
            f"Ollama GET {path} failed after {_MAX_ATTEMPTS} attempts"
        ) from last_exc

    # -- public API -------------------------------------------------------

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a chat completion via Ollama."""
        resolved_model = model or self._default_model
        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if max_tokens is not None:
            payload["options"]["num_predict"] = max_tokens

        data = await self._post("/api/chat", payload)

        content = data.get("message", {}).get("content", "")
        return LLMResponse(
            content=content,
            model=resolved_model,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
        )

    async def list_models(self) -> list[str]:
        """Return model names available on the Ollama instance."""
        data = await self._get("/api/tags")
        models: list[dict[str, Any]] = data.get("models", [])
        return [m["name"] for m in models if "name" in m]
