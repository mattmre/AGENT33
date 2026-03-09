"""MCP resource handlers for AGENT-33 registries.

Exposes agent, tool, skill, and status registries as read-only MCP resources.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.agents.registry import AgentRegistry
    from agent33.mcp_server.bridge import MCPServiceBridge
    from agent33.skills.registry import SkillRegistry
    from agent33.tools.registry import ToolRegistry

_HAS_MCP = False
try:
    from mcp.types import Resource, ResourceTemplate

    _HAS_MCP = True
except ImportError:
    pass

# Static resources (known at startup)
STATIC_RESOURCES: list[dict[str, str]] = [
    {
        "uri": "agent33://agents",
        "name": "Agent Registry",
        "description": "List of all registered agents",
        "mimeType": "application/json",
    },
    {
        "uri": "agent33://tools",
        "name": "Tool Registry",
        "description": "List of all registered tools",
        "mimeType": "application/json",
    },
    {
        "uri": "agent33://skills",
        "name": "Skill Registry",
        "description": "List of all registered skills",
        "mimeType": "application/json",
    },
    {
        "uri": "agent33://status",
        "name": "System Status",
        "description": "Current system status summary",
        "mimeType": "application/json",
    },
]

RESOURCE_TEMPLATES: list[dict[str, str]] = [
    {
        "uriTemplate": "agent33://agents/{name}",
        "name": "Agent Definition",
        "description": "Details of a specific agent",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "agent33://tools/{name}",
        "name": "Tool Details",
        "description": "Details of a specific tool",
        "mimeType": "application/json",
    },
    {
        "uriTemplate": "agent33://skills/{name}",
        "name": "Skill Details",
        "description": "Details of a specific skill",
        "mimeType": "application/json",
    },
]


async def handle_list_resources(
    bridge: MCPServiceBridge,  # noqa: ARG001
) -> list[dict[str, str]]:
    """Return list of available static resources."""
    return STATIC_RESOURCES


async def handle_list_resource_templates(
    bridge: MCPServiceBridge,  # noqa: ARG001
) -> list[dict[str, str]]:
    """Return list of resource URI templates."""
    return RESOURCE_TEMPLATES


async def handle_read_resource(bridge: MCPServiceBridge, uri: str) -> str:
    """Read a resource by URI. Returns JSON string."""
    if uri == "agent33://agents":
        return _read_agents_list(bridge)

    if uri == "agent33://tools":
        return _read_tools_list(bridge)

    if uri == "agent33://skills":
        return _read_skills_list(bridge)

    if uri == "agent33://status":
        return _read_status(bridge)

    # Handle parameterised templates: agent33://agents/{name}, etc.
    if uri.startswith("agent33://agents/"):
        name = uri.split("/", 3)[-1]
        return _read_agent_detail(bridge, name)

    if uri.startswith("agent33://tools/"):
        name = uri.split("/", 3)[-1]
        return _read_tool_detail(bridge, name)

    if uri.startswith("agent33://skills/"):
        name = uri.split("/", 3)[-1]
        return _read_skill_detail(bridge, name)

    return json.dumps({"error": f"Unknown resource URI: {uri}"})


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _read_agents_list(bridge: MCPServiceBridge) -> str:
    if not bridge.agent_registry:
        return json.dumps({"error": "Agent registry not available"})
    agents = bridge.agent_registry.list_all()
    return json.dumps(
        [
            {
                "name": a.name,
                "description": getattr(a, "description", ""),
                "capabilities": [
                    c.value if hasattr(c, "value") else str(c)
                    for c in getattr(a, "capabilities", []) or []
                ],
            }
            for a in agents
        ],
        indent=2,
    )


def _read_tools_list(bridge: MCPServiceBridge) -> str:
    if not bridge.tool_registry:
        return json.dumps({"error": "Tool registry not available"})
    tools = bridge.tool_registry.list_all()
    return json.dumps(
        [
            {
                "name": t.name if hasattr(t, "name") else str(t),
                "description": getattr(t, "description", ""),
            }
            for t in tools
        ],
        indent=2,
    )


def _read_skills_list(bridge: MCPServiceBridge) -> str:
    if not bridge.skill_registry:
        return json.dumps({"error": "Skill registry not available"})
    skills = bridge.skill_registry.list_all()
    return json.dumps(
        [
            {
                "name": s.name,
                "description": getattr(s, "description", ""),
                "tags": list(getattr(s, "tags", []) or []),
            }
            for s in skills
        ],
        indent=2,
    )


def _read_status(bridge: MCPServiceBridge) -> str:
    status: dict[str, Any] = bridge.get_system_status()
    return json.dumps(status, indent=2)


def _read_agent_detail(bridge: MCPServiceBridge, name: str) -> str:
    if not bridge.agent_registry:
        return json.dumps({"error": "Agent registry not available"})
    defn = bridge.agent_registry.get(name)
    if not defn:
        return json.dumps({"error": f"Agent '{name}' not found"})
    return json.dumps(defn.model_dump(mode="json"), indent=2, default=str)


def _read_tool_detail(bridge: MCPServiceBridge, name: str) -> str:
    if not bridge.tool_registry:
        return json.dumps({"error": "Tool registry not available"})
    tool = bridge.tool_registry.get(name)
    if not tool:
        return json.dumps({"error": f"Tool '{name}' not found"})
    return json.dumps(
        {
            "name": tool.name if hasattr(tool, "name") else str(tool),
            "description": getattr(tool, "description", ""),
        },
        indent=2,
    )


def _read_skill_detail(bridge: MCPServiceBridge, name: str) -> str:
    if not bridge.skill_registry:
        return json.dumps({"error": "Skill registry not available"})
    skill = bridge.skill_registry.get(name)
    if not skill:
        return json.dumps({"error": f"Skill '{name}' not found"})
    return json.dumps(skill.model_dump(mode="json"), indent=2, default=str)


# ---------------------------------------------------------------------------
# MCP server integration — register handlers on a live Server instance
# ---------------------------------------------------------------------------


def register_resources(
    server: Any,
    agent_registry: AgentRegistry | None,
    tool_registry: ToolRegistry | None = None,
    skill_registry: SkillRegistry | None = None,
) -> None:
    """Register 4 static resources and 3 resource templates on *server*.

    No-op when the MCP SDK is not installed (``_HAS_MCP`` is False).
    """
    if not _HAS_MCP:
        return

    from agent33.mcp_server.bridge import MCPServiceBridge

    bridge = MCPServiceBridge(
        agent_registry=agent_registry,
        tool_registry=tool_registry,
        skill_registry=skill_registry,
    )

    async def list_resources() -> list[Resource]:
        return [
            Resource(
                uri=r["uri"],
                name=r["name"],
                description=r.get("description", ""),
                mimeType=r.get("mimeType", "application/json"),
            )
            for r in STATIC_RESOURCES
        ]

    server.list_resources()(list_resources)

    async def read_resource(uri: Any) -> str:
        return await handle_read_resource(bridge, str(uri))

    server.read_resource()(read_resource)

    async def list_resource_templates() -> list[ResourceTemplate]:
        return [
            ResourceTemplate(
                uriTemplate=t["uriTemplate"],
                name=t["name"],
                description=t.get("description", ""),
                mimeType=t.get("mimeType", "application/json"),
            )
            for t in RESOURCE_TEMPLATES
        ]

    server.list_resource_templates()(list_resource_templates)
