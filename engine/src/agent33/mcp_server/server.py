"""MCP server setup — tool and resource registration."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.mcp_server.bridge import MCPServiceBridge

logger = logging.getLogger(__name__)

_HAS_MCP = False
_HAS_MCP_RESOURCES = False
try:
    from mcp.server import Server
    from mcp.types import TextContent, Tool

    _HAS_MCP = True
except ImportError:
    pass

# Resource / ResourceTemplate were added in later mcp releases; guard.
try:
    from mcp.types import Resource, ResourceTemplate  # type: ignore[attr-defined]

    _HAS_MCP_RESOURCES = True
except ImportError:
    pass


def create_mcp_server(bridge: MCPServiceBridge) -> Any:
    """Create and configure the MCP server with tool handlers.

    Returns the MCP Server instance, or ``None`` if mcp SDK not installed.
    """
    if not _HAS_MCP:
        logger.warning("MCP SDK not installed, MCP server disabled")
        return None

    server = Server("agent33-core")

    @server.list_tools()  # type: ignore[misc]
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_agents",
                description="List all registered agents",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="invoke_agent",
                description="Invoke an agent with a message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent_name": {
                            "type": "string",
                            "description": "Name of the agent",
                        },
                        "message": {
                            "type": "string",
                            "description": "Message to send",
                        },
                        "model": {
                            "type": "string",
                            "description": "Model override (optional)",
                        },
                    },
                    "required": ["agent_name", "message"],
                },
            ),
            Tool(
                name="search_memory",
                description="Search the memory/knowledge base",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="list_tools",
                description="List registered tools",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="execute_tool",
                description="Execute a registered tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string",
                            "description": "Tool name",
                        },
                        "arguments": {
                            "type": "object",
                            "description": "Tool arguments",
                        },
                    },
                    "required": ["tool_name"],
                },
            ),
            Tool(
                name="list_skills",
                description="List registered skills",
                inputSchema={"type": "object", "properties": {}},
            ),
            Tool(
                name="get_system_status",
                description="Get AGENT-33 system status",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()  # type: ignore[misc]
    async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> list[TextContent]:
        from agent33.mcp_server import tools as mcp_tools

        args = arguments or {}
        result: Any

        if name == "list_agents":
            result = await mcp_tools.handle_list_agents(bridge)
        elif name == "invoke_agent":
            result = await mcp_tools.handle_invoke_agent(
                bridge,
                agent_name=args.get("agent_name", ""),
                message=args.get("message", ""),
                model=args.get("model"),
            )
        elif name == "search_memory":
            result = await mcp_tools.handle_search_memory(
                bridge,
                query=args.get("query", ""),
                top_k=args.get("top_k", 5),
            )
        elif name == "list_tools":
            result = await mcp_tools.handle_list_tools(bridge)
        elif name == "execute_tool":
            result = await mcp_tools.handle_execute_tool(
                bridge,
                tool_name=args.get("tool_name", ""),
                arguments=args.get("arguments"),
            )
        elif name == "list_skills":
            result = await mcp_tools.handle_list_skills(bridge)
        elif name == "get_system_status":
            result = await mcp_tools.handle_get_system_status(bridge)
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, default=str))]

    # -- Resource handlers -------------------------------------------------
    _register_resource_handlers(server, bridge)

    return server


def _register_resource_handlers(server: Any, bridge: MCPServiceBridge) -> None:
    """Register MCP resource list / read / template handlers.

    Gracefully degrades when the installed ``mcp`` SDK does not expose
    ``Resource`` / ``ResourceTemplate`` types (older releases).
    """
    from agent33.mcp_server.resources import (
        handle_list_resource_templates,
        handle_list_resources,
        handle_read_resource,
    )

    if _HAS_MCP_RESOURCES:

        @server.list_resources()  # type: ignore[misc]
        async def list_resources() -> list[Resource]:  # type: ignore[name-defined]
            raw = await handle_list_resources(bridge)
            return [
                Resource(
                    uri=r["uri"],
                    name=r["name"],
                    description=r.get("description", ""),
                    mimeType=r.get("mimeType", "application/json"),
                )
                for r in raw
            ]

        @server.list_resource_templates()  # type: ignore[misc]
        async def list_resource_templates() -> list[ResourceTemplate]:  # type: ignore[name-defined]  # noqa: E501
            raw = await handle_list_resource_templates(bridge)
            return [
                ResourceTemplate(
                    uriTemplate=t["uriTemplate"],
                    name=t["name"],
                    description=t.get("description", ""),
                    mimeType=t.get("mimeType", "application/json"),
                )
                for t in raw
            ]

        @server.read_resource()  # type: ignore[misc]
        async def read_resource(uri: Any) -> str:
            return await handle_read_resource(bridge, str(uri))

    else:
        logger.info(
            "MCP Resource/ResourceTemplate types not available; "
            "resource handlers skipped"
        )
