"""Resize embedding vector to configurable dimension and switch to HNSW index.

This migration:
1. Drops the old IVFFlat index (which requires manual re-training and has
   lower recall than HNSW).
2. Drops the old vector(1536) column (data loss — see note below).
3. Re-creates the column at the configured dimension (default 768 for
   nomic-embed-text via Ollama).
4. Creates an HNSW index with cosine distance ops — self-tuning, no
   training step, better recall at comparable speed.

NOTE: This migration is destructive for existing embeddings.  If you have
stored embeddings in memory_documents, they were generated at the old
dimension and cannot be resized.  After running this migration, re-ingest
all documents so new embeddings are generated at the correct dimension.

The default dimension (768) matches nomic-embed-text.  Override via the
EMBEDDING_DIM environment variable if you use a different embedding model.

Revision ID: 002
Revises: 001
Create Date: 2026-03-25 00:00:00.000000
"""

from __future__ import annotations

import os

from alembic import op

revision: str = "002"
down_revision: str = "001"
branch_labels: tuple[str, ...] | None = None
depends_on: str | None = None

# Read dimension from env at migration time; default to 768 (nomic-embed-text).
_EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", "768"))

# HNSW build parameters.
# m=16: max connections per node (good trade-off for 768-dim vectors).
# ef_construction=200: build-time search width (higher = better recall, slower build).
_HNSW_M = 16
_HNSW_EF_CONSTRUCTION = 200


def upgrade() -> None:
    # 1. Drop old IVFFlat index.
    op.execute("DROP INDEX IF EXISTS ix_memory_documents_embedding")

    # 2. Drop old column and re-create at correct dimension.
    op.execute("ALTER TABLE memory_documents DROP COLUMN IF EXISTS embedding")
    op.execute(
        f"ALTER TABLE memory_documents ADD COLUMN embedding vector({_EMBEDDING_DIM})"
    )

    # 3. Create HNSW index (cosine distance).
    op.execute(
        f"CREATE INDEX ix_memory_documents_embedding "
        f"ON memory_documents USING hnsw (embedding vector_cosine_ops) "
        f"WITH (m = {_HNSW_M}, ef_construction = {_HNSW_EF_CONSTRUCTION})"
    )

    # Also handle memory_records table created by ORM auto-create.
    op.execute("DROP INDEX IF EXISTS ix_memory_records_embedding")
    op.execute(
        "ALTER TABLE memory_records DROP COLUMN IF EXISTS embedding"
    )
    op.execute(
        f"ALTER TABLE memory_records ADD COLUMN embedding vector({_EMBEDDING_DIM})"
    )
    op.execute(
        f"CREATE INDEX ix_memory_records_embedding "
        f"ON memory_records USING hnsw (embedding vector_cosine_ops) "
        f"WITH (m = {_HNSW_M}, ef_construction = {_HNSW_EF_CONSTRUCTION})"
    )


def downgrade() -> None:
    # Revert memory_records.
    op.execute("DROP INDEX IF EXISTS ix_memory_records_embedding")
    op.execute("ALTER TABLE memory_records DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE memory_records ADD COLUMN embedding vector(1536)")
    op.execute(
        "CREATE INDEX ix_memory_records_embedding "
        "ON memory_records USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )

    # Revert memory_documents.
    op.execute("DROP INDEX IF EXISTS ix_memory_documents_embedding")
    op.execute("ALTER TABLE memory_documents DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE memory_documents ADD COLUMN embedding vector(1536)")
    op.execute(
        "CREATE INDEX ix_memory_documents_embedding "
        "ON memory_documents USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
