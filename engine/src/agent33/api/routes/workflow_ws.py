"""WebSocket endpoint for real-time run-scoped workflow status streaming."""

from __future__ import annotations

import asyncio
import contextlib
import json
from typing import TYPE_CHECKING, Any

import structlog
from fastapi import APIRouter
from starlette.websockets import WebSocket, WebSocketDisconnect

from agent33.security.auth import validate_api_key, verify_token
from agent33.security.permissions import check_permission

if TYPE_CHECKING:
    from agent33.security.auth import TokenPayload
    from agent33.workflows.ws_manager import WorkflowWSManager

logger = structlog.get_logger()

router = APIRouter(tags=["workflows"])


@router.websocket("/v1/workflows/{run_id}/ws")
async def workflow_ws(websocket: WebSocket, run_id: str) -> None:
    """Stream run-scoped workflow events for a single execution."""
    payload = await _authenticate_websocket(websocket)
    if payload is None:
        return

    manager: WorkflowWSManager | None = getattr(websocket.app.state, "ws_manager", None)
    if manager is None:
        await websocket.close(code=4002, reason="WebSocket manager not available")
        return

    if not await manager.has_run(run_id):
        await websocket.close(code=4004, reason="Unknown run_id")
        return

    await websocket.accept()

    connected = await manager.connect(websocket, run_id)
    if not connected:
        await websocket.close(code=4004, reason="Unknown run_id")
        return

    try:
        if not await manager.send_sync(websocket, run_id):
            await websocket.close(code=4004, reason="Unknown run_id")
            return
    except Exception:
        await manager.disconnect(websocket)
        return

    heartbeat_task = asyncio.create_task(_heartbeat_loop(websocket, manager, run_id))
    logger.debug("ws_workflow_connected", run_id=run_id, subject=payload.sub)

    try:
        while True:
            raw = await websocket.receive_text()
            await _handle_client_message(websocket, manager, run_id, raw)
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.debug("ws_workflow_error", run_id=run_id, exc_info=True)
    finally:
        heartbeat_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await heartbeat_task
        await manager.disconnect(websocket)
        logger.debug("ws_workflow_disconnected", run_id=run_id)


async def _authenticate_websocket(websocket: WebSocket) -> TokenPayload | None:
    """Authenticate the WebSocket request using query-string credentials."""
    token = websocket.query_params.get("token")
    api_key = websocket.query_params.get("api_key")

    payload = None
    if token:
        try:
            payload = verify_token(token)
        except Exception:
            payload = None
    elif api_key:
        payload = validate_api_key(api_key)

    if payload is None:
        await websocket.close(code=4001, reason="Invalid or missing credentials")
        return None

    if not check_permission("workflows:read", payload.scopes):
        await websocket.close(code=4003, reason="Missing required scope")
        return None

    return payload


async def _handle_client_message(
    websocket: WebSocket,
    manager: WorkflowWSManager,
    run_id: str,
    raw: str,
) -> None:
    """Parse and dispatch a single client JSON message."""
    try:
        msg: dict[str, Any] = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        await websocket.send_json({"type": "error", "message": "Invalid JSON"})
        return

    action = msg.get("action")

    if action == "ping":
        await websocket.send_json({"type": "pong", "run_id": run_id})
        return

    if action == "sync":
        await manager.send_sync(websocket, run_id)
        return

    await websocket.send_json({"type": "error", "message": f"Unknown action: {action}"})


async def _heartbeat_loop(
    websocket: WebSocket,
    manager: WorkflowWSManager,
    run_id: str,
) -> None:
    """Send periodic keepalive events while the socket remains connected."""
    try:
        while True:
            await asyncio.sleep(manager.heartbeat_interval_seconds)
            await manager.send_heartbeat(websocket, run_id)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.debug("ws_workflow_heartbeat_stopped", run_id=run_id, exc_info=True)
