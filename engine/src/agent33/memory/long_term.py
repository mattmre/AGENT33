"""Long-term memory backed by pgvector for semantic search."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover
    Vector = None  # type: ignore[assignment,misc]


class _Base(DeclarativeBase):
    pass


class MemoryRecord(_Base):
    """A stored memory with embedding vector."""

    __tablename__ = "memory_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536) if Vector is not None else Text, nullable=False)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


@dataclass
class SearchResult:
    """A single search result from long-term memory."""

    text: str
    score: float
    metadata: dict[str, Any]


class LongTermMemory:
    """Semantic search over stored memories using pgvector."""

    def __init__(self, database_url: str, embedding_dim: int = 1536) -> None:
        self._engine = create_async_engine(database_url, echo=False)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)
        self._embedding_dim = embedding_dim

    async def initialize(self) -> None:
        """Create tables and enable pgvector extension."""
        async with self._engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(_Base.metadata.create_all)

    async def store(
        self,
        content: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> int:
        """Store text with its embedding. Returns the record id."""
        record = MemoryRecord(
            content=content,
            embedding=embedding,
            metadata_=metadata or {},
        )
        async with self._session_factory() as session, session.begin():
            session.add(record)
            await session.flush()
            record_id: int = record.id  # type: ignore[assignment]
        return record_id

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[SearchResult]:
        """Find the *top_k* most similar memories by cosine distance."""
        embedding_literal = f"[{','.join(str(v) for v in query_embedding)}]"
        sql = text(
            "SELECT content, metadata, "
            "1 - (embedding <=> :emb::vector) AS score "
            "FROM memory_records "
            "ORDER BY embedding <=> :emb::vector "
            "LIMIT :k"
        )
        async with self._session_factory() as session:
            result = await session.execute(
                sql, {"emb": embedding_literal, "k": top_k}
            )
            rows = result.fetchall()
        return [
            SearchResult(text=row[0], score=float(row[1]), metadata=row[2] or {})
            for row in rows
        ]

    async def close(self) -> None:
        """Dispose of the engine connection pool."""
        await self._engine.dispose()
