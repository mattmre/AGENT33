"""MCP auth enforcement for tool and resource operations.

Provides per-operation scope checking so that callers must hold the right
permission before invoking MCP tools or reading MCP resources.
"""

from __future__ import annotations

import structlog
from fastapi import HTTPException, status

logger = structlog.get_logger()

# Required scope per MCP tool name
TOOL_SCOPES: dict[str, str] = {
    "list_agents": "agents:read",
    "invoke_agent": "agents:invoke",
    "search_memory": "agents:read",
    "list_tools": "agents:read",
    "execute_tool": "tools:execute",
    "list_skills": "agents:read",
    "get_system_status": "agents:read",
}

# Required scope per static resource URI
RESOURCE_SCOPES: dict[str, str] = {
    "agent33://agents": "agents:read",
    "agent33://tools": "agents:read",
    "agent33://skills": "agents:read",
    "agent33://status": "agents:read",
}

# Known MCP scope names for validation
SCOPE_REQUIREMENTS: dict[str, str] = {
    "agents:read": "agents:read",
    "tools:execute": "tools:execute",
    "agents:invoke": "agents:invoke",
}


def check_tool_scope(tool_name: str, user_scopes: list[str]) -> bool:
    """Check whether *user_scopes* satisfy the requirement for *tool_name*.

    ``admin`` always passes.  Unknown tools fall back to the default
    requirement returned by :func:`get_required_scope_for_tool`.
    """
    if "admin" in user_scopes:
        return True
    required = get_required_scope_for_tool(tool_name)
    return required in user_scopes


def check_resource_scope(uri: str, user_scopes: list[str]) -> bool:
    """Check whether *user_scopes* satisfy the requirement for *uri*.

    ``admin`` always passes.  Prefix matching covers parameterised
    template URIs (e.g. ``agent33://agents/my-agent``).
    """
    if "admin" in user_scopes:
        return True

    # Exact match
    required = RESOURCE_SCOPES.get(uri)
    if required:
        return required in user_scopes

    # Prefix matching for parameterised templates
    for pattern, scope in RESOURCE_SCOPES.items():
        if uri.startswith(pattern + "/"):
            return scope in user_scopes

    # Any agent33:// URI defaults to agents:read
    if uri.startswith("agent33://"):
        return "agents:read" in user_scopes

    return True


def require_mcp_scope(scope: str) -> None:
    """Raise HTTPException 403 if *scope* is not a known MCP scope name.

    In production this would inspect JWT claims.  Currently validates that the
    requested scope name is recognised.
    """
    if scope not in SCOPE_REQUIREMENTS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unknown MCP scope: {scope}",
        )


def get_required_scope_for_tool(tool_name: str) -> str:
    """Return the required scope string for a given MCP tool name."""
    if tool_name in TOOL_SCOPES:
        return TOOL_SCOPES[tool_name]
    if tool_name.startswith("agent_"):
        return "agents:invoke"
    if tool_name.startswith("tool_"):
        return "tools:execute"
    return "agents:read"
