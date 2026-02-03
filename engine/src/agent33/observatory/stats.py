"""Statistics service for the Observatory dashboard.

Provides aggregated statistics about knowledge, sources, and usage metrics
with efficient database queries to avoid N+1 problems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agent33.db.models import (
    ActivityLog,
    ActivityType,
    Fact,
    Source,
    UsageMetric,
)

logger = structlog.get_logger()


@dataclass
class TopSubject:
    """A frequently referenced subject in the knowledge base."""

    subject: str
    count: int
    last_seen: datetime | None = None


@dataclass
class KnowledgeStats:
    """Aggregated statistics for the Observatory dashboard."""

    # Fact counts
    total_facts: int = 0
    facts_by_type: dict[str, int] = field(default_factory=dict)

    # Source counts
    total_sources: int = 0
    active_sources: int = 0

    # Content metrics
    total_content_items: int = 0
    content_processed_24h: int = 0
    facts_extracted_24h: int = 0
    queries_answered_24h: int = 0

    # Top referenced subjects
    top_subjects: list[TopSubject] = field(default_factory=list)

    # Recent activity
    recent_activity_count: int = 0


class StatsService:
    """Service for computing Observatory dashboard statistics.

    Uses efficient aggregate queries to minimize database round-trips.
    All queries support optional tenant filtering for multi-tenant deployments.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Initialize the stats service.

        Args:
            session_factory: SQLAlchemy async session factory for database access.
        """
        self._session_factory = session_factory
        self._logger = logger.bind(service="stats")

    async def get_knowledge_stats(
        self,
        tenant_id: UUID | None = None,
    ) -> KnowledgeStats:
        """Get aggregated knowledge statistics.

        Computes all dashboard statistics in efficient batched queries.

        Args:
            tenant_id: Optional tenant filter. If None, returns global stats.

        Returns:
            KnowledgeStats with all computed metrics.
        """
        stats = KnowledgeStats()
        now = datetime.now(UTC)
        twenty_four_hours_ago = now - timedelta(hours=24)

        async with self._session_factory() as session:
            # Build tenant filter condition
            tenant_filter = []
            if tenant_id is not None:
                tenant_id_str = str(tenant_id)
                tenant_filter = [Fact.tenant_id == tenant_id_str]

            # Query 1: Total facts count
            facts_count_stmt = select(func.count(Fact.id))
            if tenant_filter:
                facts_count_stmt = facts_count_stmt.where(*tenant_filter)
            result = await session.execute(facts_count_stmt)
            stats.total_facts = result.scalar() or 0

            # Query 2: Facts by type (extracted from metadata)
            # The fact type is stored in metadata_.type field if present
            # We use a single aggregated query with conditional counting
            stats.facts_by_type = await self._get_facts_by_type(
                session, tenant_id
            )

            # Query 3: Source counts (total and active) in a single query
            source_counts_stmt = select(
                func.count(Source.id).label("total"),
                func.count(
                    case((Source.is_active == True, Source.id))  # noqa: E712
                ).label("active"),
            )
            if tenant_id is not None:
                source_counts_stmt = source_counts_stmt.where(
                    Source.tenant_id == str(tenant_id)
                )
            result = await session.execute(source_counts_stmt)
            row = result.one()
            stats.total_sources = row.total or 0
            stats.active_sources = row.active or 0

            # Query 4: Total content items (sum of items_fetched from sources)
            content_items_stmt = select(func.coalesce(func.sum(Source.items_fetched), 0))
            if tenant_id is not None:
                content_items_stmt = content_items_stmt.where(
                    Source.tenant_id == str(tenant_id)
                )
            result = await session.execute(content_items_stmt)
            stats.total_content_items = result.scalar() or 0

            # Query 5: Content processed in last 24h (activities of type INGESTED)
            content_24h_stmt = select(func.count(ActivityLog.id)).where(
                ActivityLog.activity_type == ActivityType.INGESTED,
                ActivityLog.created_at >= twenty_four_hours_ago,
            )
            if tenant_id is not None:
                content_24h_stmt = content_24h_stmt.where(
                    ActivityLog.tenant_id == str(tenant_id)
                )
            result = await session.execute(content_24h_stmt)
            stats.content_processed_24h = result.scalar() or 0

            # Query 6: Facts extracted in last 24h
            facts_24h_stmt = select(func.count(Fact.id)).where(
                Fact.created_at >= twenty_four_hours_ago,
            )
            if tenant_id is not None:
                facts_24h_stmt = facts_24h_stmt.where(
                    Fact.tenant_id == str(tenant_id)
                )
            result = await session.execute(facts_24h_stmt)
            stats.facts_extracted_24h = result.scalar() or 0

            # Query 7: Queries answered in last 24h (QUERIED or RESPONDED activities)
            queries_24h_stmt = select(func.count(ActivityLog.id)).where(
                ActivityLog.activity_type.in_(
                    [ActivityType.QUERIED, ActivityType.RESPONDED]
                ),
                ActivityLog.created_at >= twenty_four_hours_ago,
            )
            if tenant_id is not None:
                queries_24h_stmt = queries_24h_stmt.where(
                    ActivityLog.tenant_id == str(tenant_id)
                )
            result = await session.execute(queries_24h_stmt)
            stats.queries_answered_24h = result.scalar() or 0

            # Query 8: Top subjects (most referenced in fact metadata)
            stats.top_subjects = await self._get_top_subjects(
                session, tenant_id, limit=10
            )

            # Query 9: Recent activity count (last 24h, all types)
            recent_activity_stmt = select(func.count(ActivityLog.id)).where(
                ActivityLog.created_at >= twenty_four_hours_ago,
            )
            if tenant_id is not None:
                recent_activity_stmt = recent_activity_stmt.where(
                    ActivityLog.tenant_id == str(tenant_id)
                )
            result = await session.execute(recent_activity_stmt)
            stats.recent_activity_count = result.scalar() or 0

        self._logger.debug(
            "computed_knowledge_stats",
            tenant_id=str(tenant_id) if tenant_id else None,
            total_facts=stats.total_facts,
            active_sources=stats.active_sources,
        )

        return stats

    async def _get_facts_by_type(
        self,
        session: AsyncSession,
        tenant_id: UUID | None,
    ) -> dict[str, int]:
        """Get count of facts grouped by type.

        Fact types are stored in the metadata_.type field. Common types:
        - entity: Named entities (people, organizations, places)
        - relationship: Connections between entities
        - claim: Assertions or statements
        - event: Timestamped occurrences

        Args:
            session: Active database session.
            tenant_id: Optional tenant filter.

        Returns:
            Dictionary mapping fact type to count.
        """
        # Since fact type is stored in JSONB metadata, we need to extract it
        # PostgreSQL: metadata->>'type' extracts the type field as text
        # We use a raw SQL approach for JSONB field extraction

        # Build the base query with JSONB extraction
        # This counts facts grouped by their metadata type field
        type_counts: dict[str, int] = {
            "entity": 0,
            "relationship": 0,
            "claim": 0,
            "event": 0,
        }

        # Query facts and extract type from metadata
        # Using conditional counting for each type to avoid multiple queries
        for fact_type in type_counts:
            stmt = select(func.count(Fact.id)).where(
                Fact.metadata_["type"].astext == fact_type
            )
            if tenant_id is not None:
                stmt = stmt.where(Fact.tenant_id == str(tenant_id))

            result = await session.execute(stmt)
            type_counts[fact_type] = result.scalar() or 0

        # Also count facts without a type (or with unknown type)
        known_types = list(type_counts.keys())
        untyped_conditions = [
            Fact.metadata_["type"].astext.notin_(known_types),
        ]

        untyped_stmt = select(func.count(Fact.id)).where(
            func.coalesce(Fact.metadata_["type"].astext, "") == ""
        )
        if tenant_id is not None:
            untyped_stmt = untyped_stmt.where(Fact.tenant_id == str(tenant_id))

        result = await session.execute(untyped_stmt)
        untyped_count = result.scalar() or 0
        if untyped_count > 0:
            type_counts["untyped"] = untyped_count

        return type_counts

    async def _get_top_subjects(
        self,
        session: AsyncSession,
        tenant_id: UUID | None,
        limit: int = 10,
    ) -> list[TopSubject]:
        """Get the most frequently referenced subjects.

        Subjects are extracted from the metadata_.subject field of facts.

        Args:
            session: Active database session.
            tenant_id: Optional tenant filter.
            limit: Maximum number of subjects to return.

        Returns:
            List of TopSubject ordered by reference count descending.
        """
        # Extract subject from metadata and group/count
        # PostgreSQL JSONB: metadata->>'subject'
        subject_col = Fact.metadata_["subject"].astext

        stmt = (
            select(
                subject_col.label("subject"),
                func.count(Fact.id).label("count"),
                func.max(Fact.created_at).label("last_seen"),
            )
            .where(subject_col.isnot(None), subject_col != "")
            .group_by(subject_col)
            .order_by(func.count(Fact.id).desc())
            .limit(limit)
        )

        if tenant_id is not None:
            stmt = stmt.where(Fact.tenant_id == str(tenant_id))

        result = await session.execute(stmt)
        rows = result.all()

        return [
            TopSubject(
                subject=row.subject,
                count=row.count,
                last_seen=row.last_seen,
            )
            for row in rows
            if row.subject  # Filter out any null/empty subjects
        ]

    async def record_metric(
        self,
        tenant_id: UUID,
        metric_type: str,
        value: int,
        metadata: dict[str, Any] | None = None,
    ) -> UsageMetric:
        """Record a usage metric.

        Creates a new usage metric record for tracking billing, quotas,
        and system analytics.

        Args:
            tenant_id: The tenant this metric belongs to.
            metric_type: Type of metric (e.g., "llm_tokens", "api_calls",
                "storage_bytes", "facts_extracted", "queries_answered").
            value: The metric value to record.
            metadata: Optional additional context (model name, endpoint, etc.).

        Returns:
            The created UsageMetric record.
        """
        now = datetime.now(UTC)

        # Create metric with period covering the instant of recording
        # For aggregation, period_start is set to the current timestamp
        # and period_end to one second later (instant metric)
        metric = UsageMetric(
            tenant_id=str(tenant_id),
            metric_type=metric_type,
            value=float(value),
            metadata_=metadata or {},
            period_start=now,
            period_end=now + timedelta(seconds=1),
        )

        async with self._session_factory() as session:
            session.add(metric)
            await session.commit()
            await session.refresh(metric)

        self._logger.debug(
            "recorded_metric",
            tenant_id=str(tenant_id),
            metric_type=metric_type,
            value=value,
        )

        return metric

    async def get_usage(
        self,
        tenant_id: UUID,
        metric_type: str,
        start: datetime,
        end: datetime,
    ) -> int:
        """Get aggregated usage for a time period.

        Sums all metric values of the specified type within the time range.

        Args:
            tenant_id: The tenant to query metrics for.
            metric_type: Type of metric to aggregate.
            start: Start of the time range (inclusive).
            end: End of the time range (exclusive).

        Returns:
            Total usage value as an integer.
        """
        stmt = select(func.coalesce(func.sum(UsageMetric.value), 0)).where(
            UsageMetric.tenant_id == str(tenant_id),
            UsageMetric.metric_type == metric_type,
            UsageMetric.period_start >= start,
            UsageMetric.period_start < end,
        )

        async with self._session_factory() as session:
            result = await session.execute(stmt)
            total = result.scalar() or 0

        self._logger.debug(
            "queried_usage",
            tenant_id=str(tenant_id),
            metric_type=metric_type,
            start=start.isoformat(),
            end=end.isoformat(),
            total=total,
        )

        return int(total)
