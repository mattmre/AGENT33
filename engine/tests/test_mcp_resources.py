"""Tests for Phase 43 Stage 2: MCP Resources & Auth."""

from __future__ import annotations

import json
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bridge(**kwargs):  # type: ignore[no-untyped-def]
    from agent33.mcp_server.bridge import MCPServiceBridge

    return MCPServiceBridge(**kwargs)


def _mock_agent(name: str = "agent-a", description: str = "desc") -> MagicMock:
    agent = MagicMock()
    agent.name = name
    agent.description = description
    cap = MagicMock()
    cap.value = "code"
    agent.capabilities = [cap]
    agent.model_dump.return_value = {
        "name": name,
        "description": description,
    }
    return agent


def _mock_tool(name: str = "tool-a", description: str = "a tool") -> MagicMock:
    tool = MagicMock()
    tool.name = name
    tool.description = description
    return tool


def _mock_skill(
    name: str = "skill-a",
    description: str = "a skill",
    tags: set[str] | None = None,
) -> MagicMock:
    skill = MagicMock()
    skill.name = name
    skill.description = description
    skill.tags = tags or {"general"}
    skill.model_dump.return_value = {
        "name": name,
        "description": description,
        "tags": list(skill.tags),
    }
    return skill


# ===================================================================
# TestMCPResources
# ===================================================================


class TestMCPResourceLists:
    """Tests for handle_list_resources and handle_list_resource_templates."""

    async def test_list_resources_returns_static_list(self) -> None:
        from agent33.mcp_server.resources import handle_list_resources

        bridge = _make_bridge()
        result = await handle_list_resources(bridge)
        assert isinstance(result, list)
        assert len(result) == 4
        uris = {r["uri"] for r in result}
        assert "agent33://agents" in uris
        assert "agent33://tools" in uris
        assert "agent33://skills" in uris
        assert "agent33://status" in uris

    async def test_list_resources_entries_have_required_keys(self) -> None:
        from agent33.mcp_server.resources import handle_list_resources

        bridge = _make_bridge()
        result = await handle_list_resources(bridge)
        for entry in result:
            assert "uri" in entry
            assert "name" in entry
            assert "mimeType" in entry

    async def test_list_resource_templates(self) -> None:
        from agent33.mcp_server.resources import handle_list_resource_templates

        bridge = _make_bridge()
        result = await handle_list_resource_templates(bridge)
        assert isinstance(result, list)
        assert len(result) == 3
        uri_templates = {t["uriTemplate"] for t in result}
        assert "agent33://agents/{name}" in uri_templates
        assert "agent33://tools/{name}" in uri_templates
        assert "agent33://skills/{name}" in uri_templates

    async def test_list_resource_templates_have_required_keys(self) -> None:
        from agent33.mcp_server.resources import handle_list_resource_templates

        bridge = _make_bridge()
        result = await handle_list_resource_templates(bridge)
        for entry in result:
            assert "uriTemplate" in entry
            assert "name" in entry


class TestMCPResourceRead:
    """Tests for handle_read_resource with various URIs."""

    async def test_read_agents_resource(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        reg = MagicMock()
        reg.list_all.return_value = [_mock_agent("alpha"), _mock_agent("beta")]
        bridge = _make_bridge(agent_registry=reg)

        raw = await handle_read_resource(bridge, "agent33://agents")
        data = json.loads(raw)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "alpha"

    async def test_read_agents_registry_unavailable(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        bridge = _make_bridge()
        raw = await handle_read_resource(bridge, "agent33://agents")
        data = json.loads(raw)
        assert "error" in data

    async def test_read_tools_resource(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        reg = MagicMock()
        reg.list_all.return_value = [_mock_tool("shell")]
        bridge = _make_bridge(tool_registry=reg)

        raw = await handle_read_resource(bridge, "agent33://tools")
        data = json.loads(raw)
        assert isinstance(data, list)
        assert data[0]["name"] == "shell"

    async def test_read_tools_registry_unavailable(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        bridge = _make_bridge()
        raw = await handle_read_resource(bridge, "agent33://tools")
        data = json.loads(raw)
        assert "error" in data

    async def test_read_skills_resource(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        reg = MagicMock()
        reg.list_all.return_value = [_mock_skill("summarize")]
        bridge = _make_bridge(skill_registry=reg)

        raw = await handle_read_resource(bridge, "agent33://skills")
        data = json.loads(raw)
        assert isinstance(data, list)
        assert data[0]["name"] == "summarize"

    async def test_read_skills_registry_unavailable(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        bridge = _make_bridge()
        raw = await handle_read_resource(bridge, "agent33://skills")
        data = json.loads(raw)
        assert "error" in data

    async def test_read_status_resource(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        bridge = _make_bridge()
        raw = await handle_read_resource(bridge, "agent33://status")
        data = json.loads(raw)
        assert data["status"] == "operational"

    async def test_read_agent_by_name(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        agent = _mock_agent("my-agent")
        reg = MagicMock()
        reg.get.return_value = agent
        bridge = _make_bridge(agent_registry=reg)

        raw = await handle_read_resource(bridge, "agent33://agents/my-agent")
        data = json.loads(raw)
        assert data["name"] == "my-agent"
        reg.get.assert_called_once_with("my-agent")

    async def test_read_agent_not_found(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        reg = MagicMock()
        reg.get.return_value = None
        bridge = _make_bridge(agent_registry=reg)

        raw = await handle_read_resource(bridge, "agent33://agents/missing")
        data = json.loads(raw)
        assert "not found" in data["error"]

    async def test_read_tool_by_name(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        tool = _mock_tool("shell")
        reg = MagicMock()
        reg.get.return_value = tool
        bridge = _make_bridge(tool_registry=reg)

        raw = await handle_read_resource(bridge, "agent33://tools/shell")
        data = json.loads(raw)
        assert data["name"] == "shell"

    async def test_read_tool_not_found(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        reg = MagicMock()
        reg.get.return_value = None
        bridge = _make_bridge(tool_registry=reg)

        raw = await handle_read_resource(bridge, "agent33://tools/nope")
        data = json.loads(raw)
        assert "not found" in data["error"]

    async def test_read_skill_by_name(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        skill = _mock_skill("summarize")
        reg = MagicMock()
        reg.get.return_value = skill
        bridge = _make_bridge(skill_registry=reg)

        raw = await handle_read_resource(bridge, "agent33://skills/summarize")
        data = json.loads(raw)
        assert data["name"] == "summarize"

    async def test_read_skill_not_found(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        reg = MagicMock()
        reg.get.return_value = None
        bridge = _make_bridge(skill_registry=reg)

        raw = await handle_read_resource(bridge, "agent33://skills/nope")
        data = json.loads(raw)
        assert "not found" in data["error"]

    async def test_read_unknown_uri(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        bridge = _make_bridge()
        raw = await handle_read_resource(bridge, "agent33://unknown/path")
        data = json.loads(raw)
        assert "Unknown resource URI" in data["error"]

    async def test_read_agent_detail_registry_unavailable(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        bridge = _make_bridge()
        raw = await handle_read_resource(bridge, "agent33://agents/foo")
        data = json.loads(raw)
        assert "error" in data

    async def test_read_tool_detail_registry_unavailable(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        bridge = _make_bridge()
        raw = await handle_read_resource(bridge, "agent33://tools/foo")
        data = json.loads(raw)
        assert "error" in data

    async def test_read_skill_detail_registry_unavailable(self) -> None:
        from agent33.mcp_server.resources import handle_read_resource

        bridge = _make_bridge()
        raw = await handle_read_resource(bridge, "agent33://skills/foo")
        data = json.loads(raw)
        assert "error" in data


# ===================================================================
# TestMCPAuth
# ===================================================================


class TestMCPAuthToolScope:
    """Tests for check_tool_scope."""

    def test_admin_always_passes(self) -> None:
        from agent33.mcp_server.auth import check_tool_scope

        assert check_tool_scope("invoke_agent", ["admin"]) is True

    def test_matching_scope(self) -> None:
        from agent33.mcp_server.auth import check_tool_scope

        assert check_tool_scope("list_agents", ["agents:read"]) is True

    def test_invoke_requires_invoke_scope(self) -> None:
        from agent33.mcp_server.auth import check_tool_scope

        assert check_tool_scope("invoke_agent", ["agents:invoke"]) is True
        assert check_tool_scope("invoke_agent", ["agents:read"]) is False

    def test_execute_tool_requires_tools_execute(self) -> None:
        from agent33.mcp_server.auth import check_tool_scope

        assert check_tool_scope("execute_tool", ["tools:execute"]) is True
        assert check_tool_scope("execute_tool", ["agents:read"]) is False

    def test_denied_when_no_matching_scope(self) -> None:
        from agent33.mcp_server.auth import check_tool_scope

        assert check_tool_scope("list_agents", ["tools:execute"]) is False

    def test_unknown_tool_allowed_by_default(self) -> None:
        from agent33.mcp_server.auth import check_tool_scope

        assert check_tool_scope("totally_new_tool", []) is True

    def test_multiple_scopes_one_matches(self) -> None:
        from agent33.mcp_server.auth import check_tool_scope

        assert check_tool_scope(
            "list_agents", ["tools:execute", "agents:read"]
        ) is True

    def test_empty_scopes_denied(self) -> None:
        from agent33.mcp_server.auth import check_tool_scope

        assert check_tool_scope("list_agents", []) is False


class TestMCPAuthResourceScope:
    """Tests for check_resource_scope."""

    def test_admin_always_passes(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope("agent33://agents", ["admin"]) is True

    def test_matching_scope(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope(
            "agent33://agents", ["agents:read"]
        ) is True

    def test_denied_when_no_matching_scope(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope(
            "agent33://agents", ["tools:execute"]
        ) is False

    def test_prefix_match_for_parameterised_uri(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope(
            "agent33://agents/my-agent", ["agents:read"]
        ) is True

    def test_prefix_match_tools(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope(
            "agent33://tools/shell", ["agents:read"]
        ) is True

    def test_prefix_match_denied(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope(
            "agent33://agents/my-agent", ["tools:execute"]
        ) is False

    def test_unknown_agent33_uri_defaults_to_agents_read(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope(
            "agent33://something/else", ["agents:read"]
        ) is True

    def test_unknown_agent33_uri_denied(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope(
            "agent33://something/else", ["tools:execute"]
        ) is False

    def test_non_agent33_uri_allowed_by_default(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope(
            "https://example.com/resource", []
        ) is True

    def test_status_resource_scope(self) -> None:
        from agent33.mcp_server.auth import check_resource_scope

        assert check_resource_scope(
            "agent33://status", ["agents:read"]
        ) is True
        assert check_resource_scope(
            "agent33://status", ["tools:execute"]
        ) is False


# ===================================================================
# TestMCPAuthConstants
# ===================================================================


class TestMCPAuthConstants:
    """Ensure scope mappings are well-formed."""

    def test_tool_scopes_covers_all_known_tools(self) -> None:
        from agent33.mcp_server.auth import TOOL_SCOPES

        expected = {
            "list_agents",
            "invoke_agent",
            "search_memory",
            "list_tools",
            "execute_tool",
            "list_skills",
            "get_system_status",
        }
        assert set(TOOL_SCOPES.keys()) == expected

    def test_resource_scopes_covers_all_static_resources(self) -> None:
        from agent33.mcp_server.auth import RESOURCE_SCOPES
        from agent33.mcp_server.resources import STATIC_RESOURCES

        static_uris = {r["uri"] for r in STATIC_RESOURCES}
        assert static_uris == set(RESOURCE_SCOPES.keys())
