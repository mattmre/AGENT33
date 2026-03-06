"""MCP (Model Context Protocol) server endpoints."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException, Request
from starlette.responses import StreamingResponse

from agent33.security.permissions import require_scope

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
async def mcp_sse(request: Request) -> StreamingResponse:
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

        async def sse_stream() -> AsyncGenerator[str, None]:
            async with transport.connect_sse(
                request.scope,
                request.receive,
                request._send,  # type: ignore[attr-defined]
            ) as (read_stream, write_stream):
                await _mcp_server.run(
                    read_stream,
                    write_stream,
                    _mcp_server.create_initialization_options(),
                )

        return StreamingResponse(
            sse_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )
    except ImportError:
        raise HTTPException(501, "MCP SDK not installed") from None
    except Exception as exc:
        logger.error("MCP SSE error: %s", exc)
        raise HTTPException(500, f"MCP SSE error: {exc}") from exc


@router.post("/messages", dependencies=[require_scope("agents:invoke")])
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
            request._send,  # type: ignore[attr-defined]
            body,
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
