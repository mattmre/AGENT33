"""Tests for MCP route wiring and server integration."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent33.api.routes.mcp import router
from agent33.security.auth import create_access_token
from agent33.security.middleware import AuthMiddleware


def _make_headers(*scopes: str) -> dict[str, str]:
    token = create_access_token("test-user", scopes=list(scopes))
    return {"Authorization": f"Bearer {token}"}


def _build_route_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware)
    app.include_router(router)
    app.state.mcp_bridge = MagicMock()
    app.state.mcp_bridge.get_system_status.return_value = {
        "status": "operational",
        "agents_loaded": 1,
    }
    app.state.mcp_server = None
    app.state.mcp_transport = None
    return app


class _FakeSseContext:
    async def __aenter__(self) -> tuple[str, str]:
        return ("read-stream", "write-stream")

    async def __aexit__(self, exc_type, exc, tb) -> bool:  # type: ignore[no-untyped-def]
        return False


class _FakeTransport:
    def __init__(self) -> None:
        self.connect_calls: list[tuple[object, object, object]] = []
        self.message_calls: list[tuple[object, object, object, bytes]] = []

    def connect_sse(self, scope, receive, send):  # type: ignore[no-untyped-def]
        self.connect_calls.append((scope, receive, send))
        return _FakeSseContext()

    async def handle_post_message(self, scope, receive, send, body):  # type: ignore[no-untyped-def]
        self.message_calls.append((scope, receive, send, body))


class _FakeMCPServer:
    def __init__(self) -> None:
        self.run = AsyncMock()

    def create_initialization_options(self) -> dict[str, str]:
        return {"mode": "test"}


class _RecordingServer:
    def __init__(self, request: object | None = None) -> None:
        self.request_context = SimpleNamespace(request=request)
        self.handlers: dict[str, object] = {}

    def list_tools(self):
        def decorator(fn):
            self.handlers["list_tools"] = fn
            return fn

        return decorator

    def call_tool(self):
        def decorator(fn):
            self.handlers["call_tool"] = fn
            return fn

        return decorator

    def list_resources(self):
        def decorator(fn):
            self.handlers["list_resources"] = fn
            return fn

        return decorator

    def list_resource_templates(self):
        def decorator(fn):
            self.handlers["list_resource_templates"] = fn
            return fn

        return decorator

    def read_resource(self):
        def decorator(fn):
            self.handlers["read_resource"] = fn
            return fn

        return decorator


class _ToolDescriptor(SimpleNamespace):
    pass


class _TextContent(SimpleNamespace):
    pass


class TestMCPRoutes:
    def test_sse_and_messages_require_authentication(self) -> None:
        app = _build_route_app()
        client = TestClient(app)

        assert client.get("/v1/mcp/sse").status_code == 401
        assert client.post("/v1/mcp/messages", content=b"{}").status_code == 401

    def test_status_requires_agents_read_scope(self) -> None:
        app = _build_route_app()
        client = TestClient(app)

        forbidden = client.get("/v1/mcp/status", headers=_make_headers("workflows:read"))
        assert forbidden.status_code == 403

        allowed = client.get("/v1/mcp/status", headers=_make_headers("agents:read"))
        assert allowed.status_code == 200
        assert allowed.json()["status"] == "operational"

    def test_routes_reuse_persistent_transport(self) -> None:
        app = _build_route_app()
        transport = _FakeTransport()
        server = _FakeMCPServer()
        app.state.mcp_transport = transport
        app.state.mcp_server = server

        with TestClient(app) as client:
            with client.stream(
                "GET", "/v1/mcp/sse", headers=_make_headers("agents:read")
            ) as sse_response:
                assert sse_response.status_code == 200
                sse_response.read()

            message_response = client.post(
                "/v1/mcp/messages",
                content=b'{"jsonrpc":"2.0"}',
                headers=_make_headers("agents:read"),
            )
            assert message_response.status_code == 200
            assert message_response.json() == {"status": "processed"}

        assert app.state.mcp_transport is transport
        assert len(transport.connect_calls) == 1
        assert len(transport.message_calls) == 1
        server.run.assert_awaited_once()


class TestMCPServiceBridge:
    def test_creation_with_workflow_registry(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge

        workflow_registry = {"release": MagicMock()}
        bridge = MCPServiceBridge(workflow_registry=workflow_registry)

        assert bridge.workflow_registry is workflow_registry
        assert bridge.get_workflow("release") is workflow_registry["release"]

    def test_system_status_counts_workflows(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge

        bridge = MCPServiceBridge(workflow_registry={"one": MagicMock(), "two": MagicMock()})
        status = bridge.get_system_status()

        assert status["status"] == "operational"
        assert status["workflows_loaded"] == 2


class TestMCPServerCreation:
    def test_create_server_without_sdk(self) -> None:
        from agent33.mcp_server.bridge import MCPServiceBridge
        from agent33.mcp_server.server import create_mcp_server

        bridge = MCPServiceBridge()
        with patch("agent33.mcp_server.server._HAS_MCP", False):
            server = create_mcp_server(bridge)
            assert server is None

    async def test_execute_tool_uses_request_context_for_auth_and_tool_context(self) -> None:
        from agent33.mcp_server.server import create_mcp_server
        from agent33.security.auth import TokenPayload

        request = SimpleNamespace(
            state=SimpleNamespace(
                user=TokenPayload(sub="tool-user", scopes=["tools:execute"], tenant_id="tenant-1")
            )
        )
        fake_server = _RecordingServer(request=request)

        with (
            patch("agent33.mcp_server.server._HAS_MCP", True),
            patch("agent33.mcp_server.server.Server", return_value=fake_server, create=True),
            patch(
                "agent33.mcp_server.server.Tool",
                side_effect=lambda **kwargs: _ToolDescriptor(**kwargs),
                create=True,
            ),
            patch(
                "agent33.mcp_server.server.TextContent",
                side_effect=lambda **kwargs: _TextContent(**kwargs),
                create=True,
            ),
            patch("agent33.mcp_server.server.register_resources"),
            patch(
                "agent33.mcp_server.tools.handle_execute_tool", new_callable=AsyncMock
            ) as exec_tool,
        ):
            exec_tool.return_value = {"success": True}
            create_mcp_server(MagicMock(spec=object))
            await fake_server.handlers["call_tool"](
                "execute_tool",
                {"tool_name": "shell", "arguments": {"command": "echo hi"}},
            )

        kwargs = exec_tool.await_args.kwargs
        context = kwargs["context"]
        assert kwargs["tool_name"] == "shell"
        assert context.user_scopes == ["tools:execute"]
        assert context.requested_by == "tool-user"
        assert context.tenant_id == "tenant-1"

    async def test_tool_call_rejects_missing_scope(self) -> None:
        from agent33.mcp_server.server import create_mcp_server
        from agent33.security.auth import TokenPayload

        request = SimpleNamespace(
            state=SimpleNamespace(user=TokenPayload(sub="reader", scopes=["agents:read"]))
        )
        fake_server = _RecordingServer(request=request)

        with (
            patch("agent33.mcp_server.server._HAS_MCP", True),
            patch("agent33.mcp_server.server.Server", return_value=fake_server, create=True),
            patch(
                "agent33.mcp_server.server.Tool",
                side_effect=lambda **kwargs: _ToolDescriptor(**kwargs),
                create=True,
            ),
            patch(
                "agent33.mcp_server.server.TextContent",
                side_effect=lambda **kwargs: _TextContent(**kwargs),
                create=True,
            ),
            patch("agent33.mcp_server.server.register_resources"),
        ):
            create_mcp_server(MagicMock(spec=object))

        try:
            await fake_server.handlers["call_tool"]("execute_tool", {"tool_name": "shell"})
        except PermissionError as exc:
            assert "tools:execute" in str(exc)
        else:
            raise AssertionError("expected PermissionError")
