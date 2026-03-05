"""OpenAI-compatible LLM provider."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from agent33.llm.base import LLMStreamChunk

import httpx

from agent33.connectors.boundary import (
    build_connector_boundary_executor,
    map_connector_exception,
)
from agent33.connectors.models import ConnectorRequest
from agent33.llm.base import (
    AudioBlock,
    ChatMessage,
    ImageBlock,
    LLMResponse,
    TextBlock,
    ToolCall,
    ToolCallFunction,
)

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
        self._boundary_executor = build_connector_boundary_executor(
            default_timeout_seconds=timeout,
            retry_attempts=1,
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
        connector = "llm:openai"
        operation = f"POST {path}"

        async def _perform_post() -> dict[str, Any]:
            response = await self._client.post(
                f"{self._base_url}{path}",
                json=payload,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

        async def _execute_post(_request: ConnectorRequest) -> dict[str, Any]:
            return await _perform_post()

        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                if self._boundary_executor is None:
                    return await _perform_post()
                request = ConnectorRequest(
                    connector=connector,
                    operation=operation,
                    payload=payload,
                    metadata={"base_url": self._base_url},
                )
                result = await self._boundary_executor.execute(request, _execute_post)
                return cast("dict[str, Any]", result)
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = _BACKOFF_BASE * (2**attempt)
                    logger.warning(
                        "openai request failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        _MAX_ATTEMPTS,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
            except Exception as exc:
                if self._boundary_executor is not None:
                    mapped = map_connector_exception(exc, connector, operation)
                    raise mapped from exc
                raise
        failure = RuntimeError(f"OpenAI request to {path} failed after {_MAX_ATTEMPTS} attempts")
        if self._boundary_executor is not None and last_exc is not None:
            raise map_connector_exception(last_exc, connector, operation) from last_exc
        raise failure from last_exc

    async def _get(self, path: str) -> dict[str, Any]:
        """GET with exponential-backoff retry."""
        connector = "llm:openai"
        operation = f"GET {path}"

        async def _perform_get() -> dict[str, Any]:
            response = await self._client.get(
                f"{self._base_url}{path}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]

        async def _execute_get(_request: ConnectorRequest) -> dict[str, Any]:
            return await _perform_get()

        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                if self._boundary_executor is None:
                    return await _perform_get()
                request = ConnectorRequest(
                    connector=connector,
                    operation=operation,
                    metadata={"base_url": self._base_url},
                )
                result = await self._boundary_executor.execute(request, _execute_get)
                return cast("dict[str, Any]", result)
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < _MAX_ATTEMPTS - 1:
                    delay = _BACKOFF_BASE * (2**attempt)
                    logger.warning(
                        "openai GET failed (attempt %d/%d), retrying in %.1fs: %s",
                        attempt + 1,
                        _MAX_ATTEMPTS,
                        delay,
                        exc,
                    )
                    await asyncio.sleep(delay)
            except Exception as exc:
                if self._boundary_executor is not None:
                    mapped = map_connector_exception(exc, connector, operation)
                    raise mapped from exc
                raise
        failure = RuntimeError(f"OpenAI GET {path} failed after {_MAX_ATTEMPTS} attempts")
        if self._boundary_executor is not None and last_exc is not None:
            raise map_connector_exception(last_exc, connector, operation) from last_exc
        raise failure from last_exc

    # -- public API -------------------------------------------------------

    @staticmethod
    def _serialize_message(m: ChatMessage) -> dict[str, Any]:
        """Serialize a ChatMessage to OpenAI's message format."""
        if isinstance(m.content, list):
            content: Any = []
            for part in m.content:
                if isinstance(part, TextBlock):
                    content.append({"type": "text", "text": part.text})
                elif isinstance(part, ImageBlock):
                    if part.base64_data:
                        url = f"data:{part.media_type};base64,{part.base64_data}"
                    else:
                        url = part.url or ""
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": url, "detail": part.detail},
                        }
                    )
                elif isinstance(part, AudioBlock):
                    content.append(
                        {
                            "type": "text",
                            "text": f"[Audio: {part.url or 'embedded'}]",
                        }
                    )
        else:
            content = m.content
        msg: dict[str, Any] = {"role": m.role, "content": content}
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
            payload["tools"] = [{"type": "function", "function": tool_def} for tool_def in tools]

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

    async def stream_complete(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        """Stream completion chunks via SSE."""
        from agent33.llm.base import LLMStreamChunk

        resolved_model = model or self._default_model
        body: dict[str, Any] = {
            "model": resolved_model,
            "messages": [self._serialize_message(m) for m in messages],
            "temperature": temperature,
            "stream": True,
        }
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if tools is not None:
            body["tools"] = [{"type": "function", "function": t} for t in tools]

        async with self._client.stream(
            "POST",
            f"{self._base_url}/chat/completions",
            json=body,
            headers=self._headers(),
            timeout=self._timeout,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                line = line.strip()
                if not line or line.startswith(":"):
                    continue
                if line.startswith("data: "):
                    line = line[6:]
                if line == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                choice = chunk_data.get("choices", [{}])[0]
                delta = choice.get("delta", {})
                yield LLMStreamChunk(
                    delta_content=delta.get("content", "") or "",
                    finish_reason=choice.get("finish_reason"),
                    model=chunk_data.get("model", resolved_model),
                )
