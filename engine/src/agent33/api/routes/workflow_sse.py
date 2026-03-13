"""SSE endpoint for real-time run-scoped workflow status streaming."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from agent33.security.permissions import require_scope

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from agent33.workflows.events import WorkflowEvent

router = APIRouter(prefix="/v1/workflows", tags=["workflows"])


@router.get("/{run_id}/events", dependencies=[require_scope("workflows:read")])
async def stream_workflow_events(run_id: str, request: Request) -> StreamingResponse:
    """Stream run-scoped workflow events over authenticated SSE."""
    manager = getattr(request.app.state, "ws_manager", None)
    if manager is None:
        raise HTTPException(status_code=503, detail="Workflow live manager not available")

    user = _get_request_user(request)
    queue, replay_events = await manager.subscribe_sse_with_replay_if_allowed(
        run_id,
        subject=user.sub,
        tenant_id=getattr(user, "tenant_id", ""),
        scopes=getattr(user, "scopes", []),
        is_admin="admin" in getattr(user, "scopes", []),
        after_event_id=request.headers.get("last-event-id"),
    )
    if queue is None:
        raise HTTPException(status_code=404, detail=f"Workflow run '{run_id}' not found")

    sync_event = await manager.build_sync_event(run_id)
    if sync_event is None:
        await manager.unsubscribe_sse(run_id, queue)
        raise HTTPException(status_code=404, detail=f"Workflow run '{run_id}' not found")

    async def event_generator() -> AsyncGenerator[str, None]:
        loop = asyncio.get_running_loop()
        poll_timeout = min(manager.heartbeat_interval_seconds, 1.0)
        next_heartbeat_at = loop.time() + manager.heartbeat_interval_seconds
        try:
            yield _format_sse(sync_event)
            for replay_event in replay_events:
                yield _format_sse(replay_event)
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=poll_timeout,
                    )
                    next_heartbeat_at = loop.time() + manager.heartbeat_interval_seconds
                except TimeoutError:
                    if loop.time() < next_heartbeat_at:
                        continue
                    heartbeat = await manager.build_heartbeat_event(run_id)
                    if heartbeat is None:
                        break
                    yield _format_sse(heartbeat)
                    next_heartbeat_at = loop.time() + manager.heartbeat_interval_seconds
                    continue
                yield _format_sse(event)
        finally:
            await manager.unsubscribe_sse(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _format_sse(event: WorkflowEvent) -> str:
    """Serialize a workflow event as a single SSE data frame."""
    frame_lines: list[str] = []
    if event.event_id:
        frame_lines.append(f"id: {event.event_id}")
    payload = event.to_json()
    for line in payload.splitlines() or [payload]:
        frame_lines.append(f"data: {line}")
    return "\n".join(frame_lines) + "\n\n"


def _get_request_user(request: Request) -> Any:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
