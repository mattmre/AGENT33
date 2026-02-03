"""Tests for Activity Feed API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from agent33.db.models import ActivityLog, ActivityType, SourceType


class TestActivityFeedAPI:
    """Tests for the activity feed endpoints."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = AsyncMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=None)
        return session

    @pytest.fixture
    def sample_activities(self):
        """Create sample activity data."""
        return [
            ActivityLog(
                id="act_1",
                tenant_id="default",
                activity_type=ActivityType.INGESTED,
                title="Ingested 10 articles from Reuters",
                description="RSS feed update",
                metadata_={"items_count": 10},
                is_public=True,
                created_at=datetime.now(UTC),
            ),
            ActivityLog(
                id="act_2",
                tenant_id="default",
                activity_type=ActivityType.LEARNED,
                title="Learned: New AI regulation proposed",
                description="Extracted fact from news article",
                metadata_={"confidence": 0.95},
                is_public=True,
                created_at=datetime.now(UTC),
            ),
        ]

    def test_activity_item_model(self):
        """Test ActivityItem pydantic model."""
        from agent33.api.routes.activity import ActivityItem

        item = ActivityItem(
            id="test_id",
            activity_type="ingested",
            title="Test Activity",
            description="Test description",
            metadata={"key": "value"},
            source_name="Test Source",
            created_at=datetime.now(UTC),
        )
        assert item.id == "test_id"
        assert item.activity_type == "ingested"

    def test_stats_response_model(self):
        """Test StatsResponse pydantic model."""
        from agent33.api.routes.activity import StatsResponse

        stats = StatsResponse(
            facts_count=100,
            sources_count=5,
            activities_today=25,
            last_activity_at=datetime.now(UTC),
        )
        assert stats.facts_count == 100
        assert stats.sources_count == 5

    def test_ask_request_model(self):
        """Test AskRequest pydantic model."""
        from agent33.api.routes.activity import AskRequest

        request = AskRequest(question="What is the weather today?")
        assert request.question == "What is the weather today?"

    def test_ask_response_model(self):
        """Test AskResponse pydantic model."""
        from agent33.api.routes.activity import AskResponse

        response = AskResponse(
            answer="The weather is sunny.",
            sources=[{"text": "Weather report", "score": 0.95}],
            confidence=0.95,
        )
        assert response.answer == "The weather is sunny."
        assert len(response.sources) == 1


class TestObservatoryAPI:
    """Tests for Observatory frontend routes."""

    def test_activity_item_model(self):
        """Test ActivityItem in observatory routes."""
        from agent33.api.routes.observatory import ActivityItem

        item = ActivityItem(
            id="test_123",
            type="query",
            message="User asked a question",
            timestamp=datetime.now(UTC),
            agent="assistant",
            metadata={"extra": "data"},
        )
        assert item.id == "test_123"
        assert item.type == "query"

    def test_record_activity(self):
        """Test recording activity to in-memory store."""
        from agent33.api.routes.observatory import _activity_store, record_activity

        initial_count = len(_activity_store)

        activity = record_activity(
            activity_type="test",
            message="Test activity message",
            agent="test_agent",
            metadata={"test": True},
        )

        assert activity.type == "test"
        assert activity.message == "Test activity message"
        assert activity.agent == "test_agent"
        assert len(_activity_store) == initial_count + 1

    def test_activity_store_bounded(self):
        """Test that activity store doesn't grow unbounded."""
        from agent33.api.routes.observatory import _activity_store, record_activity

        # Record many activities
        for i in range(1100):
            record_activity(
                activity_type="bulk",
                message=f"Bulk activity {i}",
            )

        # Store should be bounded to 1000
        assert len(_activity_store) <= 1001  # Allow for concurrent test runs

    def test_stats_response_model(self):
        """Test StatsResponse model."""
        from agent33.api.routes.observatory import StatsResponse

        stats = StatsResponse(
            facts_count=50,
            sources_count=3,
            queries_today=10,
            uptime="2h 30m",
        )
        assert stats.uptime == "2h 30m"

    def test_ask_response_model(self):
        """Test AskResponse model."""
        from agent33.api.routes.observatory import AskResponse

        response = AskResponse(
            answer="Test answer",
            sources=[{"title": "Source 1", "url": "https://example.com"}],
        )
        assert response.answer == "Test answer"
        assert len(response.sources) == 1


class TestSourcesAPI:
    """Tests for Sources management API."""

    def test_source_create_model(self):
        """Test SourceCreate pydantic model."""
        from agent33.api.routes.sources import SourceCreate

        create = SourceCreate(
            name="Test RSS Feed",
            source_type=SourceType.RSS,
            url="https://example.com/feed.xml",
            config={"max_items": 50},
            is_active=True,
        )
        assert create.name == "Test RSS Feed"
        assert create.source_type == SourceType.RSS

    def test_source_update_model(self):
        """Test SourceUpdate pydantic model."""
        from agent33.api.routes.sources import SourceUpdate

        update = SourceUpdate(
            name="Updated Name",
            is_active=False,
        )
        assert update.name == "Updated Name"
        assert update.is_active is False
        assert update.url is None  # Not provided

    def test_source_response_model(self):
        """Test SourceResponse pydantic model."""
        from agent33.api.routes.sources import SourceResponse

        response = SourceResponse(
            id="source_123",
            name="Test Source",
            source_type="rss",
            url="https://example.com/feed.xml",
            config={},
            is_active=True,
            last_fetched_at=None,
            last_error=None,
            items_fetched=100,
            created_at="2024-01-01T00:00:00Z",
        )
        assert response.items_fetched == 100

    def test_ingest_response_model(self):
        """Test IngestResponse pydantic model."""
        from agent33.api.routes.sources import IngestResponse

        response = IngestResponse(
            status="success",
            items_fetched=50,
            new_facts=25,
        )
        assert response.status == "success"
        assert response.new_facts == 25

        error_response = IngestResponse(
            status="error",
            error="Connection failed",
        )
        assert error_response.error == "Connection failed"
