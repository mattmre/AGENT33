"""WebSocket connection manager for run-scoped workflow event streaming."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

from agent33.workflows.events import WorkflowEvent, WorkflowEventType

if TYPE_CHECKING:
    from starlette.websockets import WebSocket

logger = structlog.get_logger()


@dataclass
class WorkflowRunSnapshot:
    """Current server-side view of a workflow execution run."""

    run_id: str
    workflow_name: str
    status: str = "pending"
    step_statuses: dict[str, str] = field(default_factory=dict)
    last_event_type: str | None = None
    updated_at: float = field(default_factory=time.time)
    terminal: bool = False
    error: str | None = None
    duration_ms: float | None = None

    def to_event_data(self) -> dict[str, Any]:
        """Return the transport payload used by sync events."""
        data: dict[str, Any] = {
            "status": self.status,
            "step_statuses": dict(self.step_statuses),
            "last_event_type": self.last_event_type,
            "terminal": self.terminal,
            "updated_at": self.updated_at,
        }
        if self.error is not None:
            data["error"] = self.error
        if self.duration_ms is not None:
            data["duration_ms"] = self.duration_ms
        return data


class WorkflowWSManager:
    """Manages WebSocket subscriptions and snapshots for workflow runs."""

    def __init__(self, heartbeat_interval_seconds: float = 30.0) -> None:
        self._subscriptions: dict[str, set[Any]] = {}
        self._reverse: dict[Any, set[str]] = {}
        self._sse_subscriptions: dict[str, set[asyncio.Queue[WorkflowEvent]]] = {}
        self._snapshots: dict[str, WorkflowRunSnapshot] = {}
        self._lock = asyncio.Lock()
        self.heartbeat_interval_seconds = heartbeat_interval_seconds

    async def register_run(self, run_id: str, workflow_name: str) -> None:
        """Ensure a snapshot exists for *run_id*."""
        async with self._lock:
            self._snapshots.setdefault(
                run_id,
                WorkflowRunSnapshot(run_id=run_id, workflow_name=workflow_name),
            )

    async def has_run(self, run_id: str) -> bool:
        """Return ``True`` when *run_id* is known to the manager."""
        async with self._lock:
            return run_id in self._snapshots

    async def connect(self, ws: WebSocket, run_id: str) -> bool:
        """Subscribe *ws* to a single workflow *run_id*."""
        async with self._lock:
            if run_id not in self._snapshots:
                return False

            self._subscriptions.setdefault(run_id, set()).add(ws)
            self._reverse.setdefault(ws, set()).add(run_id)

        logger.debug(
            "ws_run_connected",
            run_id=run_id,
            active_subs=await self.active_subscriptions(run_id),
        )
        return True

    async def disconnect(self, ws: WebSocket) -> None:
        """Remove *ws* from all tracked subscriptions."""
        async with self._lock:
            run_ids = list(self._reverse.pop(ws, set()))
            for run_id in run_ids:
                subs = self._subscriptions.get(run_id)
                if subs is not None:
                    subs.discard(ws)
                    if not subs:
                        del self._subscriptions[run_id]

        if run_ids:
            logger.debug("ws_disconnected", removed_subscriptions=len(run_ids))

    async def subscribe_sse(
        self,
        run_id: str,
    ) -> asyncio.Queue[WorkflowEvent] | None:
        """Register and return an SSE queue for *run_id*."""
        queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue()
        async with self._lock:
            if run_id not in self._snapshots:
                return None
            self._sse_subscriptions.setdefault(run_id, set()).add(queue)
        return queue

    async def unsubscribe_sse(
        self,
        run_id: str,
        queue: asyncio.Queue[WorkflowEvent],
    ) -> None:
        """Remove a previously registered SSE queue for *run_id*."""
        async with self._lock:
            subscribers = self._sse_subscriptions.get(run_id)
            if subscribers is None:
                return
            subscribers.discard(queue)
            if not subscribers:
                del self._sse_subscriptions[run_id]

    async def publish_event(self, event: WorkflowEvent) -> None:
        """Update the run snapshot and fan out *event* to subscribers."""
        async with self._lock:
            snapshot = self._snapshots.setdefault(
                event.run_id,
                WorkflowRunSnapshot(
                    run_id=event.run_id,
                    workflow_name=event.workflow_name,
                ),
            )
            self._apply_event(snapshot, event)
            targets = list(self._subscriptions.get(event.run_id, set()))
            sse_targets = list(self._sse_subscriptions.get(event.run_id, set()))

        for queue in sse_targets:
            queue.put_nowait(event)

        if not targets:
            return

        payload = event.to_json()
        dead: list[Any] = []
        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for ws in dead:
                    self._remove_ws_unlocked(ws)
            logger.debug("ws_dead_connections_cleaned", count=len(dead))

    async def build_sync_event(self, run_id: str) -> WorkflowEvent | None:
        """Build a transport-neutral snapshot event for *run_id*."""
        async with self._lock:
            snapshot = self._snapshots.get(run_id)
            if snapshot is None:
                return None
            data = snapshot.to_event_data()
            workflow_name = snapshot.workflow_name

        return WorkflowEvent(
            event_type=WorkflowEventType.SYNC,
            run_id=run_id,
            workflow_name=workflow_name,
            data=data,
        )

    async def send_sync(self, ws: WebSocket, run_id: str) -> bool:
        """Send the latest snapshot for *run_id* to *ws*."""
        event = await self.build_sync_event(run_id)
        if event is None:
            return False
        await ws.send_text(event.to_json())
        return True

    async def build_heartbeat_event(self, run_id: str) -> WorkflowEvent | None:
        """Build a transport-neutral heartbeat event for *run_id*."""
        async with self._lock:
            snapshot = self._snapshots.get(run_id)
            if snapshot is None:
                return None
            workflow_name = snapshot.workflow_name
            status = snapshot.status
            terminal = snapshot.terminal

        return WorkflowEvent(
            event_type=WorkflowEventType.HEARTBEAT,
            run_id=run_id,
            workflow_name=workflow_name,
            data={"status": status, "terminal": terminal},
        )

    async def send_heartbeat(self, ws: WebSocket, run_id: str) -> bool:
        """Send a heartbeat event for *run_id* to *ws*."""
        event = await self.build_heartbeat_event(run_id)
        if event is None:
            return False
        await ws.send_text(event.to_json())
        return True

    async def active_subscriptions(self, run_id: str) -> int:
        """Return the number of active subscribers for *run_id*."""
        async with self._lock:
            return len(self._subscriptions.get(run_id, set()))

    async def active_sse_subscriptions(self, run_id: str) -> int:
        """Return the number of active SSE subscribers for *run_id*."""
        async with self._lock:
            return len(self._sse_subscriptions.get(run_id, set()))

    async def connected_count(self) -> int:
        """Return the total number of tracked WebSocket connections."""
        async with self._lock:
            return len(self._reverse)

    def _apply_event(self, snapshot: WorkflowRunSnapshot, event: WorkflowEvent) -> None:
        snapshot.workflow_name = event.workflow_name
        snapshot.last_event_type = event.event_type.value
        snapshot.updated_at = event.timestamp

        if event.event_type == WorkflowEventType.WORKFLOW_STARTED:
            snapshot.status = "running"
            snapshot.terminal = False
            snapshot.error = None
            return

        if event.event_type == WorkflowEventType.STEP_STARTED and event.step_id:
            snapshot.status = "running"
            snapshot.step_statuses[event.step_id] = "running"
            return

        if event.event_type == WorkflowEventType.STEP_COMPLETED and event.step_id:
            snapshot.step_statuses[event.step_id] = "success"
            return

        if event.event_type == WorkflowEventType.STEP_SKIPPED and event.step_id:
            snapshot.step_statuses[event.step_id] = "skipped"
            return

        if event.event_type == WorkflowEventType.STEP_RETRYING and event.step_id:
            snapshot.step_statuses[event.step_id] = "retrying"
            snapshot.error = event.data.get("error")
            return

        if event.event_type == WorkflowEventType.STEP_FAILED and event.step_id:
            snapshot.step_statuses[event.step_id] = "failed"
            snapshot.error = event.data.get("error")
            return

        if event.event_type == WorkflowEventType.WORKFLOW_COMPLETED:
            snapshot.status = str(event.data.get("status", "success"))
            snapshot.duration_ms = _coerce_float(event.data.get("duration_ms"))
            snapshot.error = None
            snapshot.terminal = True
            return

        if event.event_type == WorkflowEventType.WORKFLOW_FAILED:
            snapshot.status = str(event.data.get("status", "failed"))
            snapshot.duration_ms = _coerce_float(event.data.get("duration_ms"))
            snapshot.error = event.data.get("error")
            snapshot.terminal = True

    def _remove_ws_unlocked(self, ws: Any) -> None:
        run_ids = list(self._reverse.pop(ws, set()))
        for run_id in run_ids:
            subs = self._subscriptions.get(run_id)
            if subs is not None:
                subs.discard(ws)
                if not subs:
                    del self._subscriptions[run_id]


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
