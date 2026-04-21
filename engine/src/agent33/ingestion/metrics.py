"""In-memory task metrics collector for the ingestion pipeline.

Tracks per-event success/failure counts and latency so operators can query a
lightweight summary without standing up a separate observability backend.

CLEAN-ROOM RESTRICTION
=======================
No code in this file may originate from the EvoMap/Evolver project.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class TaskMetricsCollector:
    """Accumulates task-metric records in memory.

    All methods are safe to call from a single-threaded async context.  No
    thread locks are used; this is intentionally lightweight for the pilot.
    """

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(
        self,
        event_type: str,
        tenant_id: str,
        *,
        success: bool,
        latency_ms: float | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Append a metrics record.

        Args:
            event_type: The type of event that was processed.
            tenant_id: Tenant scope for this record.
            success: Whether the processing succeeded.
            latency_ms: Optional elapsed time in milliseconds.
            metadata: Optional arbitrary key/value context.
        """
        self._records.append(
            {
                "event_type": event_type,
                "tenant_id": tenant_id,
                "success": success,
                "latency_ms": latency_ms,
                "metadata": metadata or {},
                "recorded_at": datetime.now(UTC).isoformat(),
            }
        )

    def summary(self, tenant_id: str | None = None) -> dict[str, Any]:
        """Return aggregate counts and average latency.

        Args:
            tenant_id: When given, restrict to records for this tenant only.

        Returns:
            ``{"total": int, "success_count": int, "failure_count": int,
            "avg_latency_ms": float | None}``
        """
        records = (
            [r for r in self._records if r["tenant_id"] == tenant_id]
            if tenant_id is not None
            else list(self._records)
        )
        total = len(records)
        success_count = sum(1 for r in records if r["success"])
        failure_count = total - success_count
        latencies = [r["latency_ms"] for r in records if r["latency_ms"] is not None]
        avg_latency: float | None = sum(latencies) / len(latencies) if latencies else None
        return {
            "total": total,
            "success_count": success_count,
            "failure_count": failure_count,
            "avg_latency_ms": avg_latency,
        }

    def reset(self, tenant_id: str | None = None) -> None:
        """Clear records.

        Args:
            tenant_id: When given, remove only records for this tenant.
                When ``None``, clears all records.
        """
        if tenant_id is None:
            self._records.clear()
        else:
            self._records = [r for r in self._records if r["tenant_id"] != tenant_id]
