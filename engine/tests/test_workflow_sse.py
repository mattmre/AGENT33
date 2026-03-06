"""Tests for run-scoped workflow SSE status streaming and graph overlays."""

from __future__ import annotations

import asyncio
import contextlib
import json
from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from agent33.api.routes.workflow_sse import stream_workflow_events
from agent33.main import app
from agent33.security.auth import create_access_token
from agent33.workflows.events import WorkflowEvent, WorkflowEventType
from agent33.workflows.ws_manager import WorkflowWSManager

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fastapi.responses import StreamingResponse


@pytest.fixture(autouse=True)
def clear_workflow_state() -> None:
    """Clear workflow registry, history, scheduler, auth, and live state."""
    from agent33.api.routes import workflows
    from agent33.security import auth

    def _reset() -> None:
        workflows._registry.clear()
        workflows._execution_history.clear()
        if workflows._scheduler is not None:
            with contextlib.suppress(RuntimeError):
                workflows._scheduler.stop()
            workflows._scheduler = None
        workflows.set_ws_manager(None)
        auth._api_keys.clear()
        app.state.ws_manager = None

    _reset()
    yield
    _reset()


def _install_manager(manager: WorkflowWSManager) -> None:
    from agent33.api.routes import workflows

    app.state.ws_manager = manager
    workflows.set_ws_manager(manager)


def _seed_workflow(client: TestClient, workflow_name: str) -> None:
    response = client.post(
        "/v1/workflows/",
        json={
            "name": workflow_name,
            "version": "1.0.0",
            "description": "Workflow SSE test",
            "steps": [
                {
                    "id": "step-a",
                    "action": "transform",
                    "transform": "inputs",
                }
            ],
            "execution": {"mode": "sequential"},
        },
    )
    assert response.status_code == 201


def _read_sse_events(lines: Iterator[str | bytes], count: int) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in lines:
        if isinstance(line, bytes):
            line = line.decode()
        if not line or not line.startswith("data: "):
            continue
        events.append(json.loads(line[6:]))
        if len(events) >= count:
            break
    return events


def _mock_request(manager: WorkflowWSManager) -> SimpleNamespace:
    state = SimpleNamespace(ws_manager=manager)
    return SimpleNamespace(
        app=SimpleNamespace(state=state),
        is_disconnected=AsyncMock(return_value=False),
    )


async def _read_sse_chunk(response: StreamingResponse) -> dict[str, object]:
    body_iterator = response.body_iterator
    chunk = await anext(body_iterator)
    if isinstance(chunk, bytes):
        chunk = chunk.decode()
    return json.loads(chunk.split("data: ", maxsplit=1)[1].strip())


async def _close_sse_response(response: StreamingResponse) -> None:
    await response.body_iterator.aclose()


class TestWorkflowSSEEndpoint:
    def test_sse_endpoint_requires_authentication(self) -> None:
        manager = WorkflowWSManager()
        asyncio.run(manager.register_run("run-no-auth", "wf-auth"))
        _install_manager(manager)

        client = TestClient(app)
        response = client.get("/v1/workflows/run-no-auth/events")

        assert response.status_code == 401

    def test_sse_endpoint_requires_workflows_read_scope(self) -> None:
        manager = WorkflowWSManager()
        asyncio.run(manager.register_run("run-no-scope", "wf-no-scope"))
        _install_manager(manager)

        token = create_access_token("workflow-sse-user", scopes=[])
        client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
        response = client.get("/v1/workflows/run-no-scope/events")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_sse_endpoint_streams_sync_event(self) -> None:
        manager = WorkflowWSManager(heartbeat_interval_seconds=60)
        await manager.register_run("run-api-key", "wf-api-key")
        _install_manager(manager)

        request = _mock_request(manager)
        sse_response = await stream_workflow_events("run-api-key", request)
        try:
            event = await _read_sse_chunk(sse_response)
        finally:
            await _close_sse_response(sse_response)

        assert event == {
            "type": "sync",
            "run_id": "run-api-key",
            "workflow_name": "wf-api-key",
            "timestamp": event["timestamp"],
            "data": {
                "status": "pending",
                "step_statuses": {},
                "last_event_type": None,
                "terminal": False,
                "updated_at": event["data"]["updated_at"],
            },
        }

    @pytest.mark.asyncio
    async def test_sse_endpoint_streams_live_events_and_cleans_up_on_disconnect(self) -> None:
        manager = WorkflowWSManager(heartbeat_interval_seconds=60)
        await manager.register_run("run-live", "wf-live")
        _install_manager(manager)

        request = _mock_request(manager)
        sse_response = await stream_workflow_events("run-live", request)
        try:
            sync_event = await _read_sse_chunk(sse_response)
            assert sync_event["type"] == "sync"
            assert await manager.active_sse_subscriptions("run-live") == 1

            await manager.publish_event(
                WorkflowEvent(
                    event_type=WorkflowEventType.STEP_STARTED,
                    run_id="run-live",
                    workflow_name="wf-live",
                    step_id="step-a",
                )
            )
            live_event = await _read_sse_chunk(sse_response)
        finally:
            await _close_sse_response(sse_response)

        assert live_event["type"] == "step_started"
        assert live_event["step_id"] == "step-a"
        assert await manager.active_sse_subscriptions("run-live") == 0

    @pytest.mark.asyncio
    async def test_sse_endpoint_emits_heartbeat_events(self) -> None:
        manager = WorkflowWSManager(heartbeat_interval_seconds=0.01)
        await manager.register_run("run-heartbeat", "wf-heartbeat")
        _install_manager(manager)

        request = _mock_request(manager)
        sse_response = await stream_workflow_events("run-heartbeat", request)
        try:
            events = [await _read_sse_chunk(sse_response), await _read_sse_chunk(sse_response)]
        finally:
            await _close_sse_response(sse_response)

        assert events[0] == {
            "type": "sync",
            "run_id": "run-heartbeat",
            "workflow_name": "wf-heartbeat",
            "timestamp": events[0]["timestamp"],
            "data": {
                "status": "pending",
                "step_statuses": {},
                "last_event_type": None,
                "terminal": False,
                "updated_at": events[0]["data"]["updated_at"],
            },
        }
        assert events[1] == {
            "type": "heartbeat",
            "run_id": "run-heartbeat",
            "workflow_name": "wf-heartbeat",
            "timestamp": events[1]["timestamp"],
            "data": {"status": "pending", "terminal": False},
        }


class TestWorkflowGraphLiveOverlay:
    def test_graph_route_prefers_live_snapshot_for_requested_run(self) -> None:
        token = create_access_token(
            "workflow-visualizer",
            scopes=["workflows:read", "workflows:write"],
        )
        client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
        workflow_name = "viz-live"
        _seed_workflow(client, workflow_name)

        manager = WorkflowWSManager()
        asyncio.run(manager.register_run("run-viz-live", workflow_name))
        asyncio.run(
            manager.publish_event(
                WorkflowEvent(
                    event_type=WorkflowEventType.STEP_STARTED,
                    run_id="run-viz-live",
                    workflow_name=workflow_name,
                    step_id="step-a",
                )
            )
        )
        _install_manager(manager)

        from agent33.api.routes import workflows

        workflows._execution_history.append(
            {
                "run_id": "old-history-run",
                "workflow_name": workflow_name,
                "trigger_type": "manual",
                "status": "success",
                "duration_ms": 5,
                "timestamp": 1.0,
                "error": None,
                "job_id": None,
                "step_statuses": {"step-a": "success"},
            }
        )

        response = client.get(
            f"/v1/visualizations/workflows/{workflow_name}/graph",
            params={"run_id": "run-viz-live"},
        )

        assert response.status_code == 200
        graph = response.json()
        assert graph["nodes"][0]["id"] == "step-a"
        assert graph["nodes"][0]["status"] == "running"

    def test_graph_route_falls_back_to_history_when_live_run_is_missing(self) -> None:
        token = create_access_token(
            "workflow-visualizer",
            scopes=["workflows:read", "workflows:write"],
        )
        client = TestClient(app, headers={"Authorization": f"Bearer {token}"})
        workflow_name = "viz-history"
        _seed_workflow(client, workflow_name)

        from agent33.api.routes import workflows

        workflows._execution_history.append(
            {
                "run_id": "history-run",
                "workflow_name": workflow_name,
                "trigger_type": "manual",
                "status": "success",
                "duration_ms": 5,
                "timestamp": 1.0,
                "error": None,
                "job_id": None,
                "step_statuses": {"step-a": "success"},
            }
        )

        response = client.get(
            f"/v1/visualizations/workflows/{workflow_name}/graph",
            params={"run_id": "missing-live-run"},
        )

        assert response.status_code == 200
        graph = response.json()
        assert graph["nodes"][0]["status"] == "success"
