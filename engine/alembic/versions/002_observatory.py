"""Observatory multi-tenant schema -- tenants, api_keys, sources, facts, activity_log, etc.

Revision ID: 002
Revises: 001
Create Date: 2025-02-03 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision: str = "002"
down_revision: str = "001"
branch_labels: tuple[str, ...] | None = None
depends_on: str | None = None

# Default public tenant UUID
DEFAULT_TENANT_ID = "00000000-0000-0000-0000-000000000000"


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Create new tables
    # -------------------------------------------------------------------------

    # tenants
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False),
        sa.Column("settings", JSONB(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    # api_keys
    op.create_table(
        "api_keys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("key_hash", sa.Text(), nullable=False),
        sa.Column("key_prefix", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("scopes", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_api_keys_tenant_id", "api_keys", ["tenant_id"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    # sources
    op.create_table(
        "sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("config", JSONB(), nullable=False, server_default="{}"),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fetch_cursor", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_sources_tenant_id", "sources", ["tenant_id"])
    op.create_index("ix_sources_source_type", "sources", ["source_type"])

    # facts (with vector column)
    op.create_table(
        "facts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), nullable=True),
        sa.Column("fact_type", sa.Text(), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("predicate", sa.Text(), nullable=True),
        sa.Column("object", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("metadata", JSONB(), nullable=False, server_default="{}"),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_by", UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["superseded_by"], ["facts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_facts_tenant_id", "facts", ["tenant_id"])
    op.create_index("ix_facts_source_id", "facts", ["source_id"])
    op.create_index("ix_facts_fact_type", "facts", ["fact_type"])
    op.create_index("ix_facts_subject", "facts", ["subject"])
    # Add vector column via raw SQL (pgvector type)
    op.execute("ALTER TABLE facts ADD COLUMN embedding vector(1536)")
    op.execute(
        "CREATE INDEX ix_facts_embedding "
        "ON facts USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # activity_log
    op.create_table(
        "activity_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), nullable=True),
        sa.Column("fact_id", UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["fact_id"], ["facts.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_activity_log_tenant_id", "activity_log", ["tenant_id"])
    op.create_index("ix_activity_log_created_at", "activity_log", ["created_at"])
    op.create_index("ix_activity_log_event_type", "activity_log", ["event_type"])

    # ingested_content
    op.create_table(
        "ingested_content",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", UUID(as_uuid=True), nullable=True),
        sa.Column("external_id", sa.Text(), nullable=True),
        sa.Column("content_type", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("processed_content", sa.Text(), nullable=True),
        sa.Column("language", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", JSONB(), nullable=False, server_default="{}"),
        sa.Column("processing_status", sa.Text(), nullable=True),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ingested_content_tenant_id", "ingested_content", ["tenant_id"])
    op.create_index("ix_ingested_content_source_id", "ingested_content", ["source_id"])
    op.create_index("ix_ingested_content_external_id", "ingested_content", ["external_id"])
    op.create_index("ix_ingested_content_processing_status", "ingested_content", ["processing_status"])

    # usage_metrics
    op.create_table(
        "usage_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column("metric_type", sa.Text(), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("value", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("metadata", JSONB(), nullable=False, server_default="{}"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_usage_metrics_tenant_id", "usage_metrics", ["tenant_id"])
    op.create_index("ix_usage_metrics_metric_type", "usage_metrics", ["metric_type"])
    op.create_index("ix_usage_metrics_period_start", "usage_metrics", ["period_start"])

    # -------------------------------------------------------------------------
    # 2. Add tenant_id to existing tables
    # -------------------------------------------------------------------------

    # Create memory_records table (if not exists from 001, the task references it)
    # First check if it exists by trying to add column; if table doesn't exist, create it
    op.execute("""
        CREATE TABLE IF NOT EXISTS memory_records (
            id UUID PRIMARY KEY,
            content TEXT NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    # Add embedding column if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'memory_records' AND column_name = 'embedding'
            ) THEN
                ALTER TABLE memory_records ADD COLUMN embedding vector(1536);
            END IF;
        END $$;
    """)

    # Add tenant_id to memory_records
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'memory_records' AND column_name = 'tenant_id'
            ) THEN
                ALTER TABLE memory_records ADD COLUMN tenant_id UUID;
                UPDATE memory_records SET tenant_id = '{DEFAULT_TENANT_ID}' WHERE tenant_id IS NULL;
                ALTER TABLE memory_records ALTER COLUMN tenant_id SET NOT NULL;
                ALTER TABLE memory_records ADD CONSTRAINT fk_memory_records_tenant
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
                CREATE INDEX IF NOT EXISTS ix_memory_records_tenant_id ON memory_records(tenant_id);
            END IF;
        END $$;
    """)

    # Add tenant_id to workflow_checkpoints (from 001 migration)
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'workflow_checkpoints' AND column_name = 'tenant_id'
            ) THEN
                ALTER TABLE workflow_checkpoints ADD COLUMN tenant_id UUID;
                UPDATE workflow_checkpoints SET tenant_id = '{DEFAULT_TENANT_ID}' WHERE tenant_id IS NULL;
                ALTER TABLE workflow_checkpoints ALTER COLUMN tenant_id SET NOT NULL;
                ALTER TABLE workflow_checkpoints ADD CONSTRAINT fk_workflow_checkpoints_tenant
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE;
                CREATE INDEX IF NOT EXISTS ix_workflow_checkpoints_tenant_id ON workflow_checkpoints(tenant_id);
            END IF;
        END $$;
    """)

    # -------------------------------------------------------------------------
    # 3. Insert default public tenant
    # -------------------------------------------------------------------------
    op.execute(f"""
        INSERT INTO tenants (id, name, slug, settings, is_active, created_at, updated_at)
        VALUES (
            '{DEFAULT_TENANT_ID}',
            'Public',
            'public',
            '{{}}'::jsonb,
            true,
            NOW(),
            NOW()
        )
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    # Remove tenant_id from existing tables
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_workflow_checkpoints_tenant'
            ) THEN
                ALTER TABLE workflow_checkpoints DROP CONSTRAINT fk_workflow_checkpoints_tenant;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'workflow_checkpoints' AND column_name = 'tenant_id'
            ) THEN
                DROP INDEX IF EXISTS ix_workflow_checkpoints_tenant_id;
                ALTER TABLE workflow_checkpoints DROP COLUMN tenant_id;
            END IF;
        END $$;
    """)

    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = 'fk_memory_records_tenant'
            ) THEN
                ALTER TABLE memory_records DROP CONSTRAINT fk_memory_records_tenant;
            END IF;
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'memory_records' AND column_name = 'tenant_id'
            ) THEN
                DROP INDEX IF EXISTS ix_memory_records_tenant_id;
                ALTER TABLE memory_records DROP COLUMN tenant_id;
            END IF;
        END $$;
    """)

    # Drop tables in reverse dependency order
    op.drop_table("usage_metrics")
    op.drop_table("ingested_content")
    op.drop_table("activity_log")
    op.drop_table("facts")
    op.drop_table("sources")
    op.drop_table("api_keys")
    op.drop_table("tenants")

    # Note: memory_records table is left intact (may have been created by this migration
    # but could also exist from other sources; safer to leave it)
