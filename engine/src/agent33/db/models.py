"""Central database models for AGENT-33.

This module defines all SQLAlchemy models for persistent storage including:
- Multi-tenant support via tenant_id columns
- Activity logging for the Observatory
- Facts and sources for knowledge tracking
- API keys (persistent, replacing in-memory storage)
- Usage metrics for billing/quotas
"""

from __future__ import annotations

import enum
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None  # type: ignore[assignment,misc]


def utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)


def new_uuid() -> str:
    """Generate a new UUID string."""
    return str(uuid4())


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ActivityType(str, enum.Enum):
    """Types of activity events for the Observatory feed."""
    INGESTED = "ingested"      # New content was ingested
    LEARNED = "learned"        # New fact was extracted/learned
    CORRECTED = "corrected"    # Existing knowledge was corrected
    CONNECTED = "connected"    # Connection made between facts
    QUERIED = "queried"        # User asked a question
    RESPONDED = "responded"    # Agent responded to query
    ERROR = "error"            # An error occurred


class SourceType(str, enum.Enum):
    """Types of content sources."""
    GDELT = "gdelt"
    RSS = "rss"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    MANUAL = "manual"
    WEBHOOK = "webhook"


# ---------------------------------------------------------------------------
# Tenant
# ---------------------------------------------------------------------------


class Tenant(Base):
    """A tenant (organization/user) in the multi-tenant system."""

    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=new_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(63), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    settings = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    api_keys = relationship("ApiKey", back_populates="tenant", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="tenant", cascade="all, delete-orphan")
    facts = relationship("Fact", back_populates="tenant", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="tenant", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# API Keys (persistent, replacing in-memory storage)
# ---------------------------------------------------------------------------


class ApiKey(Base):
    """Persistent API key storage."""

    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=new_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    key_id = Column(String(16), nullable=False, unique=True, index=True)  # Public identifier
    key_hash = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hash
    name = Column(String(255), nullable=False)  # Human-readable name
    scopes = Column(JSONB, nullable=False, default=list)
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    tenant = relationship("Tenant", back_populates="api_keys")


# ---------------------------------------------------------------------------
# Activity Log (for Observatory feed)
# ---------------------------------------------------------------------------


class ActivityLog(Base):
    """Activity events for the public Observatory feed."""

    __tablename__ = "activity_log"

    id = Column(String(36), primary_key=True, default=new_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type = Column(Enum(ActivityType), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)  # Show in public feed?
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="activities")
    source = relationship("Source")

    __table_args__ = (
        Index("ix_activity_log_tenant_created", "tenant_id", "created_at"),
        Index("ix_activity_log_public_created", "is_public", "created_at"),
    )


# ---------------------------------------------------------------------------
# Sources (ingestion sources)
# ---------------------------------------------------------------------------


class Source(Base):
    """A content source (RSS feed, YouTube channel, etc.)."""

    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=new_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(Enum(SourceType), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    url = Column(Text, nullable=True)  # Feed URL, channel URL, etc.
    config = Column(JSONB, nullable=False, default=dict)  # Source-specific config
    is_active = Column(Boolean, default=True, nullable=False)
    last_fetched_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    items_fetched = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    tenant = relationship("Tenant", back_populates="sources")
    facts = relationship("Fact", back_populates="source")

    __table_args__ = (
        UniqueConstraint("tenant_id", "source_type", "url", name="uq_source_tenant_type_url"),
    )


# ---------------------------------------------------------------------------
# Facts (extracted knowledge)
# ---------------------------------------------------------------------------


class Fact(Base):
    """An extracted fact/piece of knowledge."""

    __tablename__ = "facts"

    id = Column(String(36), primary_key=True, default=new_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="SET NULL"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, index=True)  # For deduplication
    embedding = Column(Vector(1536) if Vector is not None else Text, nullable=True)
    confidence = Column(Float, default=1.0, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    source_url = Column(Text, nullable=True)  # Original URL where fact was found
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    # Relationships
    tenant = relationship("Tenant", back_populates="facts")
    source = relationship("Source", back_populates="facts")

    __table_args__ = (
        UniqueConstraint("tenant_id", "content_hash", name="uq_fact_tenant_hash"),
        Index("ix_facts_tenant_created", "tenant_id", "created_at"),
    )


# ---------------------------------------------------------------------------
# Usage Metrics (for billing/quotas)
# ---------------------------------------------------------------------------


class UsageMetric(Base):
    """Track usage for billing and quotas."""

    __tablename__ = "usage_metrics"

    id = Column(String(36), primary_key=True, default=new_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # llm_tokens, api_calls, storage_bytes, etc.
    value = Column(Float, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)  # model, endpoint, etc.
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_usage_tenant_type_period", "tenant_id", "metric_type", "period_start"),
    )


# ---------------------------------------------------------------------------
# Memory Records (updated with tenant_id)
# ---------------------------------------------------------------------------


class MemoryRecord(Base):
    """A stored memory with embedding vector (multi-tenant)."""

    __tablename__ = "memory_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536) if Vector is not None else Text, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_memory_tenant_created", "tenant_id", "created_at"),
    )


# ---------------------------------------------------------------------------
# Workflow Checkpoints (updated with tenant_id)
# ---------------------------------------------------------------------------


class WorkflowCheckpoint(Base):
    """SQLAlchemy model for persisting workflow checkpoints (multi-tenant)."""

    __tablename__ = "workflow_checkpoints"

    id = Column(String(36), primary_key=True, default=new_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(String(128), nullable=False, index=True)
    step_id = Column(String(128), nullable=False)
    state_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    __table_args__ = (
        Index("ix_checkpoint_tenant_workflow", "tenant_id", "workflow_id"),
    )


# ---------------------------------------------------------------------------
# Agent Definitions (persistent registry)
# ---------------------------------------------------------------------------


class AgentDefinitionRecord(Base):
    """Persistent storage for agent definitions."""

    __tablename__ = "agent_definitions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    version = Column(String(32), nullable=False)
    definition_json = Column(Text, nullable=False)  # Full AgentDefinition as JSON
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_agent_def_tenant_name"),
    )


# ---------------------------------------------------------------------------
# Workflow Definitions (persistent registry)
# ---------------------------------------------------------------------------


class WorkflowDefinitionRecord(Base):
    """Persistent storage for workflow definitions."""

    __tablename__ = "workflow_definitions"

    id = Column(String(36), primary_key=True, default=new_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False, index=True)
    version = Column(String(32), nullable=False)
    definition_json = Column(Text, nullable=False)  # Full WorkflowDefinition as JSON
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_workflow_def_tenant_name"),
    )
