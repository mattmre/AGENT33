"""MCP tool handler implementations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.mcp_server.bridge import MCPServiceBridge

logger = logging.getLogger(__name__)


async def handle_list_agents(
    bridge: MCPServiceBridge,
) -> list[dict[str, Any]]:
    """List all registered agents."""
    if not bridge.agent_registry:
        return []
    agents = bridge.agent_registry.list_all()
    return [
        {
            "name": a.name,
            "description": getattr(a, "description", ""),
            "capabilities": [str(c) for c in getattr(a, "capabilities", [])],
        }
        for a in agents
    ]


async def handle_invoke_agent(
    bridge: MCPServiceBridge,
    agent_name: str,
    message: str,
    model: str | None = None,
) -> dict[str, Any]:
    """Invoke an agent with a message."""
    if not bridge.agent_registry or not bridge.model_router:
        return {"error": "Agent registry or model router not available"}

    defn = bridge.agent_registry.get(agent_name)
    if defn is None:
        return {"error": f"Agent '{agent_name}' not found"}

    from agent33.llm.base import ChatMessage

    system_prompt = getattr(getattr(defn, "prompts", None), "system", "") or ""
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=message),
    ]

    try:
        response = await bridge.model_router.complete(
            messages,
            model=model or "default",
        )
        return {
            "output": response.content or "",
            "model": response.model,
            "tokens_used": response.prompt_tokens + response.completion_tokens,
        }
    except Exception as exc:
        return {"error": str(exc)}


async def handle_search_memory(
    bridge: MCPServiceBridge,
    query: str,
    top_k: int = 5,  # noqa: ARG001
) -> list[dict[str, Any]]:
    """Search memory via RAG pipeline.

    Note: ``top_k`` is accepted for protocol completeness but the
    underlying ``RAGPipeline.query`` uses its constructor-configured value.
    """
    if not bridge.rag_pipeline:
        return [{"error": "RAG pipeline not available"}]

    try:
        result = await bridge.rag_pipeline.query(query)
        return [
            {
                "content": source.text,
                "score": source.score,
                "source": source.metadata.get("source", ""),
            }
            for source in result.sources
        ]
    except Exception as exc:
        return [{"error": str(exc)}]


async def handle_list_tools(
    bridge: MCPServiceBridge,
) -> list[dict[str, Any]]:
    """List registered tools."""
    if not bridge.tool_registry:
        return []
    tools = bridge.tool_registry.list_all()
    return [
        {
            "name": t.name if hasattr(t, "name") else str(t),
            "description": getattr(t, "description", ""),
        }
        for t in tools
    ]


async def handle_discover_tools(
    bridge: MCPServiceBridge,
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    """Discover relevant runtime tools."""
    discovery_service = getattr(bridge, "discovery_service", None)
    if discovery_service is None:
        return {"query": query, "matches": [], "error": "Discovery service not available"}

    matches = discovery_service.discover_tools(query, limit=limit)
    return {
        "query": query,
        "matches": [match.model_dump(mode="json") for match in matches],
    }


async def handle_execute_tool(
    bridge: MCPServiceBridge,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    context: Any | None = None,
) -> dict[str, Any]:
    """Execute a registered tool."""
    if not bridge.tool_registry:
        return {"error": "Tool registry not available"}

    tool = bridge.tool_registry.get(tool_name)
    if tool is None:
        return {"error": f"Tool '{tool_name}' not found"}

    try:
        from agent33.tools.base import ToolContext

        tool_context = context if isinstance(context, ToolContext) else ToolContext()
        result = await tool.execute(arguments or {}, tool_context)
        return {
            "tool": tool_name,
            "output": result.output or "",
            "success": result.success,
        }
    except Exception as exc:
        return {"error": str(exc)}


async def handle_list_skills(
    bridge: MCPServiceBridge,
) -> list[dict[str, Any]]:
    """List registered skills."""
    if not bridge.skill_registry:
        return []
    skills = bridge.skill_registry.list_all()
    return [
        {
            "name": s.name,
            "description": getattr(s, "description", ""),
            "tags": list(getattr(s, "tags", [])),
        }
        for s in skills
    ]


async def handle_discover_skills(
    bridge: MCPServiceBridge,
    query: str,
    limit: int = 10,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Discover relevant skills."""
    discovery_service = getattr(bridge, "discovery_service", None)
    if discovery_service is None:
        return {"query": query, "matches": [], "error": "Discovery service not available"}

    matches = discovery_service.discover_skills(query, limit=limit, tenant_id=tenant_id)
    return {
        "query": query,
        "matches": [match.model_dump(mode="json") for match in matches],
    }


async def handle_resolve_workflow(
    bridge: MCPServiceBridge,
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    """Resolve workflows and canonical templates for a task."""
    discovery_service = getattr(bridge, "discovery_service", None)
    if discovery_service is None:
        return {"query": query, "matches": [], "error": "Discovery service not available"}

    matches = discovery_service.resolve_workflow(query, limit=limit)
    return {
        "query": query,
        "matches": [match.model_dump(mode="json") for match in matches],
    }


async def handle_get_system_status(
    bridge: MCPServiceBridge,
) -> dict[str, Any]:
    """Get system status."""
    return bridge.get_system_status()
