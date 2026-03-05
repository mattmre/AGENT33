"""Bridge between MCP server and AGENT-33 services."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.agents.registry import AgentRegistry
    from agent33.llm.router import ModelRouter
    from agent33.memory.rag import RAGPipeline
    from agent33.skills.registry import SkillRegistry
    from agent33.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class MCPServiceBridge:
    """Wires MCP tool handlers to live AGENT-33 services."""

    def __init__(
        self,
        agent_registry: AgentRegistry | None = None,
        tool_registry: ToolRegistry | None = None,
        model_router: ModelRouter | None = None,
        rag_pipeline: RAGPipeline | None = None,
        skill_registry: SkillRegistry | None = None,
    ) -> None:
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.model_router = model_router
        self.rag_pipeline = rag_pipeline
        self.skill_registry = skill_registry

    def get_system_status(self) -> dict[str, Any]:
        """Return system status summary."""
        return {
            "status": "operational",
            "agents_loaded": (len(self.agent_registry.list_all()) if self.agent_registry else 0),
            "tools_loaded": (len(self.tool_registry.list_all()) if self.tool_registry else 0),
            "skills_loaded": (len(self.skill_registry.list_all()) if self.skill_registry else 0),
            "model_router_ready": self.model_router is not None,
            "rag_pipeline_ready": self.rag_pipeline is not None,
        }
