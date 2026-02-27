"""Rollback tracking and decision matrix.

Implements rollback procedures from ``core/orchestrator/RELEASE_CADENCE.md``.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from agent33.release.models import (
    RollbackRecord,
    RollbackStatus,
    RollbackType,
)

logger = logging.getLogger(__name__)

# Rollback decision matrix from RELEASE_CADENCE.md
# Maps (severity, impact) to recommended rollback type and approval level
_DECISION_MATRIX: dict[tuple[str, str], tuple[RollbackType, str]] = {
    ("critical", "high"): (RollbackType.IMMEDIATE, "on-call"),
    ("critical", "medium"): (RollbackType.IMMEDIATE, "on-call"),
    ("critical", "low"): (RollbackType.PLANNED, "team-lead"),
    ("high", "high"): (RollbackType.IMMEDIATE, "team-lead"),
    ("high", "medium"): (RollbackType.PLANNED, "team-lead"),
    ("high", "low"): (RollbackType.PLANNED, "team-lead"),
    ("medium", "high"): (RollbackType.PLANNED, "team-lead"),
    ("medium", "medium"): (RollbackType.PARTIAL, "team-lead"),
    ("medium", "low"): (RollbackType.CONFIG, "engineer"),
    ("low", "high"): (RollbackType.PARTIAL, "engineer"),
    ("low", "medium"): (RollbackType.CONFIG, "engineer"),
    ("low", "low"): (RollbackType.CONFIG, "engineer"),
}


class RollbackManager:
    """Track and manage rollbacks."""

    def __init__(self) -> None:
        self._records: dict[str, RollbackRecord] = {}

    def recommend(self, severity: str, impact: str) -> tuple[RollbackType, str]:
        """Get recommended rollback type and approval level.

        Args:
            severity: critical, high, medium, low
            impact: high, medium, low

        Returns:
            (rollback_type, approval_level)
        """
        key = (severity.lower(), impact.lower())
        return _DECISION_MATRIX.get(key, (RollbackType.PLANNED, "team-lead"))

    def create(
        self,
        release_id: str,
        reason: str,
        rollback_type: RollbackType = RollbackType.PLANNED,
        target_version: str = "",
        initiated_by: str = "",
    ) -> RollbackRecord:
        """Create a rollback record."""
        record = RollbackRecord(
            release_id=release_id,
            rollback_type=rollback_type,
            reason=reason,
            target_version=target_version,
            initiated_by=initiated_by,
        )
        self._records[record.rollback_id] = record
        logger.info(
            "rollback_created id=%s release=%s type=%s",
            record.rollback_id,
            release_id,
            rollback_type.value,
        )
        return record

    def approve(self, rollback_id: str, approved_by: str) -> RollbackRecord | None:
        """Approve a rollback."""
        record = self._records.get(rollback_id)
        if record is None:
            return None
        record.approved_by = approved_by
        record.status = RollbackStatus.IN_PROGRESS
        return record

    def complete_step(self, rollback_id: str, step_description: str) -> RollbackRecord | None:
        """Record completion of a rollback step."""
        record = self._records.get(rollback_id)
        if record is None:
            return None
        record.steps_completed.append(step_description)
        return record

    def complete(self, rollback_id: str) -> RollbackRecord | None:
        """Mark a rollback as completed."""
        record = self._records.get(rollback_id)
        if record is None:
            return None
        record.status = RollbackStatus.COMPLETED
        record.completed_at = datetime.now(UTC)
        logger.info("rollback_completed id=%s", rollback_id)
        return record

    def fail(self, rollback_id: str, error: str) -> RollbackRecord | None:
        """Mark a rollback as failed."""
        record = self._records.get(rollback_id)
        if record is None:
            return None
        record.status = RollbackStatus.FAILED
        record.errors.append(error)
        return record

    def get(self, rollback_id: str) -> RollbackRecord | None:
        return self._records.get(rollback_id)

    def list_all(
        self,
        release_id: str | None = None,
        status: RollbackStatus | None = None,
        limit: int = 50,
    ) -> list[RollbackRecord]:
        results = list(self._records.values())
        if release_id is not None:
            results = [r for r in results if r.release_id == release_id]
        if status is not None:
            results = [r for r in results if r.status == status]
        results.sort(key=lambda r: r.created_at, reverse=True)
        return results[:limit]
