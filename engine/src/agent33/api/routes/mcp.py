"""MCP (Model Context Protocol) server endpoints."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status
from starlette.responses import StreamingResponse

from agent33.security.permissions import require_scope

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/mcp", tags=["mcp-server"])


def require_authenticated_user(request: Request) -> Any:
    """Ensure the current request is authenticated."""
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return user


@router.get("/sse", dependencies=[Depends(require_authenticated_user)])
async def mcp_sse(request: Request) -> StreamingResponse:
    """SSE endpoint for MCP protocol."""
    mcp_server = getattr(request.app.state, "mcp_server", None)
    transport = getattr(request.app.state, "mcp_transport", None)

    if mcp_server is None or transport is None:
        async def stub_stream() -> AsyncGenerator[str, None]:
            yield "event: endpoint\ndata: /v1/mcp/messages\n\n"
            yield "event: status\ndata: MCP transport unavailable\n\n"

        return StreamingResponse(
            stub_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    try:
        async def sse_stream() -> AsyncGenerator[str, None]:
            async with transport.connect_sse(
                request.scope,
                request.receive,
                request._send,
            ) as (read_stream, write_stream):
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )

        return StreamingResponse(
            sse_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    except Exception as exc:
        logger.error("MCP SSE error: %s", exc)
        raise HTTPException(500, f"MCP SSE error: {exc}") from exc


@router.post("/messages", dependencies=[Depends(require_authenticated_user)])
async def mcp_messages(request: Request) -> dict[str, Any]:
    """Handle MCP protocol messages."""
    transport = getattr(request.app.state, "mcp_transport", None)
    if transport is None:
        return {"status": "accepted", "note": "MCP transport not initialized"}

    try:
        body = await request.body()
        await transport.handle_post_message(
            request.scope,
            request.receive,
            request._send,
            body,
        )
        return {"status": "processed"}
    except Exception as exc:
        logger.error("MCP message error: %s", exc)
        return {"status": "error", "detail": str(exc)}


@router.get("/status", dependencies=[require_scope("agents:read")])
async def mcp_status(request: Request) -> dict[str, Any]:
    """MCP server status."""
    bridge = getattr(request.app.state, "mcp_bridge", None)
    mcp_server = getattr(request.app.state, "mcp_server", None)

    if bridge is None:
        return {
            "available": False,
            "mcp_sdk_installed": mcp_server is not None,
        }

    return {
        "available": mcp_server is not None,
        "mcp_sdk_installed": mcp_server is not None,
        **bridge.get_system_status(),
    }
