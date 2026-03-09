"""Tests for Phase 43 Stage 2: MCP resources and auth scope enforcement."""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Mock server helper — captures decorator-registered handlers
# ---------------------------------------------------------------------------


class _MockMCPServer:
    """Minimal MCP server stub that records registered handler callbacks."""

    def __init__(self) -> None:
        self._handlers: dict[str, Any] = {}

    def list_resources(self) -> Any:
        def decorator(fn: Any) -> Any:
            self._handlers["list_resources"] = fn
            return fn

        return decorator

    def read_resource(self) -> Any:
        def decorator(fn: Any) -> Any:
            self._handlers["read_resource"] = fn
            return fn

        return decorator

    def list_resource_templates(self) -> Any:
        def decorator(fn: Any) -> Any:
            self._handlers["list_resource_templates"] = fn
            return fn

        return decorator


# ---------------------------------------------------------------------------
# Domain object helpers
# ---------------------------------------------------------------------------


def _mock_agent(name: str = "agent-a", description: str = "desc") -> MagicMock:
    agent = MagicMock()
    agent.name = name
    agent.description = description
    cap = MagicMock()
    cap.value = "code"
    agent.capabilities = [cap]
    agent.model_dump.return_value = {"name": name, "description": description}
    return agent


def _mock_skill(name: str = "skill-a", description: str = "a skill") -> MagicMock:
    skill = MagicMock()
    skill.name = name
    skill.description = description
    skill.tags = {"general"}
    skill.model_dump.return_value = {"name": name, "description": description}
    return skill


# ===================================================================
# 1. register_resources() — no-op when _HAS_MCP is False
# ===================================================================


class TestRegisterResourcesNoOp:
    def test_no_op_when_mcp_not_installed(self) -> None:
        """register_resources must be a no-op when the MCP SDK is absent."""
        from agent33.mcp_server import resources as resources_mod
        from agent33.mcp_server.resources import register_resources

        server = _MockMCPServer()
        with patch.object(resources_mod, "_HAS_MCP", False):
            register_resources(server, MagicMock())

        assert "list_resources" not in server._handlers
        assert "read_resource" not in server._handlers
        assert "list_resource_templates" not in server._handlers


# ===================================================================
# 2. register_resources() inner handlers (MCP SDK present)
# ===================================================================


class TestRegisterResourcesHandlers:
    """Test the handler functions registered by register_resources()."""

    def _setup(
        self,
        agent_registry: Any = None,
        tool_registry: Any = None,
        skill_registry: Any = None,
    ) -> _MockMCPServer:
        from agent33.mcp_server.resources import register_resources

        server = _MockMCPServer()
        register_resources(server, agent_registry, tool_registry, skill_registry)
        return server

    async def test_list_resources_returns_4_entries(self) -> None:
        server = self._setup()
        result = await server._handlers["list_resources"]()
        assert len(result) == 4
        # Strip potential trailing slash added by pydantic AnyUrl normalization
        uris = {str(r.uri).rstrip("/") for r in result}
        assert "agent33://agents" in uris
        assert "agent33://tools" in uris
        assert "agent33://skills" in uris
        assert "agent33://status" in uris

    async def test_list_resource_templates_returns_3_entries(self) -> None:
        server = self._setup()
        result = await server._handlers["list_resource_templates"]()
        assert len(result) == 3
        # Use model_dump to handle camelCase/snake_case variations across SDK versions
        template_dicts = [r.model_dump() for r in result]
        all_values = {str(v) for d in template_dicts for v in d.values()}
        assert "agent33://agents/{name}" in all_values
        assert "agent33://tools/{name}" in all_values
        assert "agent33://skills/{name}" in all_values

    async def test_read_resource_agents_returns_json_list(self) -> None:
        reg = MagicMock()
        reg.list_all.return_value = [_mock_agent("alpha"), _mock_agent("beta")]
        server = self._setup(agent_registry=reg)
        raw = await server._handlers["read_resource"]("agent33://agents")
        data = json.loads(raw)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "alpha"

    async def test_read_resource_status_returns_operational(self) -> None:
        server = self._setup()
        raw = await server._handlers["read_resource"]("agent33://status")
        data = json.loads(raw)
        assert data["status"] == "operational"

    async def test_read_resource_tools_uses_tool_registry(self) -> None:
        tool = MagicMock()
        tool.name = "shell"
        tool.description = "Run shell commands"
        reg = MagicMock()
        reg.list_all.return_value = [tool]
        server = self._setup(tool_registry=reg)
        raw = await server._handlers["read_resource"]("agent33://tools")
        data = json.loads(raw)
        assert data == [{"name": "shell", "description": "Run shell commands"}]

    async def test_read_resource_skills_with_registry(self) -> None:
        reg = MagicMock()
        reg.list_all.return_value = [_mock_skill("summarize")]
        server = self._setup(skill_registry=reg)
        raw = await server._handlers["read_resource"]("agent33://skills")
        data = json.loads(raw)
        assert isinstance(data, list)
        assert data[0]["name"] == "summarize"

    async def test_read_resource_skills_no_registry_returns_error(self) -> None:
        server = self._setup()
        raw = await server._handlers["read_resource"]("agent33://skills")
        data = json.loads(raw)
        assert "error" in data

    async def test_read_resource_agent_by_name(self) -> None:
        agent = _mock_agent("my-agent")
        agent.model_dump.return_value = {"name": "my-agent", "description": "d"}
        reg = MagicMock()
        reg.get.return_value = agent
        server = self._setup(agent_registry=reg)
        raw = await server._handlers["read_resource"]("agent33://agents/my-agent")
        data = json.loads(raw)
        assert data["name"] == "my-agent"
        reg.get.assert_called_once_with("my-agent")

    async def test_read_resource_agent_not_found_raises_value_error(self) -> None:
        reg = MagicMock()
        reg.get.return_value = None
        server = self._setup(agent_registry=reg)
        raw = await server._handlers["read_resource"]("agent33://agents/missing")
        data = json.loads(raw)
        assert data["error"] == "Agent 'missing' not found"

    async def test_read_resource_unknown_uri_raises_value_error(self) -> None:
        server = self._setup()
        raw = await server._handlers["read_resource"]("agent33://unknown/path")
        data = json.loads(raw)
        assert data["error"] == "Unknown resource URI: agent33://unknown/path"


# ===================================================================
# 3. get_required_scope_for_tool
# ===================================================================


class TestGetRequiredScopeForTool:
    def test_known_tool_invoke_agent_returns_agents_invoke(self) -> None:
        from agent33.mcp_server.auth import get_required_scope_for_tool

        assert get_required_scope_for_tool("invoke_agent") == "agents:invoke"

    def test_agent_prefix_returns_agents_invoke(self) -> None:
        from agent33.mcp_server.auth import get_required_scope_for_tool

        assert get_required_scope_for_tool("agent_invoke") == "agents:invoke"

    def test_tool_prefix_returns_tools_execute(self) -> None:
        from agent33.mcp_server.auth import get_required_scope_for_tool

        assert get_required_scope_for_tool("tool_run") == "tools:execute"

    def test_unknown_tool_returns_agents_read(self) -> None:
        from agent33.mcp_server.auth import get_required_scope_for_tool

        assert get_required_scope_for_tool("list") == "agents:read"

    def test_list_agents_returns_agents_read(self) -> None:
        from agent33.mcp_server.auth import get_required_scope_for_tool

        assert get_required_scope_for_tool("list_agents") == "agents:read"

    def test_execute_tool_returns_tools_execute(self) -> None:
        from agent33.mcp_server.auth import get_required_scope_for_tool

        assert get_required_scope_for_tool("execute_tool") == "tools:execute"


# ===================================================================
# 4. require_mcp_scope
# ===================================================================


class TestRequireMCPScope:
    def test_known_scope_does_not_raise(self) -> None:
        from agent33.mcp_server.auth import require_mcp_scope

        require_mcp_scope("agents:read")
        require_mcp_scope("agents:invoke")
        require_mcp_scope("tools:execute")

    def test_unknown_scope_raises_403(self) -> None:
        from agent33.mcp_server.auth import require_mcp_scope

        with pytest.raises(HTTPException) as exc_info:
            require_mcp_scope("unknown:scope")
        assert exc_info.value.status_code == 403


# ===================================================================
# 5. MCPServiceBridge.register_resources delegates correctly
# ===================================================================


class TestBridgeRegisterResources:
    def test_register_resources_delegates_to_module_function(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge

        agent_reg = MagicMock()
        tool_reg = MagicMock()
        skill_reg = MagicMock()
        bridge = MCPServiceBridge(
            agent_registry=agent_reg,
            tool_registry=tool_reg,
            skill_registry=skill_reg,
        )
        server = _MockMCPServer()

        with patch("agent33.mcp_server.resources.register_resources") as mock_fn:
            bridge.register_resources(server)

        mock_fn.assert_called_once_with(server, agent_reg, tool_reg, skill_reg)

    def test_register_resources_wires_handlers(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge

        agent_reg = MagicMock()
        agent_reg.list_all.return_value = []
        bridge = MCPServiceBridge(agent_registry=agent_reg)
        server = _MockMCPServer()
        bridge.register_resources(server)
        assert "read_resource" in server._handlers


# ===================================================================
# 6. app.state.mcp_bridge (without running lifespan)
# ===================================================================


class TestSetMCPServices:
    def test_mcp_status_endpoint_with_module_level_services(self) -> None:
        from agent33.api.routes.mcp import set_mcp_services
        from agent33.main import app
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.security.auth import create_access_token

        bridge = MCPServiceBridge()
        set_mcp_services(bridge, None)
        token = create_access_token("test-user", scopes=["admin"])
        client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
        response = client.get("/v1/mcp/status")
        assert response.status_code == 200
        data = response.json()
        assert "available" in data or "status" in data


def _make_mcp_route_app(scopes: list[str]) -> FastAPI:
    from agent33.api.routes import mcp

    app = FastAPI()

    @app.middleware("http")
    async def _fake_auth(request: Request, call_next):
        request.state.user = SimpleNamespace(scopes=scopes, tenant_id="tenant-test")
        return await call_next(request)

    app.include_router(mcp.router)
    return app


class TestMCPMessageRouteScopes:
    def test_tools_call_requires_tool_specific_scope(self) -> None:
        client = TestClient(_make_mcp_route_app(["agents:read"]))

        response = client.post(
            "/v1/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "invoke_agent", "arguments": {"agent_name": "a"}},
            },
        )

        assert response.status_code == 403
        assert "invoke_agent" in response.json()["detail"]

    def test_tools_call_allows_matching_scope(self) -> None:
        app = _make_mcp_route_app(["agents:read", "agents:invoke"])
        app.state.mcp_transport = MagicMock()
        app.state.mcp_transport.handle_post_message = AsyncMock()
        client = TestClient(app)

        response = client.post(
            "/v1/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "invoke_agent", "arguments": {"agent_name": "a"}},
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "processed"
