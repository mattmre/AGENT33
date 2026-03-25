"""Tests for Phase 50: Context Compression Engine.

Validates the ContextCompressor class including:
- needs_compression threshold logic
- structured summary generation with all 5 required sections
- iterative update (second compression preserves existing summary)
- tool output pruning in the middle zone
- tail protection (recent messages preserved verbatim)
- head protection (first N message groups including tool-call pairs)
- short/empty conversations (no compression needed)
- tool loop integration (compression triggered in run() and run_stream())
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from agent33.agents.context_manager import estimate_message_tokens
from agent33.llm.base import ChatMessage, LLMResponse
from agent33.memory.context_compressor import (
    _CONTEXT_SUMMARY_PREFIX,
    _TOOL_OUTPUT_PLACEHOLDER,
    REQUIRED_SECTIONS,
    ContextCompressor,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_messages(count: int, content_size: int = 200) -> list[ChatMessage]:
    """Create a list of alternating user/assistant messages."""
    msgs: list[ChatMessage] = [
        ChatMessage(role="system", content="You are a helpful assistant."),
    ]
    for i in range(count):
        role = "user" if i % 2 == 0 else "assistant"
        msgs.append(ChatMessage(role=role, content=f"Message {i}: " + "x" * content_size))
    return msgs


def _make_tool_call_group() -> list[ChatMessage]:
    """Create an assistant+tool message pair (one logical group)."""
    from agent33.llm.base import ToolCall, ToolCallFunction

    tc = ToolCall(id="tc-1", function=ToolCallFunction(name="shell", arguments='{"cmd":"ls"}'))
    return [
        ChatMessage(role="assistant", content="Let me check.", tool_calls=[tc]),
        ChatMessage(role="tool", content="file1.py\nfile2.py", tool_call_id="tc-1", name="shell"),
    ]


def _structured_summary_text() -> str:
    """Return a well-formed structured summary with all 5 sections."""
    return (
        "## Goal\nBuild a new feature.\n\n"
        "## Progress\n- Completed step 1\n- Completed step 2\n\n"
        "## Key Decisions\n- Chose approach A over B\n\n"
        "## Files Modified\n- src/main.py\n- tests/test_main.py\n\n"
        "## Next Steps\n- Implement step 3\n- Write tests"
    )


def _make_mock_router(summary_text: str | None = None) -> AsyncMock:
    """Create a mock ModelRouter that returns a structured summary."""
    router = AsyncMock()
    text = summary_text or _structured_summary_text()
    router.complete = AsyncMock(
        return_value=LLMResponse(
            content=text,
            model="test-model",
            prompt_tokens=100,
            completion_tokens=50,
        )
    )
    return router


# ---------------------------------------------------------------------------
# needs_compression
# ---------------------------------------------------------------------------


class TestNeedsCompression:
    def test_below_threshold_returns_false(self) -> None:
        compressor = ContextCompressor(threshold_percent=0.50)
        # Small conversation, large context window
        msgs = _make_messages(3, content_size=50)
        assert compressor.needs_compression(msgs, model_context_window=128_000) is False

    def test_above_threshold_returns_true(self) -> None:
        compressor = ContextCompressor(threshold_percent=0.50)
        # Large conversation with a small context window so tokens exceed 50%
        msgs = _make_messages(50, content_size=500)
        tokens = estimate_message_tokens(msgs)
        # Set window so that tokens > 50% of window (tokens / 0.50 = window at boundary)
        # Use a smaller window so tokens clearly exceed threshold
        window = int(tokens * 1.5)  # tokens = 66% of window, threshold is 50%
        assert compressor.needs_compression(msgs, model_context_window=window) is True

    def test_exactly_at_threshold_returns_false(self) -> None:
        """At exactly the threshold, compression is not needed (needs > not >=)."""
        compressor = ContextCompressor(threshold_percent=0.50)
        msgs = _make_messages(5, content_size=100)
        tokens = estimate_message_tokens(msgs)
        # Set window so threshold = tokens exactly
        window = tokens * 2  # 50% of window = tokens
        assert compressor.needs_compression(msgs, model_context_window=window) is False

    def test_zero_context_window_returns_false(self) -> None:
        compressor = ContextCompressor(threshold_percent=0.50)
        msgs = _make_messages(10)
        assert compressor.needs_compression(msgs, model_context_window=0) is False

    def test_empty_messages_returns_false(self) -> None:
        compressor = ContextCompressor(threshold_percent=0.50)
        assert compressor.needs_compression([], model_context_window=128_000) is False


# ---------------------------------------------------------------------------
# Head protection
# ---------------------------------------------------------------------------


class TestHeadProtection:
    def test_system_prompt_preserved(self) -> None:
        compressor = ContextCompressor(protect_first_n=1)
        msgs = _make_messages(20, content_size=200)
        head, middle, tail = compressor._split_zones(msgs)
        # First message is system, protect_first_n=1 means 1 logical group
        # System message is the first, then first user message is group 1
        assert head[0].role == "system"

    def test_protect_first_n_counts_groups(self) -> None:
        compressor = ContextCompressor(protect_first_n=3, tail_token_budget=0)
        msgs = _make_messages(10, content_size=50)
        head, middle, tail = compressor._split_zones(msgs)
        # protect_first_n=3 means 3 logical groups: system, user msg, assistant msg
        assert len(head) == 3

    def test_tool_call_pair_counts_as_one_group(self) -> None:
        """An assistant+tool message pair is counted as a single group."""
        compressor = ContextCompressor(protect_first_n=2, tail_token_budget=0)
        # Build: system, user, assistant+tool_call, tool_result, user, assistant
        msgs = [
            ChatMessage(role="system", content="System prompt."),
            ChatMessage(role="user", content="Hello"),
        ]
        msgs.extend(_make_tool_call_group())
        msgs.append(ChatMessage(role="user", content="Thanks"))
        msgs.append(ChatMessage(role="assistant", content="You're welcome"))

        head, middle, _tail = compressor._split_zones(msgs)
        # Group 1: system prompt
        # Group 2: user message "Hello"
        # So head should be [system, user("Hello")]
        assert len(head) == 2
        assert head[0].role == "system"
        assert head[1].content == "Hello"

    def test_protect_first_n_with_tool_pairs_in_head(self) -> None:
        """When tool-call pairs are inside the head zone, they are fully included."""
        compressor = ContextCompressor(protect_first_n=3, tail_token_budget=0)
        msgs = [
            ChatMessage(role="system", content="System prompt."),
            ChatMessage(role="user", content="Do something"),
        ]
        msgs.extend(_make_tool_call_group())  # assistant+tool = 1 group
        msgs.append(ChatMessage(role="user", content="Another message"))
        msgs.append(ChatMessage(role="assistant", content="Done"))

        head, middle, _tail = compressor._split_zones(msgs)
        # Group 1: system
        # Group 2: user "Do something"
        # Group 3: assistant+tool pair (counts as one group)
        assert len(head) == 4  # system + user + assistant + tool
        assert head[0].role == "system"
        assert head[1].content == "Do something"
        assert head[2].role == "assistant"
        assert head[3].role == "tool"

    def test_protect_zero_gives_empty_head(self) -> None:
        compressor = ContextCompressor(protect_first_n=0, tail_token_budget=0)
        msgs = _make_messages(5, content_size=50)
        head, middle, _tail = compressor._split_zones(msgs)
        assert len(head) == 0


# ---------------------------------------------------------------------------
# Tail protection
# ---------------------------------------------------------------------------


class TestTailProtection:
    def test_recent_messages_preserved(self) -> None:
        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=50_000,
        )
        msgs = _make_messages(20, content_size=200)
        _head, _middle, tail = compressor._split_zones(msgs)
        # Tail should contain the most recent messages
        assert len(tail) > 0
        assert tail[-1].content == msgs[-1].content

    def test_tail_does_not_overlap_head(self) -> None:
        """Even with a huge tail budget, tail cannot overlap with head."""
        compressor = ContextCompressor(
            protect_first_n=3,
            tail_token_budget=1_000_000,  # More than total tokens
        )
        msgs = _make_messages(5, content_size=50)
        head, middle, tail = compressor._split_zones(msgs)
        # All messages after head go to tail, middle is empty
        assert len(middle) == 0
        assert len(head) + len(tail) == len(msgs)

    def test_zero_tail_budget(self) -> None:
        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=0,
        )
        msgs = _make_messages(10, content_size=200)
        _head, _middle, tail = compressor._split_zones(msgs)
        assert len(tail) == 0


# ---------------------------------------------------------------------------
# Tool output pruning
# ---------------------------------------------------------------------------


class TestToolOutputPruning:
    def test_tool_messages_replaced_with_placeholder(self) -> None:
        msgs = [
            ChatMessage(role="user", content="Run a command"),
            ChatMessage(
                role="tool",
                content="Long tool output with lots of data...",
                tool_call_id="tc-1",
                name="shell",
            ),
            ChatMessage(role="assistant", content="The command output shows..."),
        ]
        pruned = ContextCompressor._prune_tool_outputs(msgs)

        assert len(pruned) == 3
        assert pruned[0].content == "Run a command"
        assert pruned[1].content == _TOOL_OUTPUT_PLACEHOLDER
        assert pruned[1].tool_call_id == "tc-1"
        assert pruned[1].name == "shell"
        assert pruned[2].content == "The command output shows..."

    def test_non_tool_messages_unchanged(self) -> None:
        msgs = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there"),
        ]
        pruned = ContextCompressor._prune_tool_outputs(msgs)
        assert pruned[0].content == "Hello"
        assert pruned[1].content == "Hi there"


# ---------------------------------------------------------------------------
# Structured summary generation
# ---------------------------------------------------------------------------


class TestStructuredSummary:
    @pytest.mark.asyncio
    async def test_summary_contains_all_five_sections(self) -> None:
        """The generated summary must contain all 5 required sections."""
        summary_text = _structured_summary_text()
        router = _make_mock_router(summary_text)
        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=500,
            threshold_percent=0.01,
        )

        msgs = _make_messages(30, content_size=300)
        compressed, stats = await compressor.compress(msgs, "test-model", router)

        # Find the summary message
        summary_msgs = [
            m for m in compressed if m.text_content.startswith(_CONTEXT_SUMMARY_PREFIX)
        ]
        assert len(summary_msgs) == 1

        summary_content = summary_msgs[0].text_content
        for section in REQUIRED_SECTIONS:
            assert f"## {section}" in summary_content, (
                f"Missing required section '## {section}' in summary"
            )

    @pytest.mark.asyncio
    async def test_summary_message_has_user_role(self) -> None:
        """Summary message should use 'user' role for unwinding eligibility."""
        router = _make_mock_router()
        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=500,
            threshold_percent=0.01,
        )

        msgs = _make_messages(30, content_size=300)
        compressed, _stats = await compressor.compress(msgs, "test-model", router)

        summary_msgs = [
            m for m in compressed if m.text_content.startswith(_CONTEXT_SUMMARY_PREFIX)
        ]
        assert summary_msgs[0].role == "user"

    @pytest.mark.asyncio
    async def test_llm_called_without_tools(self) -> None:
        """Summary LLM call must use tools=None to prevent recursion."""
        router = _make_mock_router()
        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=500,
            threshold_percent=0.01,
        )

        msgs = _make_messages(30, content_size=300)
        await compressor.compress(msgs, "test-model", router)

        # Verify the router was called with tools=None
        call_kwargs = router.complete.call_args
        assert call_kwargs.kwargs.get("tools") is None

    @pytest.mark.asyncio
    async def test_fallback_summary_on_llm_failure(self) -> None:
        """When LLM fails, fallback summary still has required sections."""
        router = AsyncMock()
        router.complete = AsyncMock(side_effect=RuntimeError("LLM unavailable"))

        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=500,
            threshold_percent=0.01,
        )

        msgs = _make_messages(30, content_size=300)
        compressed, _stats = await compressor.compress(msgs, "test-model", router)

        summary_msgs = [
            m for m in compressed if m.text_content.startswith(_CONTEXT_SUMMARY_PREFIX)
        ]
        assert len(summary_msgs) == 1
        summary_content = summary_msgs[0].text_content
        # Fallback should still have the section headers
        for section in REQUIRED_SECTIONS:
            assert f"## {section}" in summary_content


# ---------------------------------------------------------------------------
# Iterative update
# ---------------------------------------------------------------------------


class TestIterativeUpdate:
    @pytest.mark.asyncio
    async def test_second_compression_detects_existing_summary(self) -> None:
        """When a prior summary exists, the compressor uses iterative update."""
        router = _make_mock_router()
        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=500,
            threshold_percent=0.01,
        )

        msgs = _make_messages(30, content_size=300)

        # First compression
        compressed_1, stats_1 = await compressor.compress(msgs, "test-model", router)
        assert not stats_1.used_iterative_update

        # Add more messages to the compressed conversation
        for i in range(10):
            compressed_1.append(
                ChatMessage(role="user" if i % 2 == 0 else "assistant", content="x" * 300)
            )

        # Second compression should detect existing summary
        compressed_2, stats_2 = await compressor.compress(compressed_1, "test-model", router)
        assert stats_2.used_iterative_update

    @pytest.mark.asyncio
    async def test_iterative_update_removes_old_summary(self) -> None:
        """Iterative update replaces the old summary, not duplicates it."""
        router = _make_mock_router()
        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=500,
            threshold_percent=0.01,
        )

        msgs = _make_messages(30, content_size=300)
        compressed_1, _ = await compressor.compress(msgs, "test-model", router)

        # Add more messages
        for i in range(10):
            compressed_1.append(
                ChatMessage(role="user" if i % 2 == 0 else "assistant", content="x" * 300)
            )

        compressed_2, _ = await compressor.compress(compressed_1, "test-model", router)

        # Count summary messages -- should be exactly 1
        summary_count = sum(
            1 for m in compressed_2 if m.text_content.startswith(_CONTEXT_SUMMARY_PREFIX)
        )
        assert summary_count == 1


# ---------------------------------------------------------------------------
# Compression stats
# ---------------------------------------------------------------------------


class TestCompressionStats:
    @pytest.mark.asyncio
    async def test_stats_reflect_actual_compression(self) -> None:
        router = _make_mock_router()
        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=500,
            threshold_percent=0.01,
        )

        msgs = _make_messages(30, content_size=300)
        original_tokens = estimate_message_tokens(msgs)

        _compressed, stats = await compressor.compress(msgs, "test-model", router)

        assert stats.original_tokens == original_tokens
        assert stats.compressed_tokens < stats.original_tokens
        assert stats.messages_removed > 0
        assert stats.messages_kept > 0
        assert 0.0 < stats.compression_ratio < 1.0

    @pytest.mark.asyncio
    async def test_no_compression_when_nothing_in_middle(self) -> None:
        """Short conversation: head+tail cover everything, middle is empty."""
        router = _make_mock_router()
        compressor = ContextCompressor(
            protect_first_n=3,
            tail_token_budget=100_000,
        )

        msgs = _make_messages(3, content_size=50)

        compressed, stats = await compressor.compress(msgs, "test-model", router)

        assert stats.messages_removed == 0
        assert stats.compression_ratio == 1.0
        assert len(compressed) == len(msgs)


# ---------------------------------------------------------------------------
# Original messages are not mutated
# ---------------------------------------------------------------------------


class TestImmutability:
    @pytest.mark.asyncio
    async def test_original_messages_unchanged(self) -> None:
        """compress() must not mutate the input message list."""
        router = _make_mock_router()
        compressor = ContextCompressor(
            protect_first_n=1,
            tail_token_budget=500,
            threshold_percent=0.01,
        )

        msgs = _make_messages(30, content_size=300)
        original_len = len(msgs)
        original_contents = [m.text_content for m in msgs]

        _compressed, _stats = await compressor.compress(msgs, "test-model", router)

        assert len(msgs) == original_len
        assert [m.text_content for m in msgs] == original_contents


# ---------------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------------


class TestConfigValidation:
    def test_threshold_must_be_between_0_and_1(self) -> None:
        with pytest.raises(ValueError, match="threshold_percent"):
            ContextCompressor(threshold_percent=0.0)
        with pytest.raises(ValueError, match="threshold_percent"):
            ContextCompressor(threshold_percent=1.0)
        with pytest.raises(ValueError, match="threshold_percent"):
            ContextCompressor(threshold_percent=1.5)

    def test_protect_first_n_must_be_non_negative(self) -> None:
        with pytest.raises(ValueError, match="protect_first_n"):
            ContextCompressor(protect_first_n=-1)

    def test_tail_token_budget_must_be_non_negative(self) -> None:
        with pytest.raises(ValueError, match="tail_token_budget"):
            ContextCompressor(tail_token_budget=-1)


# ---------------------------------------------------------------------------
# ShortTermMemory integration
# ---------------------------------------------------------------------------


class TestShortTermMemoryIntegration:
    def test_compressor_field_exists(self) -> None:
        from agent33.memory.short_term import ShortTermMemory

        mem = ShortTermMemory()
        assert mem.compressor is None
        assert mem.compression_count == 0

    def test_compressor_field_accepts_instance(self) -> None:
        from agent33.memory.short_term import ShortTermMemory

        compressor = ContextCompressor()
        mem = ShortTermMemory(compressor=compressor)
        assert mem.compressor is compressor
        assert mem.compression_count == 0


# ---------------------------------------------------------------------------
# Config integration
# ---------------------------------------------------------------------------


class TestConfigIntegration:
    def test_compression_config_defaults(self) -> None:
        from agent33.config import Settings

        s = Settings(
            jwt_secret="test-secret",
            api_secret_key="test-key",
        )
        assert s.context_compression_enabled is False
        assert s.context_compression_threshold_percent == 0.50

    def test_compression_config_override(self) -> None:
        from agent33.config import Settings

        s = Settings(
            jwt_secret="test-secret",
            api_secret_key="test-key",
            context_compression_enabled=True,
            context_compression_threshold_percent=0.75,
        )
        assert s.context_compression_enabled is True
        assert s.context_compression_threshold_percent == 0.75


# ---------------------------------------------------------------------------
# Tool loop integration
# ---------------------------------------------------------------------------


class TestToolLoopIntegration:
    def test_tool_loop_accepts_compressor_parameter(self) -> None:
        """ToolLoop.__init__ should accept context_compressor kwarg."""
        from agent33.agents.tool_loop import ToolLoop

        router = AsyncMock()
        registry = AsyncMock()
        compressor = ContextCompressor()

        loop = ToolLoop(
            router=router,
            tool_registry=registry,
            context_compressor=compressor,
            model_context_window=64_000,
        )
        assert loop._context_compressor is compressor
        assert loop._model_context_window == 64_000

    def test_tool_loop_defaults_no_compressor(self) -> None:
        """ToolLoop should work without a compressor (backward compatible)."""
        from agent33.agents.tool_loop import ToolLoop

        router = AsyncMock()
        registry = AsyncMock()

        loop = ToolLoop(router=router, tool_registry=registry)
        assert loop._context_compressor is None
        assert loop._model_context_window == 128_000
