"""Execution lineage tracking for workflow steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class LineageRecord:
    """Single lineage entry for one workflow step."""

    workflow_id: str
    step_id: str
    action: str
    inputs_hash: str
    outputs_hash: str
    parent_id: str | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ExecutionLineage:
    """Records and queries execution lineage for workflows."""

    def __init__(self) -> None:
        self._records: list[LineageRecord] = []

    def record(
        self,
        workflow_id: str,
        step_id: str,
        action: str,
        inputs_hash: str,
        outputs_hash: str,
        parent_id: str | None = None,
    ) -> LineageRecord:
        """Record a lineage entry and return it."""
        entry = LineageRecord(
            workflow_id=workflow_id,
            step_id=step_id,
            action=action,
            inputs_hash=inputs_hash,
            outputs_hash=outputs_hash,
            parent_id=parent_id,
        )
        self._records.append(entry)
        return entry

    def query(self, workflow_id: str) -> list[LineageRecord]:
        """Return all lineage records for a workflow."""
        return [r for r in self._records if r.workflow_id == workflow_id]
