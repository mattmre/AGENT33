"""Workflow event types for real-time run-scoped status streaming."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowEventType(StrEnum):
    """Types of events emitted during workflow execution."""

    SYNC = "sync"
    HEARTBEAT = "heartbeat"
    WORKFLOW_STARTED = "workflow_started"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_SKIPPED = "step_skipped"
    STEP_RETRYING = "step_retrying"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"


@dataclass(frozen=True)
class WorkflowEvent:
    """Immutable event emitted during a single workflow execution run.

    ``run_id`` is the unique execution identifier. ``workflow_name`` identifies the
    workflow definition shared across multiple runs.
    """

    event_type: WorkflowEventType
    run_id: str
    workflow_name: str
    timestamp: float = field(default_factory=time.time)
    step_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON serialization."""
        result: dict[str, Any] = {
            "type": self.event_type.value,
            "run_id": self.run_id,
            "workflow_name": self.workflow_name,
            "timestamp": self.timestamp,
        }
        if self.step_id is not None:
            result["step_id"] = self.step_id
        if self.data:
            result["data"] = self.data
        return result

    def to_json(self) -> str:
        """Serialize the event to a JSON string for transport."""
        return json.dumps(self.to_dict())
