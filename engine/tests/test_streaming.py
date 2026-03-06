"""Targeted tests for token-level streaming."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent33.agents.events import ToolLoopEvent
from agent33.llm.base import (
    ChatMessage,
    LLMResponse,
    LLMStreamChunk,
    ToolCall,
    ToolCallDelta,
    ToolCallFunction,
)
from agent33.llm.ollama import OllamaProvider
from agent33.llm.openai import OpenAIProvider

if TYPE_CHECKING:
    from agent33.connectors.models import ConnectorRequest


class _StreamResponse:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    async def __aenter__(self) -> _StreamResponse:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    def raise_for_status(self) -> None:
        return None

    async def aiter_lines(self):  # type: ignore[no-untyped-def]
        for line in self._lines:
            yield line


class _OpenAIStreamClient:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def stream(self, *args: Any, **kwargs: Any) -> _StreamResponse:
        return _StreamResponse(self._lines)

    async def aclose(self) -> None:
        return None


class _OllamaStreamClient:
    def __init__(self, *, lines: list[str]) -> None:
        self._lines = lines
        self.last_json: dict[str, Any] | None = None

    def stream(self, *args: Any, **kwargs: Any) -> _StreamResponse:
        self.last_json = kwargs.get("json")
        return _StreamResponse(self._lines)

    async def aclose(self) -> None:
        return None


class _BoundaryExecutor:
    def __init__(self, *, failure: Exception | None = None) -> None:
        self.failure = failure
        self.calls: list[ConnectorRequest] = []

    async def execute(self, request: ConnectorRequest, handler: Any) -> Any:
        self.calls.append(request)
        if self.failure is not None:
            raise self.failure
        return await handler(request)


def _make_registry(*tools: MagicMock) -> MagicMock:
    registry = MagicMock()
    registry.list_all.return_value = list(tools)
    registry.get_entry.return_value = None

    async def _validated_execute(name: str, params: dict[str, Any], context: Any) -> Any:
        for tool in tools:
            if tool.name == name:
                return await tool.execute(params, context)
        raise AssertionError(f"unknown tool: {name}")

    registry.validated_execute = AsyncMock(side_effect=_validated_execute)
    return registry


def _make_tool(name: str = "shell") -> MagicMock:
    from agent33.tools.base import ToolResult

    tool = MagicMock()
    tool.name = name
    tool.description = "mock tool"
    tool.execute = AsyncMock(return_value=ToolResult.ok("ok"))
    return tool


def _messages() -> list[ChatMessage]:
    return [ChatMessage(role="user", content="hello")]


@pytest.mark.asyncio
async def test_openai_stream_complete_emits_tool_call_deltas() -> None:
    provider = OpenAIProvider(api_key="test-key", base_url="http://example.com/v1")
    provider._client = _OpenAIStreamClient(
        [
            'data: {"choices":[{"delta":{"content":"Hello "}}],"model":"gpt-4o"}',
            (
                'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"call_1",'
                '"function":{"name":"shell","arguments":"{\\"command\\": "}}]}}],'
                '"model":"gpt-4o"}'
            ),
            (
                'data: {"choices":[{"delta":{"tool_calls":[{"index":0,'
                '"function":{"arguments":"\\"dir\\"}"}}]},"finish_reason":"tool_calls"}],'
                '"model":"gpt-4o"}'
            ),
            "data: [DONE]",
        ]
    )  # type: ignore[assignment]

    chunks = [chunk async for chunk in provider.stream_complete(_messages(), model="gpt-4o")]

    assert chunks[0].delta_content == "Hello "
    tool_deltas = [chunk.tool_call_delta for chunk in chunks if chunk.tool_call_delta is not None]
    assert len(tool_deltas) == 2
    assert tool_deltas[0].name == "shell"
    assert tool_deltas[1].arguments_fragment == '"dir"}'
    await provider.close()


@pytest.mark.asyncio
async def test_openai_stream_complete_uses_connector_boundary_executor() -> None:
    provider = OpenAIProvider(api_key="test-key", base_url="http://example.com/v1")
    provider._client = _OpenAIStreamClient(
        [
            'data: {"choices":[{"delta":{"content":"Hello"}}],"model":"gpt-4o"}',
            "data: [DONE]",
        ]
    )  # type: ignore[assignment]
    boundary = _BoundaryExecutor()
    provider._boundary_executor = boundary  # type: ignore[assignment]

    chunks = [chunk async for chunk in provider.stream_complete(_messages(), model="gpt-4o")]

    assert [chunk.delta_content for chunk in chunks] == ["Hello"]
    assert len(boundary.calls) == 1
    request = boundary.calls[0]
    assert request.connector == "llm:openai"
    assert request.operation == "POST /chat/completions"
    assert request.payload["stream"] is True
    await provider.close()


@pytest.mark.asyncio
async def test_ollama_stream_complete_sends_tools_and_emits_tool_delta() -> None:
    client = _OllamaStreamClient(
        lines=[
            json.dumps(
                {
                    "model": "llama3.2",
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "function": {
                                    "name": "shell",
                                    "arguments": {"command": "pwd"},
                                },
                            }
                        ]
                    },
                    "done": True,
                }
            )
        ]
    )
    provider = OllamaProvider(base_url="http://localhost:11434")
    provider._client = client  # type: ignore[assignment]

    chunks = [
        chunk
        async for chunk in provider.stream_complete(
            _messages(),
            model="llama3.2",
            tools=[{"name": "shell", "parameters": {"type": "object"}}],
        )
    ]

    assert client.last_json is not None
    assert "tools" in client.last_json
    tool_deltas = [chunk.tool_call_delta for chunk in chunks if chunk.tool_call_delta is not None]
    assert len(tool_deltas) == 1
    assert tool_deltas[0].name == "shell"
    assert tool_deltas[0].arguments_fragment == '{"command": "pwd"}'
    await provider.close()


@pytest.mark.asyncio
async def test_ollama_stream_complete_propagates_boundary_blocking_error() -> None:
    provider = OllamaProvider(base_url="http://localhost:11434")
    provider._client = _OllamaStreamClient(lines=[])  # type: ignore[assignment]
    provider._boundary_executor = _BoundaryExecutor(
        failure=PermissionError("blocked by policy")
    )  # type: ignore[assignment]

    with pytest.raises(
        RuntimeError,
        match="Connector governance blocked llm:ollama/POST /api/chat",
    ):
        _ = [chunk async for chunk in provider.stream_complete(_messages(), model="llama3.2")]

    await provider.close()


@pytest.mark.asyncio
async def test_tool_loop_stream_uses_token_streaming_before_tool_execution() -> None:
    from agent33.agents.tool_loop import ToolLoop, ToolLoopConfig

    tool = _make_tool("shell")
    registry = _make_registry(tool)

    router = MagicMock()
    router.complete = AsyncMock(
        return_value=LLMResponse(
            content="",
            model="test-model",
            prompt_tokens=10,
            completion_tokens=5,
            tool_calls=[
                ToolCall(
                    id="call_1",
                    function=ToolCallFunction(name="shell", arguments='{"command": "pwd"}'),
                )
            ],
            finish_reason="tool_calls",
        )
    )

    async def _stream_complete(*args: Any, **kwargs: Any):  # noqa: ARG001
        yield LLMStreamChunk(delta_content="Thinking ")
        yield LLMStreamChunk(
            tool_call_delta=ToolCallDelta(
                index=0,
                id="call_1",
                name="shell",
                arguments_fragment='{"command": "pwd"}',
            ),
            finish_reason="tool_calls",
            model="test-model",
        )

    router.stream_complete = _stream_complete

    loop = ToolLoop(
        router=router,
        tool_registry=registry,
        config=ToolLoopConfig(max_iterations=1, enable_double_confirmation=False),
    )

    events = [event async for event in loop.run_stream(_messages(), model="test-model")]

    assert any(event.event_type == "llm_token" for event in events)
    assert any(event.event_type == "tool_call_requested" for event in events)
    assert router.complete.await_count == 0


@pytest.mark.asyncio
async def test_tool_loop_stream_falls_back_to_complete_when_streaming_unsupported() -> None:
    from agent33.agents.tool_loop import ToolLoop, ToolLoopConfig

    router = MagicMock()
    router.complete = AsyncMock(
        return_value=LLMResponse(
            content="done",
            model="test-model",
            prompt_tokens=3,
            completion_tokens=2,
            tool_calls=None,
            finish_reason="stop",
        )
    )

    async def _unsupported_stream_complete(*args: Any, **kwargs: Any):  # noqa: ARG001
        raise NotImplementedError
        yield  # pragma: no cover

    router.stream_complete = _unsupported_stream_complete

    loop = ToolLoop(
        router=router,
        tool_registry=_make_registry(),
        config=ToolLoopConfig(max_iterations=1, enable_double_confirmation=False),
    )

    events = [event async for event in loop.run_stream(_messages(), model="test-model")]

    assert isinstance(events[-1], ToolLoopEvent)
    assert events[-1].event_type == "completed"
    assert events[-1].data["termination_reason"] == "natural"
    assert router.complete.await_count == 1
