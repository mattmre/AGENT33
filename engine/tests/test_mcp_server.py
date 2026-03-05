"""Tests for Phase 43: MCP Server."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch


class TestMCPServiceBridge:
    def test_creation_with_no_services(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge

        bridge = MCPServiceBridge()
        assert bridge.agent_registry is None
        assert bridge.tool_registry is None

    def test_creation_with_services(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge

        registry = MagicMock()
        bridge = MCPServiceBridge(agent_registry=registry)
        assert bridge.agent_registry is registry

    def test_system_status_no_services(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge

        bridge = MCPServiceBridge()
        status = bridge.get_system_status()
        assert status["status"] == "operational"
        assert status["agents_loaded"] == 0
        assert status["tools_loaded"] == 0
        assert not status["model_router_ready"]

    def test_system_status_with_services(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge

        agent_reg = MagicMock()
        agent_reg.list_all.return_value = [MagicMock(), MagicMock()]
        tool_reg = MagicMock()
        tool_reg.list_all.return_value = [MagicMock()]
        skill_reg = MagicMock()
        skill_reg.list_all.return_value = []
        router = MagicMock()

        bridge = MCPServiceBridge(
            agent_registry=agent_reg,
            tool_registry=tool_reg,
            skill_registry=skill_reg,
            model_router=router,
        )
        status = bridge.get_system_status()
        assert status["agents_loaded"] == 2
        assert status["tools_loaded"] == 1
        assert status["model_router_ready"]


class TestToolHandlers:
    async def test_list_agents_empty(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_list_agents

        bridge = MCPServiceBridge()
        result = await handle_list_agents(bridge)
        assert result == []

    async def test_list_agents_with_registry(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_list_agents

        agent = MagicMock()
        agent.name = "test-agent"
        agent.description = "A test"
        agent.capabilities = ["code"]
        registry = MagicMock()
        registry.list_all.return_value = [agent]
        bridge = MCPServiceBridge(agent_registry=registry)
        result = await handle_list_agents(bridge)
        assert len(result) == 1
        assert result[0]["name"] == "test-agent"

    async def test_invoke_agent_no_registry(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_invoke_agent

        bridge = MCPServiceBridge()
        result = await handle_invoke_agent(bridge, "test", "hello")
        assert "error" in result

    async def test_invoke_agent_not_found(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_invoke_agent

        registry = MagicMock()
        registry.get.return_value = None
        router = MagicMock()
        bridge = MCPServiceBridge(agent_registry=registry, model_router=router)
        result = await handle_invoke_agent(bridge, "missing", "hello")
        assert "not found" in result["error"]

    async def test_invoke_agent_success(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_invoke_agent

        agent = MagicMock()
        agent.prompts.system = "You are helpful"
        registry = MagicMock()
        registry.get.return_value = agent

        response = MagicMock()
        response.content = "Hello back!"
        response.model = "test-model"
        response.prompt_tokens = 10
        response.completion_tokens = 5
        router = MagicMock()
        router.complete = AsyncMock(return_value=response)

        bridge = MCPServiceBridge(agent_registry=registry, model_router=router)
        result = await handle_invoke_agent(bridge, "test", "hello")
        assert result["output"] == "Hello back!"
        assert result["tokens_used"] == 15

    async def test_search_memory_no_pipeline(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_search_memory

        bridge = MCPServiceBridge()
        result = await handle_search_memory(bridge, "test query")
        assert result[0]["error"]

    async def test_list_tools_empty(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_list_tools

        bridge = MCPServiceBridge()
        result = await handle_list_tools(bridge)
        assert result == []

    async def test_list_tools_with_registry(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_list_tools

        tool = MagicMock()
        tool.name = "shell"
        tool.description = "Run shell commands"
        registry = MagicMock()
        registry.list_all.return_value = [tool]
        bridge = MCPServiceBridge(tool_registry=registry)
        result = await handle_list_tools(bridge)
        assert len(result) == 1
        assert result[0]["name"] == "shell"

    async def test_execute_tool_no_registry(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_execute_tool

        bridge = MCPServiceBridge()
        result = await handle_execute_tool(bridge, "shell")
        assert "error" in result

    async def test_execute_tool_not_found(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_execute_tool

        registry = MagicMock()
        registry.get.return_value = None
        bridge = MCPServiceBridge(tool_registry=registry)
        result = await handle_execute_tool(bridge, "missing")
        assert "not found" in result["error"]

    async def test_list_skills_empty(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_list_skills

        bridge = MCPServiceBridge()
        result = await handle_list_skills(bridge)
        assert result == []

    async def test_get_system_status(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.tools import handle_get_system_status

        bridge = MCPServiceBridge()
        result = await handle_get_system_status(bridge)
        assert result["status"] == "operational"


class TestMCPServerCreation:
    def test_create_server_without_sdk(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.server import create_mcp_server

        bridge = MCPServiceBridge()
        with patch("agent33.mcp_server.server._HAS_MCP", False):
            server = create_mcp_server(bridge)
            assert server is None

    def test_server_module_exists(self) -> None:
        from agent33.mcp_server import server

        assert hasattr(server, "create_mcp_server")


class TestMCPRoutes:
    def test_set_mcp_services(self) -> None:
        from agent33.api.routes.mcp import set_mcp_services

        bridge = MagicMock()
        server = MagicMock()
        set_mcp_services(bridge, server)

    def test_mcp_status_route_exists(self) -> None:
        from agent33.api.routes.mcp import router

        routes = [r.path for r in router.routes]  # type: ignore[union-attr]
        assert any("/status" in str(r) for r in routes)
