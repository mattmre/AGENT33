"""Tests for Phase 38 Stage 2: token-level LLM streaming with tool call reassembly.

Covers:
- ToolCallDelta construction and immutability
- ToolCallAssembler (imported via agent33.llm.streaming) fragment accumulation
- LLMStreamChunk with populated delta_tool_calls
- LLMTokenEvent dataclass
- OpenAI provider: SSE tool-call delta parsing + assembler integration
- Ollama provider: full tool-call object emission
- run_stream(): llm_token events, NotImplementedError fallback, delta reassembly
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent33.agents.events import LLMTokenEvent
from agent33.llm.base import (
    ChatMessage,
    LLMStreamChunk,
    ToolCallDelta,
)
from agent33.llm.streaming import ToolCallAssembler

# ---------------------------------------------------------------------------
# ToolCallDelta
# ---------------------------------------------------------------------------


class TestToolCallDelta:
    def test_construction_defaults(self) -> None:
        delta = ToolCallDelta(index=0)
        assert delta.index == 0
        assert delta.id == ""
        assert delta.function_name == ""
        assert delta.arguments_delta == ""

    def test_construction_all_fields(self) -> None:
        delta = ToolCallDelta(
            index=2,
            id="call_xyz",
            function_name="my_tool",
            arguments_delta='{"key": "val',
        )
        assert delta.index == 2
        assert delta.id == "call_xyz"
        assert delta.function_name == "my_tool"
        assert delta.arguments_delta == '{"key": "val'

    def test_frozen_prevents_mutation(self) -> None:
        delta = ToolCallDelta(index=0, id="original")
        with pytest.raises(AttributeError):
            delta.id = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# ToolCallAssembler (via agent33.llm.streaming import)
# ---------------------------------------------------------------------------


class TestToolCallAssembler:
    def test_streaming_module_exports_assembler(self) -> None:
        """agent33.llm.streaming must export ToolCallAssembler."""
        from agent33.llm.stream_assembler import ToolCallAssembler as CoreTCA
        from agent33.llm.streaming import ToolCallAssembler as StreamingTCA

        assert StreamingTCA is CoreTCA

    def test_feed_single_delta_sets_pending(self) -> None:
        asm = ToolCallAssembler()
        assert not asm.has_pending
        asm.feed([ToolCallDelta(index=0, id="c1", function_name="shell")])
        assert asm.has_pending

    def test_feed_accumulates_argument_fragments(self) -> None:
        asm = ToolCallAssembler()
        asm.feed([ToolCallDelta(index=0, id="c1", function_name="run")])
        asm.feed([ToolCallDelta(index=0, arguments_delta='{"cmd"')])
        asm.feed([ToolCallDelta(index=0, arguments_delta=': "ls"}')])
        result = asm.finalize()
        assert result[0].function.arguments == '{"cmd": "ls"}'

    def test_finalize_returns_complete_tool_calls(self) -> None:
        from agent33.llm.base import ToolCall

        asm = ToolCallAssembler()
        asm.feed([ToolCallDelta(index=0, id="call_1", function_name="greet")])
        asm.feed([ToolCallDelta(index=0, arguments_delta='{"name": "Alice"}')])
        result = asm.finalize()
        assert len(result) == 1
        assert isinstance(result[0], ToolCall)
        assert result[0].id == "call_1"
        assert result[0].function.name == "greet"
        assert result[0].function.arguments == '{"name": "Alice"}'

    def test_assembler_handles_partial_json_fragments(self) -> None:
        """Assembler concatenates raw JSON fragments without early parsing."""
        asm = ToolCallAssembler()
        asm.feed([ToolCallDelta(index=0, id="c1", function_name="calc")])
        # Stream JSON in small pieces
        for fragment in ['{"op"', ': "add"', ', "val": 42}']:
            asm.feed([ToolCallDelta(index=0, arguments_delta=fragment)])
        result = asm.finalize()
        assert result[0].function.arguments == '{"op": "add", "val": 42}'

    def test_finalize_clears_pending_state(self) -> None:
        asm = ToolCallAssembler()
        asm.feed([ToolCallDelta(index=0, id="c1", function_name="f")])
        assert asm.has_pending
        asm.finalize()
        assert not asm.has_pending

    def test_multiple_tool_calls_sorted_by_index(self) -> None:
        asm = ToolCallAssembler()
        asm.feed([
            ToolCallDelta(index=1, id="c1", function_name="write"),
            ToolCallDelta(index=0, id="c0", function_name="read"),
        ])
        asm.feed([ToolCallDelta(index=0, arguments_delta='{"path":"a"}')])
        asm.feed([ToolCallDelta(index=1, arguments_delta='{"path":"b"}')])
        result = asm.finalize()
        assert len(result) == 2
        assert result[0].function.name == "read"
        assert result[1].function.name == "write"

    def test_reset_discards_all_deltas(self) -> None:
        asm = ToolCallAssembler()
        asm.feed([ToolCallDelta(index=0, id="c1", function_name="x")])
        asm.reset()
        assert not asm.has_pending
        assert asm.finalize() == []


# ---------------------------------------------------------------------------
# LLMStreamChunk with delta_tool_calls
# ---------------------------------------------------------------------------


class TestLLMStreamChunkWithDeltas:
    def test_chunk_with_tool_call_delta(self) -> None:
        delta = ToolCallDelta(index=0, id="c1", function_name="shell")
        chunk = LLMStreamChunk(delta_tool_calls=[delta])
        assert len(chunk.delta_tool_calls) == 1
        assert chunk.delta_tool_calls[0].id == "c1"
        assert chunk.delta_tool_calls[0].function_name == "shell"

    def test_chunk_content_alongside_tool_call_delta(self) -> None:
        delta = ToolCallDelta(index=0, arguments_delta='{"x": 1}')
        chunk = LLMStreamChunk(
            delta_content="Thinking...",
            delta_tool_calls=[delta],
        )
        assert chunk.delta_content == "Thinking..."
        assert chunk.delta_tool_calls[0].arguments_delta == '{"x": 1}'

    def test_chunk_defaults_empty_tool_calls_list(self) -> None:
        chunk = LLMStreamChunk(delta_content="hello")
        assert chunk.delta_tool_calls == []
        assert chunk.finish_reason is None


# ---------------------------------------------------------------------------
# LLMTokenEvent
# ---------------------------------------------------------------------------


class TestLLMTokenEvent:
    def test_defaults(self) -> None:
        event = LLMTokenEvent()
        assert event.event_type == "llm_token"
        assert event.delta == ""
        assert event.run_id == ""

    def test_with_all_fields(self) -> None:
        event = LLMTokenEvent(delta="Hello", run_id="run-abc-123")
        assert event.delta == "Hello"
        assert event.run_id == "run-abc-123"
        assert event.event_type == "llm_token"

    def test_frozen_prevents_mutation(self) -> None:
        event = LLMTokenEvent(delta="x")
        with pytest.raises(AttributeError):
            event.delta = "mutated"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# OpenAI provider: SSE tool-call delta parsing
# ---------------------------------------------------------------------------


def _make_openai_mock_stream(sse_lines: list[str]) -> Any:
    """Build a mock httpx streaming context manager yielding the given SSE lines."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    async def _aiter_lines() -> Any:
        for line in sse_lines:
            yield line

    mock_resp.aiter_lines = _aiter_lines
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


class TestOpenAIProviderStreaming:
    async def test_content_delta_chunks_emitted(self) -> None:
        """OpenAI SSE content deltas are yielded as LLMStreamChunk objects."""
        from agent33.llm.openai import OpenAIProvider

        sse_lines = [
            "data: " + '{"choices":[{"delta":{"content":"Hello"},"finish_reason":null,"index":0}],"model":"gpt-4"}',  # noqa: E501
            "data: " + '{"choices":[{"delta":{"content":" world"},"finish_reason":null,"index":0}],"model":"gpt-4"}',  # noqa: E501
            'data: {"choices":[{"delta":{},"finish_reason":"stop","index":0}],"model":"gpt-4"}',
            "data: [DONE]",
        ]
        provider = OpenAIProvider(api_key="test-key", base_url="http://fake")
        provider._client.stream = MagicMock(
            return_value=_make_openai_mock_stream(sse_lines)
        )

        chunks = [
            c
            async for c in provider.stream_complete(
                [ChatMessage(role="user", content="hi")],
                model="gpt-4",
            )
        ]

        content = "".join(c.delta_content for c in chunks)
        assert "Hello" in content
        assert " world" in content

    async def test_tool_call_deltas_populated(self) -> None:
        """OpenAI SSE tool_call deltas populate delta_tool_calls on chunks."""
        from agent33.llm.openai import OpenAIProvider

        sse_lines = [
            json.dumps({
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "id": "call_1",
                            "function": {"name": "shell", "arguments": ""},
                        }]
                    },
                    "finish_reason": None,
                }],
                "model": "gpt-4",
            }),
            json.dumps({
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "function": {"arguments": '{"cmd":'},
                        }]
                    },
                    "finish_reason": None,
                }],
                "model": "gpt-4",
            }),
            json.dumps({
                "choices": [{
                    "delta": {
                        "tool_calls": [{
                            "index": 0,
                            "function": {"arguments": '"ls"}'},
                        }]
                    },
                    "finish_reason": "tool_calls",
                }],
                "model": "gpt-4",
            }),
            "data: [DONE]",
        ]
        # Prefix SSE data: lines
        sse_lines = [f"data: {ln}" if not ln.startswith("data:") else ln for ln in sse_lines]

        provider = OpenAIProvider(api_key="test-key", base_url="http://fake")
        provider._client.stream = MagicMock(
            return_value=_make_openai_mock_stream(sse_lines)
        )

        chunks = [
            c
            async for c in provider.stream_complete(
                [ChatMessage(role="user", content="run ls")],
                model="gpt-4",
            )
        ]

        tc_chunks = [c for c in chunks if c.delta_tool_calls]
        assert len(tc_chunks) >= 1
        first_tc = tc_chunks[0].delta_tool_calls[0]
        assert first_tc.id == "call_1"
        assert first_tc.function_name == "shell"

    async def test_assembler_integration_with_openai_stream(self) -> None:
        """OpenAI streamed deltas assemble into a complete ToolCall."""
        from agent33.llm.openai import OpenAIProvider

        sse_lines = [
            json.dumps({
                "choices": [{
                    "delta": {"tool_calls": [{"index": 0, "id": "c1", "function": {
                        "name": "greet", "arguments": "",
                    }}]},
                    "finish_reason": None,
                }],
                "model": "gpt-4",
            }),
            json.dumps({
                "choices": [{
                    "delta": {"tool_calls": [{"index": 0, "function": {"arguments": '{"name"'}}]},
                    "finish_reason": None,
                }],
                "model": "gpt-4",
            }),
            json.dumps({
                "choices": [{
                    "delta": {  # noqa: E501
                        "tool_calls": [{"index": 0, "function": {"arguments": ': "Alice"}'}}],
                    },
                    "finish_reason": "tool_calls",
                }],
                "model": "gpt-4",
            }),
            "data: [DONE]",
        ]
        sse_lines = [f"data: {ln}" if not ln.startswith("data:") else ln for ln in sse_lines]

        provider = OpenAIProvider(api_key="test-key", base_url="http://fake")
        provider._client.stream = MagicMock(
            return_value=_make_openai_mock_stream(sse_lines)
        )

        asm = ToolCallAssembler()
        async for chunk in provider.stream_complete(
            [ChatMessage(role="user", content="greet Alice")],
            model="gpt-4",
        ):
            if chunk.delta_tool_calls:
                asm.feed(chunk.delta_tool_calls)

        result = asm.finalize()
        assert len(result) == 1
        assert result[0].function.name == "greet"
        assert result[0].function.arguments == '{"name": "Alice"}'

    async def test_finish_reason_stop_emitted(self) -> None:
        """OpenAI stream chunk with finish_reason='stop' is yielded."""
        from agent33.llm.openai import OpenAIProvider

        sse_lines = [
            "data: " + '{"choices":[{"delta":{"content":"done"},"finish_reason":"stop","index":0}],"model":"gpt-4"}',  # noqa: E501
            "data: [DONE]",
        ]
        provider = OpenAIProvider(api_key="test-key", base_url="http://fake")
        provider._client.stream = MagicMock(
            return_value=_make_openai_mock_stream(sse_lines)
        )

        chunks = [
            c
            async for c in provider.stream_complete(
                [ChatMessage(role="user", content="go")],
                model="gpt-4",
            )
        ]

        finish_chunks = [c for c in chunks if c.finish_reason is not None]
        assert len(finish_chunks) >= 1
        assert finish_chunks[-1].finish_reason == "stop"


# ---------------------------------------------------------------------------
# Ollama provider: full tool-call object emission
# ---------------------------------------------------------------------------


def _make_ollama_mock_stream(ndjson_lines: list[str]) -> Any:
    """Build a mock httpx streaming context manager yielding NDJSON lines."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()

    async def _aiter_lines() -> Any:
        for line in ndjson_lines:
            yield line

    mock_resp.aiter_lines = _aiter_lines
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_resp)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


class TestOllamaProviderStreaming:
    async def test_content_streaming_emits_chunks(self) -> None:
        """Ollama NDJSON stream yields content delta chunks."""
        from agent33.llm.ollama import OllamaProvider

        ndjson_lines = [
            '{"model":"llama3","message":{"role":"assistant","content":"Hello"},"done":false}',
            '{"model":"llama3","message":{"role":"assistant","content":" world"},"done":false}',
            '{"model":"llama3","message":{"role":"assistant","content":""},"done":true,"prompt_eval_count":10,"eval_count":5}',
        ]
        provider = OllamaProvider(base_url="http://fake")
        provider._client.stream = MagicMock(
            return_value=_make_ollama_mock_stream(ndjson_lines)
        )

        chunks = [
            c
            async for c in provider.stream_complete(
                [ChatMessage(role="user", content="hi")],
                model="llama3",
            )
        ]

        content = "".join(c.delta_content for c in chunks)
        assert "Hello" in content
        assert " world" in content
        assert chunks[-1].finish_reason == "stop"

    async def test_tool_calls_emitted_as_full_objects(self) -> None:
        """Ollama sends complete tool_call objects; provider maps them to deltas."""
        from agent33.llm.ollama import OllamaProvider

        payload = {
            "model": "llama3",
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"function": {"name": "read_file", "arguments": {"path": "/etc/hosts"}}}
                ],
            },
            "done": True,
        }
        provider = OllamaProvider(base_url="http://fake")
        provider._client.stream = MagicMock(
            return_value=_make_ollama_mock_stream([json.dumps(payload)])
        )

        chunks = [
            c
            async for c in provider.stream_complete(
                [ChatMessage(role="user", content="read hosts")],
                model="llama3",
            )
        ]

        tc_chunks = [c for c in chunks if c.delta_tool_calls]
        assert len(tc_chunks) == 1
        assert tc_chunks[0].delta_tool_calls[0].function_name == "read_file"

    async def test_ollama_tool_calls_assemble_correctly(self) -> None:
        """Ollama tool-call deltas reassemble into a usable ToolCall."""
        from agent33.llm.ollama import OllamaProvider

        payload = {
            "model": "llama3",
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "write_file",
                            "arguments": {"path": "/tmp/out.txt", "content": "hello"},
                        }
                    }
                ],
            },
            "done": True,
        }
        provider = OllamaProvider(base_url="http://fake")
        provider._client.stream = MagicMock(
            return_value=_make_ollama_mock_stream([json.dumps(payload)])
        )

        asm = ToolCallAssembler()
        async for chunk in provider.stream_complete(
            [ChatMessage(role="user", content="write")],
            model="llama3",
        ):
            if chunk.delta_tool_calls:
                asm.feed(chunk.delta_tool_calls)

        result = asm.finalize()
        assert len(result) == 1
        assert result[0].function.name == "write_file"


# ---------------------------------------------------------------------------
# run_stream() integration tests
# ---------------------------------------------------------------------------


def _make_streaming_router_from_chunks(chunks: list[LLMStreamChunk]) -> Any:
    async def _stream_complete(*args: Any, **kwargs: Any) -> Any:
        for chunk in chunks:
            yield chunk

    router = MagicMock()
    router.stream_complete = _stream_complete
    router.complete = AsyncMock()
    return router


def _make_registry_no_tools() -> Any:
    registry = MagicMock()
    registry.list_all.return_value = []
    registry.get_entry.return_value = None
    return registry


class TestRunStreamTokenEvents:
    async def test_emits_llm_token_events_for_content(self) -> None:
        """run_stream emits llm_token events for each streamed content chunk."""
        from agent33.agents.events import ToolLoopEvent
        from agent33.agents.tool_loop import ToolLoop, ToolLoopConfig

        chunks = [
            LLMStreamChunk(delta_content="Token1"),
            LLMStreamChunk(delta_content="Token2"),
            LLMStreamChunk(delta_content="Token3", finish_reason="stop"),
        ]
        router = _make_streaming_router_from_chunks(chunks)
        registry = _make_registry_no_tools()
        config = ToolLoopConfig(max_iterations=3, enable_double_confirmation=False)
        loop = ToolLoop(router=router, tool_registry=registry, config=config)

        events: list[ToolLoopEvent] = []
        async for event in loop.run_stream(
            [ChatMessage(role="user", content="go")], model="m"
        ):
            events.append(event)

        token_events = [e for e in events if e.event_type == "llm_token"]
        assert len(token_events) == 3
        assert token_events[0].data["content"] == "Token1"
        assert token_events[1].data["content"] == "Token2"
        assert token_events[2].data["content"] == "Token3"
        assert events[-1].event_type == "completed"

    async def test_fallback_to_complete_when_no_stream_complete(self) -> None:
        """run_stream falls back to complete() when router lacks stream_complete."""
        from agent33.agents.tool_loop import ToolLoop, ToolLoopConfig
        from agent33.llm.base import LLMResponse

        response = LLMResponse(
            content="fallback answer",
            model="m",
            prompt_tokens=5,
            completion_tokens=5,
        )
        router = MagicMock(spec=["complete"])
        router.complete = AsyncMock(return_value=response)
        registry = _make_registry_no_tools()
        config = ToolLoopConfig(max_iterations=3, enable_double_confirmation=False)
        loop = ToolLoop(router=router, tool_registry=registry, config=config)

        events = []
        async for event in loop.run_stream(
            [ChatMessage(role="user", content="go")], model="m"
        ):
            events.append(event)

        event_types = [e.event_type for e in events]
        assert "llm_token" not in event_types
        assert "completed" in event_types
        assert router.complete.call_count == 1

    async def test_fallback_when_stream_complete_raises_not_implemented(self) -> None:
        """run_stream falls back to complete() when stream_complete raises NotImplementedError."""
        from agent33.agents.tool_loop import ToolLoop, ToolLoopConfig
        from agent33.llm.base import LLMResponse

        async def _raising_stream(*args: Any, **kwargs: Any) -> Any:
            msg = "streaming not supported by this provider"
            raise NotImplementedError(msg)
            yield  # type: ignore[misc]  # pragma: no cover

        response = LLMResponse(
            content="fallback content",
            model="m",
            prompt_tokens=5,
            completion_tokens=5,
        )
        router = MagicMock()
        router.stream_complete = _raising_stream
        router.complete = AsyncMock(return_value=response)
        registry = _make_registry_no_tools()
        config = ToolLoopConfig(max_iterations=3, enable_double_confirmation=False)
        loop = ToolLoop(router=router, tool_registry=registry, config=config)

        events = []
        async for event in loop.run_stream(
            [ChatMessage(role="user", content="go")], model="m"
        ):
            events.append(event)

        # complete() must have been called as the fallback
        assert router.complete.call_count >= 1
        event_types = [e.event_type for e in events]
        assert "completed" in event_types
        # NotImplementedError must NOT surface as an error event
        assert "error" not in event_types

    async def test_run_stream_assembles_tool_calls_from_deltas(self) -> None:
        """run_stream reassembles streamed tool-call deltas and dispatches the tool."""
        from agent33.agents.tool_loop import ToolLoop, ToolLoopConfig
        from agent33.tools.base import ToolResult

        call1_chunks = [
            LLMStreamChunk(
                delta_tool_calls=[ToolCallDelta(index=0, id="c1", function_name="shell")]
            ),
            LLMStreamChunk(
                delta_tool_calls=[ToolCallDelta(index=0, arguments_delta='{"cmd":"ls"}')]
            ),
            LLMStreamChunk(finish_reason="stop"),
        ]
        call2_chunks = [
            LLMStreamChunk(delta_content="Done!", finish_reason="stop"),
        ]

        call_count = 0

        async def _stream_complete(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1
            source = call1_chunks if call_count == 1 else call2_chunks
            for chunk in source:
                yield chunk

        tool = MagicMock()
        tool.name = "shell"
        tool.description = "Run commands"
        tool.execute = AsyncMock(return_value=ToolResult.ok("ok"))

        registry = MagicMock()
        registry.list_all.return_value = [tool]
        registry.get_entry.return_value = None
        registry.validated_execute = AsyncMock(return_value=ToolResult.ok("ok"))

        router = MagicMock()
        router.stream_complete = _stream_complete
        router.complete = AsyncMock()

        config = ToolLoopConfig(max_iterations=5, enable_double_confirmation=False)
        loop = ToolLoop(router=router, tool_registry=registry, config=config)

        events = []
        async for event in loop.run_stream(
            [ChatMessage(role="user", content="run ls")], model="m"
        ):
            events.append(event)

        event_types = [e.event_type for e in events]
        assert "tool_call_started" in event_types
        assert "tool_call_completed" in event_types
        assert events[-1].event_type == "completed"
        assert events[-1].data["termination_reason"] == "natural"
