"""FastAPI router for MCP proxy server management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException

from agent33.mcp_server.proxy_models import ProxyServerConfig  # noqa: TC001 (FastAPI body)
from agent33.security.permissions import require_scope

if TYPE_CHECKING:
    from agent33.mcp_server.proxy_manager import ProxyManager

router = APIRouter(prefix="/v1/mcp/proxy", tags=["mcp-proxy"])

_proxy_manager: ProxyManager | None = None


def set_proxy_manager(manager: ProxyManager) -> None:
    """Inject the proxy manager (called from lifespan)."""
    global _proxy_manager  # noqa: PLW0603
    _proxy_manager = manager


def get_proxy_manager() -> ProxyManager | None:
    """Return the proxy manager singleton."""
    return _proxy_manager


def _require_manager() -> ProxyManager:
    if _proxy_manager is None:
        raise HTTPException(status_code=503, detail="MCP proxy manager not initialized")
    return _proxy_manager


# ---------------------------------------------------------------------------
# Server management endpoints
# ---------------------------------------------------------------------------


@router.get("/servers", dependencies=[require_scope("agents:read")])
async def list_proxy_servers() -> dict[str, Any]:
    """List all registered proxy servers with health status."""
    manager = _require_manager()
    if manager.health_check_enabled:
        await manager.refresh_health()
    servers = manager.list_servers()
    summary = manager.health_summary()
    return {
        "servers": servers,
        **summary,
    }


@router.get("/servers/{server_id}", dependencies=[require_scope("agents:read")])
async def get_proxy_server(server_id: str) -> dict[str, Any]:
    """Get details and health for a specific proxy server."""
    manager = _require_manager()
    if manager.health_check_enabled:
        await manager.refresh_health()
    handle = manager.get_server(server_id)
    if handle is None:
        raise HTTPException(status_code=404, detail=f"Proxy server '{server_id}' not found")
    return handle.status_summary()


@router.post("/servers", dependencies=[require_scope("admin")])
async def add_proxy_server(config: ProxyServerConfig) -> dict[str, Any]:
    """Register and start a new proxy server."""
    manager = _require_manager()
    try:
        handle = await manager.add_server(config)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return handle.status_summary()


@router.delete("/servers/{server_id}", dependencies=[require_scope("admin")])
async def remove_proxy_server(server_id: str) -> dict[str, Any]:
    """Stop and unregister a proxy server."""
    manager = _require_manager()
    removed = await manager.remove_server(server_id)
    if not removed:
        raise HTTPException(status_code=404, detail=f"Proxy server '{server_id}' not found")
    return {"id": server_id, "status": "removed"}


@router.post("/servers/{server_id}/restart", dependencies=[require_scope("admin")])
async def restart_proxy_server(server_id: str) -> dict[str, Any]:
    """Restart a specific proxy server."""
    manager = _require_manager()
    handle = manager.get_server(server_id)
    if handle is None:
        raise HTTPException(status_code=404, detail=f"Proxy server '{server_id}' not found")
    await handle.stop()
    await handle.start()
    return handle.status_summary()


# ---------------------------------------------------------------------------
# Tool and health endpoints
# ---------------------------------------------------------------------------


@router.get("/tools", dependencies=[require_scope("agents:read")])
async def list_proxy_tools() -> dict[str, Any]:
    """List all aggregated proxy tools."""
    manager = _require_manager()
    if manager.health_check_enabled:
        await manager.refresh_health()
    tools = manager.list_aggregated_tools()
    return {"tools": tools, "count": len(tools)}


@router.get("/health")
async def proxy_fleet_health() -> dict[str, Any]:
    """Fleet-level health summary (public)."""
    manager = _require_manager()
    if manager.health_check_enabled:
        await manager.refresh_health()
    return manager.health_summary()
