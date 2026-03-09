"""Tests for WebSocket workflow status streaming (Phase 25 Stage 3)."""

from __future__ import annotations

import asyncio
import json
from dataclasses import FrozenInstanceError
from time import perf_counter
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from agent33.workflows.events import WorkflowEvent, WorkflowEventType
from agent33.workflows.ws_manager import WorkflowWSManager

# ---------------------------------------------------------------------------
# WorkflowEvent tests
# ---------------------------------------------------------------------------


class TestWorkflowEventType:
    """Tests for the WorkflowEventType enum."""

    def test_all_event_types_defined(self) -> None:
        expected = {
            "workflow_started",
            "step_started",
            "step_completed",
            "step_failed",
            "step_skipped",
            "step_retrying",
            "workflow_completed",
            "workflow_failed",
        }
        actual = {e.value for e in WorkflowEventType}
        assert actual == expected

    def test_event_type_is_str(self) -> None:
        assert isinstance(WorkflowEventType.WORKFLOW_STARTED, str)
        assert WorkflowEventType.STEP_COMPLETED == "step_completed"


class TestWorkflowEvent:
    """Tests for WorkflowEvent dataclass."""

    def test_create_minimal_event(self) -> None:
        evt = WorkflowEvent(
            event_type=WorkflowEventType.WORKFLOW_STARTED,
            workflow_id="wf-1",
        )
        assert evt.event_type == WorkflowEventType.WORKFLOW_STARTED
        assert evt.workflow_id == "wf-1"
        assert evt.step_id is None
        assert evt.data == {}
        assert isinstance(evt.timestamp, float)

    def test_create_step_event(self) -> None:
        evt = WorkflowEvent(
            event_type=WorkflowEventType.STEP_COMPLETED,
            workflow_id="wf-2",
            step_id="step-a",
            data={"duration_ms": 42.5},
        )
        assert evt.step_id == "step-a"
        assert evt.data["duration_ms"] == 42.5

    def test_frozen(self) -> None:
        evt = WorkflowEvent(
            event_type=WorkflowEventType.WORKFLOW_STARTED,
            workflow_id="wf-1",
        )
        with pytest.raises(FrozenInstanceError):
            evt.workflow_id = "other"  # type: ignore[misc]

    def test_to_dict_minimal(self) -> None:
        ts = 1700000000.0
        evt = WorkflowEvent(
            event_type=WorkflowEventType.WORKFLOW_STARTED,
            workflow_id="wf-1",
            timestamp=ts,
        )
        d = evt.to_dict()
        assert d == {
            "type": "workflow_started",
            "workflow_id": "wf-1",
            "timestamp": ts,
        }
        # No step_id or data keys when not set
        assert "step_id" not in d
        assert "data" not in d

    def test_to_dict_with_step_and_data(self) -> None:
        evt = WorkflowEvent(
            event_type=WorkflowEventType.STEP_FAILED,
            workflow_id="wf-3",
            timestamp=1700000001.0,
            step_id="step-x",
            data={"error": "boom"},
        )
        d = evt.to_dict()
        assert d["step_id"] == "step-x"
        assert d["data"] == {"error": "boom"}
        assert d["type"] == "step_failed"

    def test_to_json(self) -> None:
        evt = WorkflowEvent(
            event_type=WorkflowEventType.WORKFLOW_COMPLETED,
            workflow_id="wf-4",
            timestamp=1700000002.0,
            data={"status": "success"},
        )
        raw = evt.to_json()
        parsed = json.loads(raw)
        assert parsed["type"] == "workflow_completed"
        assert parsed["workflow_id"] == "wf-4"
        assert parsed["data"]["status"] == "success"

    def test_to_json_round_trip(self) -> None:
        evt = WorkflowEvent(
            event_type=WorkflowEventType.STEP_RETRYING,
            workflow_id="wf-5",
            step_id="step-retry",
            timestamp=1700000003.0,
            data={"attempt": 2, "max_attempts": 3},
        )
        d = json.loads(evt.to_json())
        assert d == evt.to_dict()


# ---------------------------------------------------------------------------
# WorkflowWSManager tests
# ---------------------------------------------------------------------------


def _mock_ws(*, alive: bool = True) -> MagicMock:
    """Create a mock WebSocket object."""
    ws = MagicMock()
    if alive:
        ws.send_text = AsyncMock()
    else:
        ws.send_text = AsyncMock(side_effect=RuntimeError("connection closed"))
    return ws


class TestWorkflowWSManager:
    """Tests for the WebSocket connection manager."""

    @pytest.fixture
    def manager(self) -> WorkflowWSManager:
        return WorkflowWSManager()

    @pytest.mark.asyncio
    async def test_subscribe(self, manager: WorkflowWSManager) -> None:
        ws = _mock_ws()
        await manager.subscribe(ws, "wf-1")
        assert await manager.active_subscriptions("wf-1") == 1
        assert await manager.connected_count() == 1

    @pytest.mark.asyncio
    async def test_subscribe_multiple_workflows(self, manager: WorkflowWSManager) -> None:
        ws = _mock_ws()
        await manager.subscribe(ws, "wf-1")
        await manager.subscribe(ws, "wf-2")
        assert await manager.active_subscriptions("wf-1") == 1
        assert await manager.active_subscriptions("wf-2") == 1
        assert await manager.connected_count() == 1  # same ws

    @pytest.mark.asyncio
    async def test_subscribe_multiple_clients(self, manager: WorkflowWSManager) -> None:
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        await manager.subscribe(ws1, "wf-1")
        await manager.subscribe(ws2, "wf-1")
        assert await manager.active_subscriptions("wf-1") == 2
        assert await manager.connected_count() == 2

    @pytest.mark.asyncio
    async def test_unsubscribe(self, manager: WorkflowWSManager) -> None:
        ws = _mock_ws()
        await manager.subscribe(ws, "wf-1")
        await manager.unsubscribe(ws, "wf-1")
        assert await manager.active_subscriptions("wf-1") == 0

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent(self, manager: WorkflowWSManager) -> None:
        ws = _mock_ws()
        # Should not raise
        await manager.unsubscribe(ws, "wf-nope")
        assert await manager.active_subscriptions("wf-nope") == 0

    @pytest.mark.asyncio
    async def test_disconnect(self, manager: WorkflowWSManager) -> None:
        ws = _mock_ws()
        await manager.subscribe(ws, "wf-1")
        await manager.subscribe(ws, "wf-2")
        await manager.disconnect(ws)
        assert await manager.active_subscriptions("wf-1") == 0
        assert await manager.active_subscriptions("wf-2") == 0
        assert await manager.connected_count() == 0

    @pytest.mark.asyncio
    async def test_disconnect_preserves_other_clients(self, manager: WorkflowWSManager) -> None:
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        await manager.subscribe(ws1, "wf-1")
        await manager.subscribe(ws2, "wf-1")
        await manager.disconnect(ws1)
        assert await manager.active_subscriptions("wf-1") == 1
        assert await manager.connected_count() == 1

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_subscribers(self, manager: WorkflowWSManager) -> None:
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        await manager.subscribe(ws1, "wf-1")
        await manager.subscribe(ws2, "wf-1")

        evt = WorkflowEvent(
            event_type=WorkflowEventType.STEP_STARTED,
            workflow_id="wf-1",
            step_id="s1",
        )
        await manager.broadcast("wf-1", evt)

        ws1.send_text.assert_awaited_once()
        ws2.send_text.assert_awaited_once()
        # Both should receive the same payload
        payload = json.loads(ws1.send_text.call_args[0][0])
        assert payload["type"] == "step_started"
        assert payload["workflow_id"] == "wf-1"

    @pytest.mark.asyncio
    async def test_broadcast_no_subscribers(self, manager: WorkflowWSManager) -> None:
        evt = WorkflowEvent(
            event_type=WorkflowEventType.WORKFLOW_COMPLETED,
            workflow_id="wf-none",
        )
        # Should not raise
        await manager.broadcast("wf-none", evt)

    @pytest.mark.asyncio
    async def test_broadcast_only_target_workflow(self, manager: WorkflowWSManager) -> None:
        ws1 = _mock_ws()
        ws2 = _mock_ws()
        await manager.subscribe(ws1, "wf-1")
        await manager.subscribe(ws2, "wf-2")

        evt = WorkflowEvent(
            event_type=WorkflowEventType.STEP_COMPLETED,
            workflow_id="wf-1",
        )
        await manager.broadcast("wf-1", evt)

        ws1.send_text.assert_awaited_once()
        ws2.send_text.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_broadcast_dead_connection_cleanup(self, manager: WorkflowWSManager) -> None:
        alive = _mock_ws(alive=True)
        dead = _mock_ws(alive=False)
        await manager.subscribe(alive, "wf-1")
        await manager.subscribe(dead, "wf-1")

        evt = WorkflowEvent(
            event_type=WorkflowEventType.STEP_COMPLETED,
            workflow_id="wf-1",
        )
        await manager.broadcast("wf-1", evt)

        # Dead connection should be cleaned up
        assert await manager.active_subscriptions("wf-1") == 1
        assert await manager.connected_count() == 1

        # Alive connection still received the event
        alive.send_text.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_clients_concurrently(
        self, manager: WorkflowWSManager
    ) -> None:
        ready = asyncio.Event()

        class _SlowWS:
            async def send_text(self, payload: str) -> None:
                assert payload
                await asyncio.sleep(0.05)

        class _FastWS:
            async def send_text(self, payload: str) -> None:
                assert payload
                ready.set()

        await manager.subscribe(_SlowWS(), "wf-1")
        await manager.subscribe(_FastWS(), "wf-1")

        evt = WorkflowEvent(
            event_type=WorkflowEventType.STEP_COMPLETED,
            workflow_id="wf-1",
        )

        start = perf_counter()
        broadcast_task = asyncio.create_task(manager.broadcast("wf-1", evt))
        await asyncio.wait_for(ready.wait(), timeout=0.02)
        await broadcast_task

        assert perf_counter() - start < 0.1

    @pytest.mark.asyncio
    async def test_subscribe_idempotent(self, manager: WorkflowWSManager) -> None:
        ws = _mock_ws()
        await manager.subscribe(ws, "wf-1")
        await manager.subscribe(ws, "wf-1")  # same sub again
        # Sets deduplicate, so still 1
        assert await manager.active_subscriptions("wf-1") == 1

    @pytest.mark.asyncio
    async def test_disconnect_unknown_ws(self, manager: WorkflowWSManager) -> None:
        ws = _mock_ws()
        # Should not raise
        await manager.disconnect(ws)
        assert await manager.connected_count() == 0


# ---------------------------------------------------------------------------
# Executor event_sink integration tests
# ---------------------------------------------------------------------------


class TestExecutorEventSink:
    """Test that WorkflowExecutor emits events via the event_sink."""

    @pytest.mark.asyncio
    async def test_executor_emits_workflow_and_step_events(self) -> None:
        from agent33.workflows.definition import WorkflowDefinition

        defn = WorkflowDefinition.model_validate(
            {
                "name": "evt-test-wf",
                "version": "1.0.0",
                "steps": [
                    {"id": "s1", "action": "transform", "inputs": {"value": "x"}},
                ],
            }
        )

        captured: list[WorkflowEvent] = []

        def sink(event: WorkflowEvent) -> None:
            captured.append(event)

        from agent33.workflows.executor import WorkflowExecutor

        executor = WorkflowExecutor(defn, event_sink=sink)
        await executor.execute({"data": "hello"})

        types = [e.event_type for e in captured]
        assert WorkflowEventType.WORKFLOW_STARTED in types
        assert WorkflowEventType.STEP_STARTED in types
        assert WorkflowEventType.STEP_COMPLETED in types
        assert WorkflowEventType.WORKFLOW_COMPLETED in types

    @pytest.mark.asyncio
    async def test_executor_no_sink_no_error(self) -> None:
        """Executor works fine without an event_sink (backward compat)."""
        from agent33.workflows.definition import WorkflowDefinition
        from agent33.workflows.executor import WorkflowExecutor

        defn = WorkflowDefinition.model_validate(
            {
                "name": "no-sink-wf",
                "version": "1.0.0",
                "steps": [
                    {"id": "s1", "action": "transform", "inputs": {"value": "x"}},
                ],
            }
        )
        executor = WorkflowExecutor(defn)
        result = await executor.execute({"data": "hello"})
        assert result.status.value == "success"

    @pytest.mark.asyncio
    async def test_executor_emits_step_skipped(self) -> None:
        from agent33.workflows.definition import WorkflowDefinition
        from agent33.workflows.executor import WorkflowExecutor

        defn = WorkflowDefinition.model_validate(
            {
                "name": "skip-wf",
                "version": "1.0.0",
                "steps": [
                    {
                        "id": "s1",
                        "action": "transform",
                        "inputs": {"value": "x"},
                        "condition": "false",
                    },
                ],
            }
        )

        captured: list[WorkflowEvent] = []
        executor = WorkflowExecutor(defn, event_sink=captured.append)
        await executor.execute({})

        types = [e.event_type for e in captured]
        assert WorkflowEventType.STEP_SKIPPED in types

    @pytest.mark.asyncio
    async def test_route_event_sink_flushes_in_order(self) -> None:
        from agent33.api.routes.workflows import _build_workflow_event_sink

        captured: list[str] = []

        class _Manager:
            async def broadcast(self, workflow_id: str, event: WorkflowEvent) -> None:
                await asyncio.sleep(0.01 if event.step_id == "s1" else 0)
                captured.append(f"{workflow_id}:{event.step_id}")

        sink, flush = _build_workflow_event_sink(_Manager())
        sink(
            WorkflowEvent(
                event_type=WorkflowEventType.STEP_STARTED,
                workflow_id="wf-ordered",
                step_id="s1",
            )
        )
        sink(
            WorkflowEvent(
                event_type=WorkflowEventType.STEP_COMPLETED,
                workflow_id="wf-ordered",
                step_id="s2",
            )
        )

        await flush()

        assert captured == ["wf-ordered:s1", "wf-ordered:s2"]


# ---------------------------------------------------------------------------
# WebSocket endpoint tests (using mock/unit approach)
# ---------------------------------------------------------------------------


class TestWorkflowWSEndpointAuth:
    """Test WebSocket endpoint authentication."""

    def test_ws_endpoint_rejects_missing_token(self) -> None:
        """WebSocket connection without token should be rejected."""
        from starlette.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect

        from agent33.main import app
        from agent33.workflows.ws_manager import WorkflowWSManager

        app.state.ws_manager = WorkflowWSManager()
        client = TestClient(app)
        with pytest.raises(WebSocketDisconnect), client.websocket_connect("/v1/workflows/ws"):
            pass

    def test_ws_endpoint_rejects_invalid_token(self) -> None:
        """WebSocket connection with bad token should be rejected."""
        from starlette.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect

        from agent33.main import app
        from agent33.workflows.ws_manager import WorkflowWSManager

        app.state.ws_manager = WorkflowWSManager()
        client = TestClient(app)
        with (
            pytest.raises(WebSocketDisconnect),
            client.websocket_connect("/v1/workflows/ws?token=bad-token"),
        ):
            pass

    def test_ws_endpoint_accepts_valid_token(self) -> None:
        """WebSocket connection with valid JWT should be accepted."""
        from starlette.testclient import TestClient

        from agent33.main import app
        from agent33.security.auth import create_access_token
        from agent33.workflows.ws_manager import WorkflowWSManager

        app.state.ws_manager = WorkflowWSManager()
        token = create_access_token("ws-user", scopes=["admin"])
        client = TestClient(app)
        with client.websocket_connect(f"/v1/workflows/ws?token={token}") as ws:
            ws.send_json({"action": "ping"})
            resp = ws.receive_json()
            assert resp == {"type": "pong"}

    def test_ws_endpoint_rejects_missing_workflows_read_scope(self) -> None:
        """WebSocket connection without workflows:read should be rejected."""
        from starlette.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect

        from agent33.main import app
        from agent33.security.auth import create_access_token
        from agent33.workflows.ws_manager import WorkflowWSManager

        app.state.ws_manager = WorkflowWSManager()
        token = create_access_token("ws-user", scopes=["agents:read"])
        client = TestClient(app)
        with (
            pytest.raises(WebSocketDisconnect),
            client.websocket_connect(f"/v1/workflows/ws?token={token}"),
        ):
            pass


class TestWorkflowWSEndpointActions:
    """Test WebSocket endpoint client message handling."""

    @pytest.fixture
    def ws_conn(self) -> Any:
        """Yield an authenticated WebSocket connection."""
        from starlette.testclient import TestClient

        from agent33.main import app
        from agent33.security.auth import create_access_token
        from agent33.workflows.ws_manager import WorkflowWSManager

        app.state.ws_manager = WorkflowWSManager()
        token = create_access_token("ws-action-user", scopes=["admin"])
        client = TestClient(app)
        with client.websocket_connect(f"/v1/workflows/ws?token={token}") as ws:
            yield ws

    def test_ping_pong(self, ws_conn: Any) -> None:
        ws_conn.send_json({"action": "ping"})
        resp = ws_conn.receive_json()
        assert resp == {"type": "pong"}

    def test_subscribe(self, ws_conn: Any) -> None:
        ws_conn.send_json({"action": "subscribe", "workflow_id": "wf-test-1"})
        resp = ws_conn.receive_json()
        assert resp["type"] == "subscribed"
        assert resp["workflow_id"] == "wf-test-1"

    def test_unsubscribe(self, ws_conn: Any) -> None:
        ws_conn.send_json({"action": "subscribe", "workflow_id": "wf-test-2"})
        ws_conn.receive_json()  # consume subscribed response
        ws_conn.send_json({"action": "unsubscribe", "workflow_id": "wf-test-2"})
        resp = ws_conn.receive_json()
        assert resp["type"] == "unsubscribed"
        assert resp["workflow_id"] == "wf-test-2"

    def test_unknown_action(self, ws_conn: Any) -> None:
        ws_conn.send_json({"action": "explode"})
        resp = ws_conn.receive_json()
        assert resp["type"] == "error"
        assert "Unknown action" in resp["message"]

    def test_invalid_json(self, ws_conn: Any) -> None:
        ws_conn.send_text("not json!!!")
        resp = ws_conn.receive_json()
        assert resp["type"] == "error"
        assert "Invalid JSON" in resp["message"]

    def test_subscribe_missing_workflow_id(self, ws_conn: Any) -> None:
        ws_conn.send_json({"action": "subscribe"})
        resp = ws_conn.receive_json()
        assert resp["type"] == "error"
        assert "workflow_id" in resp["message"]

    def test_unsubscribe_missing_workflow_id(self, ws_conn: Any) -> None:
        ws_conn.send_json({"action": "unsubscribe"})
        resp = ws_conn.receive_json()
        assert resp["type"] == "error"
        assert "workflow_id" in resp["message"]
