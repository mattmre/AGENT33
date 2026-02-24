"""Phase 32 kickoff tests: connector middleware, governance, and circuit breaker."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from agent33.connectors.circuit_breaker import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
)
from agent33.connectors.executor import ConnectorExecutor
from agent33.connectors.governance import BlocklistConnectorPolicy
from agent33.connectors.middleware import (
    CircuitBreakerMiddleware,
    GovernanceMiddleware,
)
from agent33.connectors.models import ConnectorRequest
from agent33.tools.mcp_bridge import MCPServerConnection


class _Response:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


class _NeverCalledClient:
    async def post(self, url: str, json: dict[str, Any]) -> _Response:  # noqa: ARG002
        raise AssertionError("HTTP client should not be called when governance denies")

    async def aclose(self) -> None:
        return None


class _FailingClient:
    def __init__(self) -> None:
        self.calls = 0

    async def post(self, url: str, json: dict[str, Any]) -> _Response:  # noqa: ARG002
        self.calls += 1
        raise httpx.ConnectError("connect failed")

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_connector_executor_middleware_ordering() -> None:
    events: list[str] = []

    class FirstMiddleware:
        async def __call__(self, request: ConnectorRequest, call_next):
            events.append(f"first-before:{request.operation}")
            result = await call_next(request)
            events.append("first-after")
            return result

    class SecondMiddleware:
        async def __call__(self, request: ConnectorRequest, call_next):
            events.append(f"second-before:{request.operation}")
            result = await call_next(request)
            events.append("second-after")
            return result

    executor = ConnectorExecutor([FirstMiddleware(), SecondMiddleware()])
    request = ConnectorRequest(connector="mcp:test", operation="tools/list")

    async def handler(req: ConnectorRequest) -> dict[str, str]:
        events.append(f"handler:{req.operation}")
        return {"ok": "yes"}

    result = await executor.execute(request, handler)

    assert result == {"ok": "yes"}
    assert events == [
        "first-before:tools/list",
        "second-before:tools/list",
        "handler:tools/list",
        "second-after",
        "first-after",
    ]


def test_circuit_breaker_transitions_closed_open_half_open_closed() -> None:
    now = 100.0

    def _clock() -> float:
        return now

    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout_seconds=10.0,
        half_open_success_threshold=1,
        clock=_clock,
    )

    breaker.before_call()
    breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED

    breaker.before_call()
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN

    with pytest.raises(CircuitOpenError):
        breaker.before_call()

    now = 111.0
    breaker.before_call()
    assert breaker.state == CircuitState.HALF_OPEN
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_mcp_connection_boundary_governance_blocks_operation() -> None:
    executor = ConnectorExecutor(
        [
            GovernanceMiddleware(
                BlocklistConnectorPolicy(blocked_operations=frozenset({"tools/call"}))
            )
        ]
    )
    conn = MCPServerConnection(
        name="phase32",
        url="https://example.com/mcp",
        boundary_executor=executor,
    )
    conn._client = _NeverCalledClient()  # type: ignore[assignment]

    with pytest.raises(PermissionError, match="operation blocked by policy"):
        await conn.call_tool("search", {"q": "agent33"})


@pytest.mark.asyncio
async def test_mcp_connection_boundary_circuit_breaker_opens_after_failure() -> None:
    breaker = CircuitBreaker(
        failure_threshold=1,
        recovery_timeout_seconds=60.0,
        half_open_success_threshold=1,
    )
    executor = ConnectorExecutor(
        [CircuitBreakerMiddleware(breaker)]
    )
    conn = MCPServerConnection(
        name="phase32",
        url="https://example.com/mcp",
        boundary_executor=executor,
    )
    failing_client = _FailingClient()
    conn._client = failing_client  # type: ignore[assignment]

    with pytest.raises(httpx.ConnectError):
        await conn.list_tools()

    with pytest.raises(CircuitOpenError):
        await conn.list_tools()

    assert failing_client.calls == 1
