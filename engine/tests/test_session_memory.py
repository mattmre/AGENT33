"""Tests for session memory: observation, summarization, progressive recall."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from agent33.memory.observation import Observation, ObservationCapture


class TestObservation:
    """Test Observation dataclass."""

    def test_defaults(self) -> None:
        obs = Observation()
        assert obs.id
        assert obs.session_id == ""
        assert obs.event_type == ""
        assert obs.tags == []

    def test_with_fields(self) -> None:
        obs = Observation(
            session_id="s1",
            agent_name="coder",
            event_type="llm_response",
            content="hello",
            tags=["test"],
        )
        assert obs.session_id == "s1"
        assert obs.agent_name == "coder"
        assert "test" in obs.tags


class TestObservationCapture:
    """Test ObservationCapture recording and filtering."""

    @pytest.mark.asyncio
    async def test_record_and_flush(self) -> None:
        capture = ObservationCapture()
        obs = Observation(content="test content")
        obs_id = await capture.record(obs)
        assert obs_id == obs.id
        assert capture.buffer_size == 1

        flushed = await capture.flush()
        assert len(flushed) == 1
        assert capture.buffer_size == 0

    @pytest.mark.asyncio
    async def test_private_tags_not_stored(self) -> None:
        """Observations with private tags are buffered but not stored in LTM."""
        mock_memory = AsyncMock()
        mock_embed = AsyncMock()
        mock_embed.embed.return_value = [0.1] * 1536

        capture = ObservationCapture(
            long_term_memory=mock_memory,
            embedding_provider=mock_embed,
        )
        obs = Observation(content="secret data", tags=["sensitive"])
        await capture.record(obs)

        # Should be buffered
        assert capture.buffer_size == 1
        # Should NOT be stored in long-term memory
        mock_memory.store.assert_not_called()

    @pytest.mark.asyncio
    async def test_public_obs_stored_in_ltm(self) -> None:
        """Non-private observations are stored with embedding."""
        mock_memory = AsyncMock()
        mock_embed = AsyncMock()
        mock_embed.embed.return_value = [0.1] * 1536

        capture = ObservationCapture(
            long_term_memory=mock_memory,
            embedding_provider=mock_embed,
        )
        obs = Observation(content="public data", tags=["general"])
        await capture.record(obs)

        mock_embed.embed.assert_called_once_with("public data")
        mock_memory.store.assert_called_once()


class TestSessionSummarizer:
    """Test SessionSummarizer."""

    @pytest.mark.asyncio
    async def test_summarize(self) -> None:
        from agent33.llm.base import LLMResponse
        from agent33.memory.summarizer import SessionSummarizer

        mock_router = AsyncMock()
        mock_router.complete.return_value = LLMResponse(
            content='{"summary": "Agent did things", "key_facts": ["fact1"], "tags": ["coding"]}',
            model="test",
            prompt_tokens=10,
            completion_tokens=20,
        )

        summarizer = SessionSummarizer(router=mock_router)
        observations = [
            Observation(event_type="llm_response", agent_name="coder", content="wrote code"),
            Observation(event_type="tool_call", agent_name="coder", content="ran tests"),
        ]
        result = await summarizer.summarize(observations)

        assert result["summary"] == "Agent did things"
        assert "fact1" in result["key_facts"]
        assert "coding" in result["tags"]

    @pytest.mark.asyncio
    async def test_summarize_json_error_fallback(self) -> None:
        from agent33.llm.base import LLMResponse
        from agent33.memory.summarizer import SessionSummarizer

        mock_router = AsyncMock()
        mock_router.complete.return_value = LLMResponse(
            content="Not valid JSON at all",
            model="test",
            prompt_tokens=10,
            completion_tokens=20,
        )

        summarizer = SessionSummarizer(router=mock_router)
        result = await summarizer.summarize([Observation(content="test")])
        assert "summary" in result
        assert result["key_facts"] == []


class TestProgressiveRecall:
    """Test ProgressiveRecall at different detail levels."""

    @pytest.mark.asyncio
    async def test_index_level(self) -> None:
        from agent33.memory.long_term import SearchResult
        from agent33.memory.progressive_recall import ProgressiveRecall

        mock_memory = AsyncMock()
        mock_memory.search.return_value = [
            SearchResult(
                text="Some observation content here",
                score=0.9,
                metadata={
                    "observation_id": "obs1",
                    "agent_name": "coder",
                    "event_type": "llm_response",
                    "tags": ["coding"],
                },
            )
        ]
        mock_embed = AsyncMock()
        mock_embed.embed.return_value = [0.1] * 1536

        recall = ProgressiveRecall(mock_memory, mock_embed)
        results = await recall.search("code", level="index")

        assert len(results) == 1
        assert results[0].level == "index"
        assert "coder" in results[0].content
        assert results[0].token_estimate < 100

    @pytest.mark.asyncio
    async def test_full_level(self) -> None:
        from agent33.memory.long_term import SearchResult
        from agent33.memory.progressive_recall import ProgressiveRecall

        mock_memory = AsyncMock()
        mock_memory.search.return_value = [
            SearchResult(
                text="Full detailed content of the observation",
                score=0.8,
                metadata={"observation_id": "obs2"},
            )
        ]
        mock_embed = AsyncMock()
        mock_embed.embed.return_value = [0.1] * 1536

        recall = ProgressiveRecall(mock_memory, mock_embed)
        results = await recall.search("detail", level="full")

        assert len(results) == 1
        assert results[0].level == "full"
        assert "Full detailed content" in results[0].content
