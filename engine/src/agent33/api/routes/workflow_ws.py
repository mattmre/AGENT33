"""WebSocket endpoint for real-time workflow status streaming."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from agent33.workflows.ws_manager import WorkflowWSManager

logger = structlog.get_logger()

router = APIRouter(tags=["workflows"])


@router.websocket("/v1/workflows/ws")
async def workflow_ws(websocket: WebSocket) -> None:
    """WebSocket endpoint for subscribing to workflow execution events.

    Authentication is performed via a ``token`` query parameter because
    browser WebSocket APIs cannot set custom headers.

    After the connection is accepted the client sends JSON messages:

    * ``{"action": "subscribe", "workflow_id": "..."}``
    * ``{"action": "unsubscribe", "workflow_id": "..."}``
    * ``{"action": "ping"}``

    The server pushes events as JSON and responds to pings with
    ``{"type": "pong"}``.
    """
    # -- Auth: validate JWT from query param before accepting ---------------
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    try:
        from agent33.security.auth import verify_token
        from agent33.security.permissions import check_permission

        payload = verify_token(token)
        if not check_permission("workflows:read", payload.scopes):
            await websocket.close(
                code=4003,
                reason="Missing required scope: workflows:read",
            )
            return
    except Exception:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    # -- Resolve the WSManager from app state ------------------------------
    manager: WorkflowWSManager | None = getattr(websocket.app.state, "ws_manager", None)
    if manager is None:
        await websocket.close(code=4002, reason="WebSocket manager not available")
        return

    await websocket.accept()
    logger.debug("ws_workflow_connected")

    try:
        while True:
            raw = await websocket.receive_text()
            await _handle_client_message(websocket, manager, raw)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("ws_workflow_error", exc_info=True)
    finally:
        await manager.disconnect(websocket)
        logger.debug("ws_workflow_disconnected")


async def _handle_client_message(
    ws: WebSocket,
    manager: WorkflowWSManager,
    raw: str,
) -> None:
    """Parse and dispatch a single client JSON message."""
    try:
        msg: dict[str, Any] = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        await ws.send_json({"type": "error", "message": "Invalid JSON"})
        return

    action = msg.get("action")

    if action == "ping":
        await ws.send_json({"type": "pong"})
        return

    if action == "subscribe":
        workflow_id = msg.get("workflow_id")
        if not workflow_id or not isinstance(workflow_id, str):
            await ws.send_json({"type": "error", "message": "Missing workflow_id"})
            return
        await manager.subscribe(ws, workflow_id)
        await ws.send_json({"type": "subscribed", "workflow_id": workflow_id})
        return

    if action == "unsubscribe":
        workflow_id = msg.get("workflow_id")
        if not workflow_id or not isinstance(workflow_id, str):
            await ws.send_json({"type": "error", "message": "Missing workflow_id"})
            return
        await manager.unsubscribe(ws, workflow_id)
        await ws.send_json({"type": "unsubscribed", "workflow_id": workflow_id})
        return

    await ws.send_json({"type": "error", "message": f"Unknown action: {action}"})
