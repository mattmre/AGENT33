"""WebSocket connection manager for workflow event streaming."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from starlette.websockets import WebSocket

    from agent33.workflows.events import WorkflowEvent

logger = structlog.get_logger()


class WorkflowWSManager:
    """Manages WebSocket subscriptions for workflow status events.

    Thread-safe via an ``asyncio.Lock``.  Clients subscribe to individual
    workflow IDs and receive events broadcast for those workflows.

    Dead connections are detected and cleaned up automatically on broadcast.
    """

    def __init__(self) -> None:
        self._subscriptions: dict[str, set[Any]] = {}
        self._reverse: dict[Any, set[str]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, ws: WebSocket, workflow_id: str) -> None:
        """Subscribe *ws* to events for *workflow_id*."""
        async with self._lock:
            if workflow_id not in self._subscriptions:
                self._subscriptions[workflow_id] = set()
            self._subscriptions[workflow_id].add(ws)

            if ws not in self._reverse:
                self._reverse[ws] = set()
            self._reverse[ws].add(workflow_id)

        logger.debug(
            "ws_subscribed",
            workflow_id=workflow_id,
            active_subs=len(self._subscriptions.get(workflow_id, set())),
        )

    async def unsubscribe(self, ws: WebSocket, workflow_id: str) -> None:
        """Remove *ws* from *workflow_id* subscription."""
        async with self._lock:
            self._unsubscribe_unlocked(ws, workflow_id)

    async def disconnect(self, ws: WebSocket) -> None:
        """Remove *ws* from all subscriptions (e.g. on close)."""
        async with self._lock:
            workflow_ids = list(self._reverse.pop(ws, set()))
            for wid in workflow_ids:
                subs = self._subscriptions.get(wid)
                if subs is not None:
                    subs.discard(ws)
                    if not subs:
                        del self._subscriptions[wid]

        if workflow_ids:
            logger.debug("ws_disconnected", removed_subscriptions=len(workflow_ids))

    async def broadcast(self, workflow_id: str, event: WorkflowEvent) -> None:
        """Send *event* to every WebSocket subscribed to *workflow_id*.

        Dead connections are silently removed.
        """
        async with self._lock:
            subs = self._subscriptions.get(workflow_id)
            if not subs:
                return
            targets = list(subs)

        payload = event.to_json()
        results = await asyncio.gather(
            *(ws.send_text(payload) for ws in targets),
            return_exceptions=True,
        )
        dead = [
            ws
            for ws, result in zip(targets, results, strict=False)
            if isinstance(result, Exception)
        ]

        if dead:
            async with self._lock:
                for ws in dead:
                    self._remove_ws_unlocked(ws)
            logger.debug("ws_dead_connections_cleaned", count=len(dead))

    # -- Introspection helpers (useful for tests) --------------------------

    async def active_subscriptions(self, workflow_id: str) -> int:
        """Return the number of active subscribers for *workflow_id*."""
        async with self._lock:
            return len(self._subscriptions.get(workflow_id, set()))

    async def connected_count(self) -> int:
        """Return the total number of tracked WebSocket connections."""
        async with self._lock:
            return len(self._reverse)

    # -- Internal ----------------------------------------------------------

    def _unsubscribe_unlocked(self, ws: Any, workflow_id: str) -> None:
        subs = self._subscriptions.get(workflow_id)
        if subs is not None:
            subs.discard(ws)
            if not subs:
                del self._subscriptions[workflow_id]
        rev = self._reverse.get(ws)
        if rev is not None:
            rev.discard(workflow_id)
            if not rev:
                del self._reverse[ws]

    def _remove_ws_unlocked(self, ws: Any) -> None:
        workflow_ids = list(self._reverse.pop(ws, set()))
        for wid in workflow_ids:
            subs = self._subscriptions.get(wid)
            if subs is not None:
                subs.discard(ws)
                if not subs:
                    del self._subscriptions[wid]
