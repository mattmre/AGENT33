"""MCP (Model Context Protocol) server endpoints."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import Response, StreamingResponse

from agent33.mcp_server.auth import check_resource_scope, check_tool_scope
from agent33.security.permissions import _get_token_payload, require_scope

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/mcp", tags=["mcp-server"])

# Module-level service references, wired during lifespan.
_bridge: Any = None
_mcp_server: Any = None


def set_mcp_services(bridge: Any, server: Any) -> None:
    """Wire MCP services from lifespan."""
    global _bridge, _mcp_server  # noqa: PLW0603
    _bridge = bridge
    _mcp_server = server


@router.get("/sse", dependencies=[require_scope("agents:read")])
async def mcp_sse(request: Request) -> Response:
    """SSE endpoint for MCP protocol.

    When the MCP SDK is available and configured, this provides
    the SSE transport. Otherwise returns a stub stream.
    """
    if _mcp_server is None:
        # Stub: emit endpoint info and close
        async def stub_stream() -> AsyncGenerator[str, None]:
            yield "event: endpoint\ndata: /v1/mcp/messages\n\n"
            yield "event: status\ndata: MCP SDK not installed\n\n"

        return StreamingResponse(
            stub_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # Real SSE transport (when MCP SDK is available)
    try:
        from mcp.server.sse import SseServerTransport

        transport = SseServerTransport("/v1/mcp/messages")
        # Store transport for message endpoint
        request.app.state.mcp_transport = transport

        async def handle_sse() -> Response:
            async with transport.connect_sse(
                request.scope,
                request.receive,
                request._send,
            ) as (read_stream, write_stream):
                await _mcp_server.run(
                    read_stream,
                    write_stream,
                    _mcp_server.create_initialization_options(),
                )
            return Response()

        return await handle_sse()
    except ImportError:
        raise HTTPException(501, "MCP SDK not installed") from None
    except Exception as exc:
        logger.error("MCP SSE error: %s", exc)
        raise HTTPException(500, f"MCP SSE error: {exc}") from exc


def _iter_mcp_messages(payload: Any) -> list[dict[str, Any]]:
    """Normalize a JSON-RPC payload into a list of message objects."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _enforce_message_scope(request: Request, body: bytes) -> None:
    """Apply scope checks for MCP JSON-RPC messages before transport handling."""
    payload = _get_token_payload(request)

    try:
        message_payload = json.loads(body.decode("utf-8")) if body else {}
    except (UnicodeDecodeError, json.JSONDecodeError):
        return

    for message in _iter_mcp_messages(message_payload):
        method = str(message.get("method", ""))
        params = message.get("params", {})
        if not isinstance(params, dict):
            params = {}

        if method == "tools/call":
            tool_name = str(params.get("name", ""))
            if not check_tool_scope(tool_name, payload.scopes):
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing required scope for MCP tool: {tool_name}",
                )
            continue

        if method == "resources/read":
            uri = str(params.get("uri", ""))
            if not check_resource_scope(uri, payload.scopes):
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing required scope for MCP resource: {uri}",
                )


@router.post("/messages", dependencies=[require_scope("agents:read")])
async def mcp_messages(request: Request) -> dict[str, Any]:
    """Handle MCP protocol messages."""
    body = await request.body()
    _enforce_message_scope(request, body)

    transport = getattr(request.app.state, "mcp_transport", None)
    if transport is None:
        return {"status": "accepted", "note": "MCP transport not initialized"}

    receive_state = {"sent": False}

    async def replay_receive() -> dict[str, Any]:
        if not receive_state["sent"]:
            receive_state["sent"] = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    try:
        await transport.handle_post_message(
            request.scope,
            replay_receive,
            request._send,
        )
        return {"status": "processed"}
    except Exception as exc:
        logger.error("MCP message error: %s", exc)
        return {"status": "error", "detail": str(exc)}


@router.get("/status")
async def mcp_status() -> dict[str, Any]:
    """MCP server status."""
    if _bridge is None:
        return {
            "available": False,
            "mcp_sdk_installed": _mcp_server is not None,
        }
    return {
        "available": True,
        "mcp_sdk_installed": _mcp_server is not None,
        **_bridge.get_system_status(),
    }
