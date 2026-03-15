"""Export provenance data as audit bundles."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from agent33.provenance.models import AuditBundle, AuditTimelineEntry
from agent33.provenance.timeline import _summarize

if TYPE_CHECKING:
    from agent33.provenance.collector import ProvenanceCollector


class AuditExporter:
    """Creates exportable audit bundles from collected provenance receipts."""

    def __init__(self, collector: ProvenanceCollector) -> None:
        self._collector = collector

    def export(
        self,
        *,
        tenant_id: str = "",
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> AuditBundle:
        """Build and return an :class:`AuditBundle`.

        *since* and *until* bound the time window.  When *until* is supplied,
        a large ``limit`` is used and results are post-filtered.
        """
        # Fetch a generous upper bound; the deque is capped at max_receipts.
        receipts = self._collector.query(
            tenant_id=tenant_id,
            since=since,
            limit=self._collector._max_receipts,  # noqa: SLF001
        )

        if until is not None:
            receipts = [r for r in receipts if r.timestamp <= until]

        entries = [
            AuditTimelineEntry(
                timestamp=r.timestamp,
                source=r.source,
                actor=r.actor,
                summary=_summarize(r.source, r.metadata),
                receipt_id=r.receipt_id,
            )
            for r in receipts
        ]

        return AuditBundle(
            bundle_id=uuid4().hex,
            created_at=datetime.now(UTC),
            entries=entries,
            total_entries=len(entries),
        )
