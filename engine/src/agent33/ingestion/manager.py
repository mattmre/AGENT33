"""Ingestion manager - orchestrates all ingestion workers."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent33.db.models import ActivityLog, ActivityType, Fact, Source, SourceType
from agent33.db.session import get_session_factory
from agent33.ingestion.base import BaseWorker, IngestResult
from agent33.ingestion.gdelt import GDELTWorker
from agent33.ingestion.rss import RSSWorker
from agent33.ingestion.youtube import YouTubeWorker

logger = structlog.get_logger()

WORKER_CLASSES: dict[str, type[BaseWorker]] = {
    "gdelt": GDELTWorker,
    "rss": RSSWorker,
    "youtube": YouTubeWorker,
}


class IngestionManager:
    """Manages ingestion workers and stores results."""

    def __init__(self, tenant_id: str) -> None:
        self.tenant_id = tenant_id
        self._session_factory = get_session_factory()
        self._logger = logger.bind(manager="ingestion", tenant_id=tenant_id)

    async def run_source(self, source_id: str) -> dict[str, Any]:
        """Run ingestion for a single source.

        Args:
            source_id: The source ID to ingest from.

        Returns:
            Summary of ingestion results.
        """
        async with self._session_factory() as session:
            # Load source config
            source = await session.get(Source, source_id)
            if not source:
                raise ValueError(f"Source not found: {source_id}")

            if source.tenant_id != self.tenant_id:
                raise PermissionError("Source belongs to different tenant")

            if not source.is_active:
                self._logger.info("source_inactive", source_id=source_id)
                return {"status": "skipped", "reason": "inactive"}

            # Create worker
            worker_cls = WORKER_CLASSES.get(source.source_type.value)
            if not worker_cls:
                raise ValueError(f"Unknown source type: {source.source_type}")

            worker = worker_cls(
                tenant_id=self.tenant_id,
                source_id=source_id,
                config={"url": source.url, **source.config},
            )

            # Run ingestion
            try:
                results = await worker.run()

                # Store results
                new_facts = 0
                for result in results:
                    stored = await self._store_result(session, source, result)
                    if stored:
                        new_facts += 1

                # Update source metadata
                source.last_fetched_at = datetime.now(UTC)
                source.items_fetched += len(results)
                source.last_error = None

                await session.commit()

                # Log activity
                await self._log_activity(
                    session,
                    ActivityType.INGESTED,
                    f"Ingested {len(results)} items from {source.name}",
                    f"New facts: {new_facts}, Source: {source.source_type.value}",
                    source_id=source_id,
                    metadata={"items_fetched": len(results), "new_facts": new_facts},
                )

                return {
                    "status": "success",
                    "items_fetched": len(results),
                    "new_facts": new_facts,
                }

            except Exception as e:
                source.last_error = str(e)
                await session.commit()

                self._logger.error(
                    "ingestion_failed",
                    source_id=source_id,
                    error=str(e),
                )
                raise

    async def run_all_sources(self, source_type: SourceType | None = None) -> dict[str, Any]:
        """Run ingestion for all active sources.

        Args:
            source_type: Optional filter by source type.

        Returns:
            Summary of all ingestion results.
        """
        async with self._session_factory() as session:
            stmt = select(Source).where(
                Source.tenant_id == self.tenant_id,
                Source.is_active == True,  # noqa: E712
            )
            if source_type:
                stmt = stmt.where(Source.source_type == source_type)

            result = await session.execute(stmt)
            sources = result.scalars().all()

        results = {}
        for source in sources:
            try:
                result = await self.run_source(source.id)
                results[source.id] = result
            except Exception as e:
                results[source.id] = {"status": "error", "error": str(e)}

        return {
            "total_sources": len(sources),
            "results": results,
        }

    async def _store_result(
        self,
        session: AsyncSession,
        source: Source,
        result: IngestResult,
    ) -> bool:
        """Store an ingestion result as a fact.

        Returns True if a new fact was created, False if duplicate.
        """
        # Check for duplicate by content hash
        content_hash = result.content_hash or hashlib.sha256(
            result.content.encode()
        ).hexdigest()

        stmt = select(Fact).where(
            Fact.tenant_id == self.tenant_id,
            Fact.content_hash == content_hash,
        )
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            return False

        # Create new fact
        fact = Fact(
            tenant_id=self.tenant_id,
            source_id=source.id,
            content=result.content,
            content_hash=content_hash,
            source_url=result.source_url,
            metadata_={
                "title": result.title,
                "published_at": result.published_at.isoformat() if result.published_at else None,
                **result.metadata,
            },
        )
        session.add(fact)

        # Log the learning activity
        await self._log_activity(
            session,
            ActivityType.LEARNED,
            f"Learned: {result.title[:100]}" if result.title else "Learned new fact",
            result.content[:500] if result.content else None,
            source_id=source.id,
            metadata={"fact_id": fact.id, "source_url": result.source_url},
        )

        return True

    async def _log_activity(
        self,
        session: AsyncSession,
        activity_type: ActivityType,
        title: str,
        description: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        is_public: bool = True,
    ) -> ActivityLog:
        """Log an activity event."""
        activity = ActivityLog(
            tenant_id=self.tenant_id,
            activity_type=activity_type,
            title=title,
            description=description,
            source_id=source_id,
            metadata_=metadata or {},
            is_public=is_public,
        )
        session.add(activity)
        return activity


async def create_default_sources(tenant_id: str) -> list[Source]:
    """Create default ingestion sources for a new tenant.

    Returns list of created sources.
    """
    session_factory = get_session_factory()

    default_sources = [
        {
            "name": "GDELT World News",
            "source_type": SourceType.GDELT,
            "url": None,
            "config": {
                "query": "sourcelang:eng",
                "max_records": 50,
                "timespan": "15min",
            },
        },
        {
            "name": "Hacker News",
            "source_type": SourceType.RSS,
            "url": "https://news.ycombinator.com/rss",
            "config": {"max_items": 30},
        },
        {
            "name": "Reuters Top News",
            "source_type": SourceType.RSS,
            "url": "https://feeds.reuters.com/reuters/topNews",
            "config": {"max_items": 20},
        },
        {
            "name": "Ars Technica",
            "source_type": SourceType.RSS,
            "url": "https://feeds.arstechnica.com/arstechnica/index",
            "config": {"max_items": 20},
        },
    ]

    sources = []
    async with session_factory() as session:
        for source_config in default_sources:
            source = Source(
                tenant_id=tenant_id,
                name=source_config["name"],
                source_type=source_config["source_type"],
                url=source_config["url"],
                config=source_config["config"],
                is_active=True,
            )
            session.add(source)
            sources.append(source)

        await session.commit()

    return sources
