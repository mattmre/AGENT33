"""OpenAI-compatible LLM provider."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from agent33.llm.base import ChatMessage, LLMResponse, ToolCall, ToolCallFunction

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://api.openai.com/v1"
_MAX_ATTEMPTS = 3
_BACKOFF_BASE = 1.0
_DEFAULT_TIMEOUT = 120.0


class OpenAIProvider:
    """LLM provider for OpenAI and OpenAI-compatible APIs."""

    def __init__(
        self,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        default_model: str = "gpt-4o",
        timeout: float = _DEFAULT_TIMEOUT,
        max_connections: int = 20,
        max_keepalive_connections: int = 10,
    ) -> None:
        self._api_key = api_key
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

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    # -- helpers ----------------------------------------------------------

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        """POST with exponential-backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = await self._client.post(
                    f"{self._base_url}{path}",
                    json=payload,
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = _BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "openai request failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        _MAX_ATTEMPTS,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
        raise RuntimeError(
            f"OpenAI request to {path} failed after {_MAX_ATTEMPTS} attempts"
        ) from last_exc

    async def _get(self, path: str) -> dict[str, Any]:
        """GET with exponential-backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                response = await self._client.get(
                    f"{self._base_url}{path}",
                    headers=self._headers(),
                )
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = _BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        "openai GET failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        _MAX_ATTEMPTS,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
        raise RuntimeError(
            f"OpenAI GET {path} failed after {_MAX_ATTEMPTS} attempts"
        ) from last_exc

    # -- public API -------------------------------------------------------

    @staticmethod
    def _serialize_message(m: ChatMessage) -> dict[str, Any]:
        """Serialize a ChatMessage to OpenAI's message format."""
        msg: dict[str, Any] = {"role": m.role, "content": m.content}
        # Include tool_calls on assistant messages when present
        if m.tool_calls:
            msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in m.tool_calls
            ]
        # Include tool_call_id and name on tool result messages
        if m.tool_call_id:
            msg["tool_call_id"] = m.tool_call_id
        if m.name:
            msg["name"] = m.name
        return msg

    @staticmethod
    def _parse_tool_calls(raw_calls: list[dict[str, Any]]) -> list[ToolCall]:
        """Parse tool calls from an OpenAI response message."""
        result: list[ToolCall] = []
        for tc in raw_calls:
            func_data = tc.get("function", {})
            result.append(
                ToolCall(
                    id=tc.get("id", ""),
                    function=ToolCallFunction(
                        name=func_data.get("name", ""),
                        arguments=func_data.get("arguments", "{}"),
                    ),
                )
            )
        return result

    async def complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        """Generate a chat completion via the OpenAI API."""
        resolved_model = model or self._default_model
        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": [self._serialize_message(m) for m in messages],
            "temperature": temperature,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            # Wrap each tool dict in the OpenAI function tool format
            payload["tools"] = [
                {"type": "function", "function": tool_def} for tool_def in tools
            ]

        data = await self._post("/chat/completions", payload)

        choices = data.get("choices", [])
        if not choices:
            return LLMResponse(
                content="",
                model=resolved_model,
                prompt_tokens=data.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=data.get("usage", {}).get("completion_tokens", 0),
            )

        choice = choices[0]
        message_data = choice.get("message", {})
        content = message_data.get("content") or ""
        finish = choice.get("finish_reason", "stop")

        # Parse tool calls from response if present
        raw_tool_calls = message_data.get("tool_calls")
        parsed_tool_calls: list[ToolCall] | None = None
        if raw_tool_calls:
            parsed_tool_calls = self._parse_tool_calls(raw_tool_calls)
            # OpenAI uses "tool_calls" as the finish_reason
            if finish in ("tool_calls", "function_call"):
                finish = "tool_calls"

        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            model=resolved_model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            tool_calls=parsed_tool_calls,
            finish_reason=finish,
        )

    async def list_models(self) -> list[str]:
        """Return available model identifiers from the API."""
        data = await self._get("/models")
        models: list[dict[str, Any]] = data.get("data", [])
        return [m["id"] for m in models if "id" in m]
