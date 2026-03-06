"""Workflow event types for real-time WebSocket status streaming."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowEventType(StrEnum):
    """Types of events emitted during workflow execution."""

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
    """Immutable event emitted during workflow execution.

    Attributes:
        event_type: The kind of event.
        workflow_id: Identifier for the workflow execution run.
        timestamp: Unix epoch timestamp (seconds).
        step_id: Optional step identifier (populated for step-level events).
        data: Arbitrary payload specific to the event type.
    """

    event_type: WorkflowEventType
    workflow_id: str
    timestamp: float = field(default_factory=time.time)
    step_id: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a plain dict suitable for JSON serialization."""
        result: dict[str, Any] = {
            "type": self.event_type.value,
            "workflow_id": self.workflow_id,
            "timestamp": self.timestamp,
        }
        if self.step_id is not None:
            result["step_id"] = self.step_id
        if self.data:
            result["data"] = self.data
        return result

    def to_json(self) -> str:
        """Serialize the event to a JSON string for WebSocket transmission."""
        return json.dumps(self.to_dict())
