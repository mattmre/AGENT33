"""Thin MCP auth helpers backed by the shared permissions system."""

from __future__ import annotations

from typing import Any

from agent33.security.permissions import check_permission

TOOL_SCOPES: dict[str, str] = {
    "list_agents": "agents:read",
    "invoke_agent": "agents:invoke",
    "search_memory": "agents:read",
    "list_tools": "agents:read",
    "execute_tool": "tools:execute",
    "list_skills": "agents:read",
    "get_system_status": "agents:read",
}

RESOURCE_SCOPES: dict[str, str] = {
    "agent33://agent-registry": "agents:read",
    "agent33://tool-catalog": "agents:read",
    "agent33://policy-pack": "component-security:read",
    "agent33://schema-index": "agents:read",
    "agent33://agents/": "agents:read",
    "agent33://tools/": "agents:read",
    "agent33://workflows/": "workflows:read",
}


def get_server_request(server: Any) -> Any:
    """Return the active request from the MCP server context, if present."""
    try:
        request_context = getattr(server, "request_context", None)
    except LookupError:
        return None

    try:
        return getattr(request_context, "request", None)
    except LookupError:
        return None


def get_authenticated_scopes(server: Any) -> list[str]:
    """Return authenticated scopes from the active MCP request context."""
    request = get_server_request(server)
    user = getattr(getattr(request, "state", None), "user", None)
    if user is None:
        return []
    return list(getattr(user, "scopes", []))


def get_required_scope_for_tool(tool_name: str) -> str | None:
    """Return the scope required to invoke an MCP tool."""
    return TOOL_SCOPES.get(tool_name)


def get_required_scope_for_resource(uri: str) -> str | None:
    """Return the scope required to read an MCP resource."""
    exact_scope = RESOURCE_SCOPES.get(uri)
    if exact_scope is not None:
        return exact_scope

    for prefix, scope in RESOURCE_SCOPES.items():
        if prefix.endswith("/") and uri.startswith(prefix):
            return scope

    return None


def enforce_tool_scope(server: Any, tool_name: str) -> None:
    """Raise when the current request lacks scope for an MCP tool."""
    required_scope = get_required_scope_for_tool(tool_name)
    if required_scope is None:
        return
    _enforce_scope(server, required_scope)


def enforce_resource_scope(server: Any, uri: str) -> None:
    """Raise when the current request lacks scope for an MCP resource."""
    required_scope = get_required_scope_for_resource(uri)
    if required_scope is None:
        return
    _enforce_scope(server, required_scope)


def _enforce_scope(server: Any, required_scope: str) -> None:
    request = get_server_request(server)
    user = getattr(getattr(request, "state", None), "user", None)
    if user is None:
        raise PermissionError("MCP request is not authenticated")

    if not check_permission(required_scope, list(getattr(user, "scopes", []))):
        raise PermissionError(f"Missing required scope: {required_scope}")
