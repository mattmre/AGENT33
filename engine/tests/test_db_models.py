"""Tests for database models."""

from __future__ import annotations

from datetime import UTC

from agent33.db.models import (
    ActivityLog,
    ActivityType,
    AgentDefinitionRecord,
    ApiKey,
    Fact,
    MemoryRecord,
    Source,
    SourceType,
    Tenant,
    UsageMetric,
    WorkflowCheckpoint,
    WorkflowDefinitionRecord,
    new_uuid,
    utc_now,
)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_utc_now_returns_utc(self):
        """Test that utc_now returns UTC datetime."""
        now = utc_now()
        assert now.tzinfo == UTC

    def test_new_uuid_format(self):
        """Test that new_uuid returns valid UUID string."""
        uuid = new_uuid()
        assert isinstance(uuid, str)
        assert len(uuid) == 36  # Standard UUID format
        assert uuid.count("-") == 4


class TestActivityType:
    """Tests for ActivityType enum."""

    def test_all_activity_types_exist(self):
        """Test that all expected activity types are defined."""
        expected = ["ingested", "learned", "corrected", "connected", "queried", "responded", "error"]
        for activity in expected:
            assert hasattr(ActivityType, activity.upper())

    def test_activity_type_values(self):
        """Test that activity type values are lowercase strings."""
        assert ActivityType.INGESTED.value == "ingested"
        assert ActivityType.LEARNED.value == "learned"
        assert ActivityType.ERROR.value == "error"


class TestSourceType:
    """Tests for SourceType enum."""

    def test_all_source_types_exist(self):
        """Test that all expected source types are defined."""
        expected = ["gdelt", "rss", "youtube", "twitter", "manual", "webhook"]
        for source in expected:
            assert hasattr(SourceType, source.upper())


class TestTenantModel:
    """Tests for Tenant model."""

    def test_tenant_has_required_fields(self):
        """Test that Tenant model has all required columns."""
        columns = [c.name for c in Tenant.__table__.columns]
        assert "id" in columns
        assert "name" in columns
        assert "slug" in columns
        assert "is_active" in columns
        assert "settings" in columns
        assert "created_at" in columns

    def test_tenant_slug_is_unique(self):
        """Test that slug has unique constraint."""
        slug_column = Tenant.__table__.columns["slug"]
        assert slug_column.unique is True


class TestApiKeyModel:
    """Tests for ApiKey model."""

    def test_apikey_has_required_fields(self):
        """Test that ApiKey model has all required columns."""
        columns = [c.name for c in ApiKey.__table__.columns]
        required = ["id", "tenant_id", "key_id", "key_hash", "name", "scopes", "is_active"]
        for col in required:
            assert col in columns

    def test_apikey_foreign_key(self):
        """Test that tenant_id has foreign key constraint."""
        tenant_id_col = ApiKey.__table__.columns["tenant_id"]
        assert len(tenant_id_col.foreign_keys) == 1


class TestActivityLogModel:
    """Tests for ActivityLog model."""

    def test_activity_log_has_required_fields(self):
        """Test that ActivityLog model has all required columns."""
        columns = [c.name for c in ActivityLog.__table__.columns]
        required = ["id", "tenant_id", "activity_type", "title", "is_public", "created_at"]
        for col in required:
            assert col in columns

    def test_activity_log_indexes(self):
        """Test that appropriate indexes exist."""
        indexes = [idx.name for idx in ActivityLog.__table__.indexes]
        assert "ix_activity_log_tenant_created" in indexes
        assert "ix_activity_log_public_created" in indexes


class TestSourceModel:
    """Tests for Source model."""

    def test_source_has_required_fields(self):
        """Test that Source model has all required columns."""
        columns = [c.name for c in Source.__table__.columns]
        required = ["id", "tenant_id", "source_type", "name", "url", "config", "is_active"]
        for col in required:
            assert col in columns

    def test_source_unique_constraint(self):
        """Test that source has unique constraint on tenant+type+url."""
        constraints = [c.name for c in Source.__table__.constraints if hasattr(c, "name") and c.name]
        assert "uq_source_tenant_type_url" in constraints


class TestFactModel:
    """Tests for Fact model."""

    def test_fact_has_required_fields(self):
        """Test that Fact model has all required columns."""
        columns = [c.name for c in Fact.__table__.columns]
        required = ["id", "tenant_id", "content", "content_hash", "confidence"]
        for col in required:
            assert col in columns

    def test_fact_unique_constraint(self):
        """Test that fact has unique constraint on tenant+hash."""
        constraints = [c.name for c in Fact.__table__.constraints if hasattr(c, "name") and c.name]
        assert "uq_fact_tenant_hash" in constraints

    def test_fact_default_confidence(self):
        """Test that confidence defaults to 1.0."""
        confidence_col = Fact.__table__.columns["confidence"]
        assert confidence_col.default.arg == 1.0


class TestUsageMetricModel:
    """Tests for UsageMetric model."""

    def test_usage_metric_has_required_fields(self):
        """Test that UsageMetric model has all required columns."""
        columns = [c.name for c in UsageMetric.__table__.columns]
        required = ["id", "tenant_id", "metric_type", "value", "period_start", "period_end"]
        for col in required:
            assert col in columns


class TestMemoryRecordModel:
    """Tests for MemoryRecord model."""

    def test_memory_record_has_tenant_id(self):
        """Test that MemoryRecord has tenant_id for multi-tenancy."""
        columns = [c.name for c in MemoryRecord.__table__.columns]
        assert "tenant_id" in columns

    def test_memory_record_has_embedding(self):
        """Test that MemoryRecord has embedding column."""
        columns = [c.name for c in MemoryRecord.__table__.columns]
        assert "embedding" in columns


class TestWorkflowCheckpointModel:
    """Tests for WorkflowCheckpoint model."""

    def test_checkpoint_has_tenant_id(self):
        """Test that WorkflowCheckpoint has tenant_id for multi-tenancy."""
        columns = [c.name for c in WorkflowCheckpoint.__table__.columns]
        assert "tenant_id" in columns

    def test_checkpoint_indexes(self):
        """Test that checkpoint has appropriate indexes."""
        indexes = [idx.name for idx in WorkflowCheckpoint.__table__.indexes]
        assert "ix_checkpoint_tenant_workflow" in indexes


class TestAgentDefinitionRecordModel:
    """Tests for AgentDefinitionRecord model."""

    def test_agent_def_has_required_fields(self):
        """Test that AgentDefinitionRecord has all required columns."""
        columns = [c.name for c in AgentDefinitionRecord.__table__.columns]
        required = ["id", "tenant_id", "name", "version", "definition_json", "is_active"]
        for col in required:
            assert col in columns


class TestWorkflowDefinitionRecordModel:
    """Tests for WorkflowDefinitionRecord model."""

    def test_workflow_def_has_required_fields(self):
        """Test that WorkflowDefinitionRecord has all required columns."""
        columns = [c.name for c in WorkflowDefinitionRecord.__table__.columns]
        required = ["id", "tenant_id", "name", "version", "definition_json", "is_active"]
        for col in required:
            assert col in columns
