"""Integration tests for application wiring (Phase 2).

Verifies that the FastAPI app starts/stops cleanly, middleware is applied,
and the lifespan initialises all expected connections (using mocks where
external services are unavailable).
"""

from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


def _make_mock_ltm():
    """Create a mock LongTermMemory instance."""
    m = MagicMock()
    m.initialize = AsyncMock()
    m.close = AsyncMock()
    return m


def _make_mock_nats_bus():
    """Create a mock NATSMessageBus instance."""
    m = MagicMock()
    m.connect = AsyncMock()
    m.close = AsyncMock()
    m.is_connected = False
    return m


def _make_mock_redis_module():
    """Create a mock redis.asyncio module with a mock client."""
    client = MagicMock()
    client.ping = AsyncMock(return_value=True)
    client.aclose = AsyncMock()
    mod = MagicMock()
    mod.from_url = MagicMock(return_value=client)
    return mod


@pytest.fixture
def patched_app():
    """Yield (app, TestClient) with all external I/O mocked."""
    from agent33.main import app

    mock_ltm = _make_mock_ltm()
    mock_nats = _make_mock_nats_bus()
    mock_redis_mod = _make_mock_redis_module()

    with (
        patch("agent33.main.LongTermMemory", return_value=mock_ltm),
        patch("agent33.main.NATSMessageBus", return_value=mock_nats),
        patch.dict(sys.modules, {"redis": MagicMock(), "redis.asyncio": mock_redis_mod}),
        TestClient(app, raise_server_exceptions=False) as client,
    ):
        yield app, client, mock_ltm


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAppStartupShutdown:
    """Verify the app starts and stops without errors."""

    def test_app_starts_and_stops_cleanly(self, patched_app):
        """The app lifespan should complete startup and shutdown without raising.

        We verify startup occurred by checking that the DB mock was called and
        that app.state was populated (startup side-effects).
        """
        app, _client, mock_ltm = patched_app
        # If we get here, the lifespan started successfully
        mock_ltm.initialize.assert_awaited_once()
        assert hasattr(app.state, "long_term_memory")


class TestSecurityMiddleware:
    """Verify the AuthMiddleware is wired into the app."""

    def test_middleware_is_registered(self, patched_app):
        """The AuthMiddleware class should be present in the middleware stack."""
        from agent33.security.middleware import AuthMiddleware

        app, _, _ = patched_app
        middleware_classes = [
            getattr(m, "cls", None) for m in app.user_middleware
        ]
        assert AuthMiddleware in middleware_classes

    def test_unauthenticated_request_returns_401(self, patched_app):
        """Non-public endpoints should require authentication."""
        _app, client, _ = patched_app
        resp = client.get("/agents/")
        assert resp.status_code == 401

    def test_cors_middleware_is_registered(self, patched_app):
        """CORSMiddleware should be present in the middleware stack."""
        from starlette.middleware.cors import CORSMiddleware

        app, _, _ = patched_app
        middleware_classes = [
            getattr(m, "cls", None) for m in app.user_middleware
        ]
        assert CORSMiddleware in middleware_classes


class TestLifespanState:
    """Verify that lifespan populates app.state with expected attributes."""

    def test_state_has_long_term_memory(self, patched_app):
        app, _, _ = patched_app
        assert hasattr(app.state, "long_term_memory")

    def test_state_has_nats_bus(self, patched_app):
        app, _, _ = patched_app
        assert hasattr(app.state, "nats_bus")

    def test_state_has_model_router(self, patched_app):
        app, _, _ = patched_app
        assert hasattr(app.state, "model_router")

    def test_state_has_redis(self, patched_app):
        app, _, _ = patched_app
        assert hasattr(app.state, "redis")


class TestAgentWorkflowBridge:
    """Verify the agent runtime bridge is registered in invoke_agent registry."""

    def test_default_agent_registered(self, patched_app):
        from agent33.workflows.actions.invoke_agent import get_agent

        _app, _, _ = patched_app
        handler = get_agent("__default__")
        assert callable(handler)
