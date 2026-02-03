"""Tests for ingestion workers (GDELT, RSS, YouTube)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent33.ingestion.base import BaseWorker, IngestResult
from agent33.ingestion.gdelt import GDELTWorker
from agent33.ingestion.rss import RSSWorker
from agent33.ingestion.youtube import YouTubeWorker


class TestIngestResult:
    """Tests for IngestResult dataclass."""

    def test_content_hash_auto_generated(self):
        """Test that content_hash is automatically generated if not provided."""
        result = IngestResult(
            source_url="https://example.com/article",
            title="Test Article",
            content="This is the article content.",
        )
        assert result.content_hash
        assert len(result.content_hash) == 64  # SHA-256 hex digest

    def test_content_hash_deterministic(self):
        """Test that same content produces same hash."""
        content = "Same content twice"
        result1 = IngestResult(source_url="url1", title="Title", content=content)
        result2 = IngestResult(source_url="url2", title="Title", content=content)
        assert result1.content_hash == result2.content_hash

    def test_metadata_defaults_to_empty(self):
        """Test that metadata defaults to empty dict."""
        result = IngestResult(source_url="url", title="Title", content="Content")
        assert result.metadata == {}


class TestGDELTWorker:
    """Tests for GDELT ingestion worker."""

    @pytest.fixture
    def worker(self):
        """Create a GDELT worker for testing."""
        return GDELTWorker(
            tenant_id="test_tenant",
            source_id="test_source",
            config={"max_records": 10},
        )

    def test_source_type(self, worker):
        """Test that source type is correct."""
        assert worker.source_type == "gdelt"

    def test_build_query_defaults(self, worker):
        """Test default query building."""
        params = worker._build_query()
        assert "sourcelang:eng" in params["query"]
        assert params["mode"] == "artlist"
        assert params["format"] == "json"

    def test_build_query_with_domain(self):
        """Test query building with domain filter."""
        worker = GDELTWorker(
            tenant_id="test",
            source_id="test",
            config={"domain": "reuters.com"},
        )
        params = worker._build_query()
        assert "domain:reuters.com" in params["query"]

    @pytest.mark.asyncio
    async def test_fetch_parses_articles(self, worker):
        """Test that fetch correctly parses GDELT response."""
        mock_response = {
            "articles": [
                {
                    "url": "https://example.com/article1",
                    "title": "Test Article 1",
                    "seendate": "20240101120000",
                    "domain": "example.com",
                    "language": "English",
                    "tone": 2.5,
                },
                {
                    "url": "https://example.com/article2",
                    "title": "Test Article 2",
                    "seendate": "20240101130000",
                    "domain": "example.com",
                    "language": "English",
                    "tone": -1.0,
                },
            ]
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.get.return_value = AsyncMock(
                status_code=200,
                raise_for_status=MagicMock(),
                json=MagicMock(return_value=mock_response),
            )
            mock_client.return_value = mock_instance

            results = []
            async for result in worker.fetch():
                results.append(result)

            assert len(results) == 2
            assert results[0].source_url == "https://example.com/article1"
            assert results[0].title == "Test Article 1"
            assert "domain" in results[0].metadata


class TestRSSWorker:
    """Tests for RSS ingestion worker."""

    @pytest.fixture
    def worker(self):
        """Create an RSS worker for testing."""
        return RSSWorker(
            tenant_id="test_tenant",
            source_id="test_source",
            config={"url": "https://example.com/feed.xml", "max_items": 5},
        )

    def test_source_type(self, worker):
        """Test that source type is correct."""
        assert worker.source_type == "rss"

    def test_strip_html(self, worker):
        """Test HTML stripping."""
        html = "<p>Hello <strong>world</strong></p>"
        stripped = worker._strip_html(html)
        assert stripped == "Hello world"

    def test_strip_html_cdata(self, worker):
        """Test CDATA stripping."""
        html = "<![CDATA[Hello world]]>"
        stripped = worker._strip_html(html)
        assert stripped == "Hello world"

    @pytest.mark.asyncio
    async def test_fetch_requires_url(self):
        """Test that fetch raises error without URL."""
        worker = RSSWorker(
            tenant_id="test",
            source_id="test",
            config={},  # No URL
        )

        with pytest.raises(ValueError, match="requires 'url'"):
            async for _ in worker.fetch():
                pass

    @pytest.mark.asyncio
    async def test_simple_rss_parsing(self, worker):
        """Test simple RSS XML parsing (without feedparser)."""
        rss_content = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Article One</title>
                    <link>https://example.com/1</link>
                    <description>First article content</description>
                </item>
                <item>
                    <title>Article Two</title>
                    <link>https://example.com/2</link>
                    <description>Second article content</description>
                </item>
            </channel>
        </rss>
        """

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.__aenter__.return_value = mock_instance
            mock_instance.__aexit__.return_value = None
            mock_instance.get.return_value = AsyncMock(
                status_code=200,
                raise_for_status=MagicMock(),
                text=rss_content,
            )
            mock_client.return_value = mock_instance

            # Force simple parsing by patching HAS_FEEDPARSER
            with patch.object(RSSWorker, "_parse_with_feedparser", side_effect=ImportError):
                results = []
                async for result in worker.fetch():
                    results.append(result)

            assert len(results) == 2
            assert results[0].title == "Article One"
            assert results[0].source_url == "https://example.com/1"


class TestYouTubeWorker:
    """Tests for YouTube transcript ingestion worker."""

    @pytest.fixture
    def worker(self):
        """Create a YouTube worker for testing."""
        return YouTubeWorker(
            tenant_id="test_tenant",
            source_id="test_source",
            config={"video_ids": ["dQw4w9WgXcQ"]},
        )

    def test_source_type(self, worker):
        """Test that source type is correct."""
        assert worker.source_type == "youtube"

    def test_extract_video_id_watch_url(self, worker):
        """Test extracting video ID from watch URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = worker._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_short_url(self, worker):
        """Test extracting video ID from short URL."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = worker._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_extract_video_id_embed_url(self, worker):
        """Test extracting video ID from embed URL."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = worker._extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"

    def test_combine_transcript(self, worker):
        """Test combining transcript segments."""
        transcript_data = [
            {"start": 0, "text": "Hello", "duration": 1},
            {"start": 1, "text": "world", "duration": 1},
            {"start": 35, "text": "New paragraph", "duration": 1},
        ]
        combined = worker._combine_transcript(transcript_data)
        assert "Hello world" in combined
        assert "New paragraph" in combined
        # Should have paragraph break after 30 seconds
        assert "\n\n" in combined

    def test_estimate_duration(self, worker):
        """Test duration estimation from transcript."""
        transcript_data = [
            {"start": 0, "duration": 5},
            {"start": 5, "duration": 10},
            {"start": 100, "duration": 5},
        ]
        duration = worker._estimate_duration(transcript_data)
        assert duration == 105  # 100 + 5

    @pytest.mark.asyncio
    async def test_fetch_no_videos_configured(self):
        """Test that fetch handles empty video list gracefully."""
        worker = YouTubeWorker(
            tenant_id="test",
            source_id="test",
            config={},  # No videos
        )

        results = []
        async for result in worker.fetch():
            results.append(result)

        assert len(results) == 0


class TestBaseWorker:
    """Tests for base worker functionality."""

    def test_abstract_methods(self):
        """Test that BaseWorker cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseWorker(tenant_id="test", source_id="test")

    @pytest.mark.asyncio
    async def test_run_collects_results(self):
        """Test that run() collects all fetch() results."""

        class TestWorker(BaseWorker):
            @property
            def source_type(self) -> str:
                return "test"

            async def fetch(self):
                yield IngestResult(source_url="url1", title="Title 1", content="Content 1")
                yield IngestResult(source_url="url2", title="Title 2", content="Content 2")

        worker = TestWorker(tenant_id="test", source_id="test")
        results = await worker.run()

        assert len(results) == 2
        assert results[0].source_url == "url1"
        assert results[1].source_url == "url2"
