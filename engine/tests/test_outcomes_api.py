"""Phase 30 Stage 1 tests for outcomes backend contracts."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from agent33.api.routes.outcomes import _service
from agent33.main import app
from agent33.security.auth import create_access_token


def _client(scopes: list[str], *, tenant_id: str = "tenant-a") -> TestClient:
    token = create_access_token("outcomes-user", scopes=scopes, tenant_id=tenant_id)
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


@pytest.fixture(autouse=True)
def reset_outcomes_service() -> None:
    _service._events.clear()
    yield
    _service._events.clear()


@pytest.fixture
def writer_client() -> TestClient:
    return _client(["outcomes:read", "outcomes:write"])


@pytest.fixture
def reader_client() -> TestClient:
    return _client(["outcomes:read"])


@pytest.fixture
def no_scope_client() -> TestClient:
    return _client([])


@pytest.fixture
def tenant_b_writer() -> TestClient:
    return _client(["outcomes:read", "outcomes:write"], tenant_id="tenant-b")


@pytest.fixture
def anonymous_client() -> TestClient:
    return TestClient(app)


def test_outcomes_endpoints_require_auth(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/v1/outcomes/events")
    assert response.status_code == 401


def test_outcomes_scope_enforcement(
    reader_client: TestClient, no_scope_client: TestClient
) -> None:
    write_response = reader_client.post(
        "/v1/outcomes/events",
        json={
            "domain": "delivery",
            "event_type": "deploy",
            "metric_type": "success_rate",
            "value": 0.9,
        },
    )
    assert write_response.status_code == 403
    assert "outcomes:write" in write_response.json()["detail"]

    read_response = no_scope_client.get("/v1/outcomes/events")
    assert read_response.status_code == 403
    assert "outcomes:read" in read_response.json()["detail"]


def test_events_are_tenant_scoped(
    writer_client: TestClient, tenant_b_writer: TestClient
) -> None:
    writer_client.post(
        "/v1/outcomes/events",
        json={
            "domain": "delivery",
            "event_type": "deploy",
            "metric_type": "success_rate",
            "value": 0.8,
        },
    )
    tenant_b_writer.post(
        "/v1/outcomes/events",
        json={
            "domain": "delivery",
            "event_type": "deploy",
            "metric_type": "success_rate",
            "value": 0.2,
        },
    )

    tenant_a_events = writer_client.get("/v1/outcomes/events").json()
    tenant_b_events = tenant_b_writer.get("/v1/outcomes/events").json()
    assert len(tenant_a_events) == 1
    assert len(tenant_b_events) == 1
    assert tenant_a_events[0]["tenant_id"] == "tenant-a"
    assert tenant_b_events[0]["tenant_id"] == "tenant-b"


def test_list_events_supports_domain_and_event_filters(writer_client: TestClient) -> None:
    writer_client.post(
        "/v1/outcomes/events",
        json={
            "domain": "delivery",
            "event_type": "deploy",
            "metric_type": "success_rate",
            "value": 0.8,
        },
    )
    writer_client.post(
        "/v1/outcomes/events",
        json={
            "domain": "support",
            "event_type": "ticket_closed",
            "metric_type": "quality_score",
            "value": 0.6,
        },
    )

    response = writer_client.get(
        "/v1/outcomes/events",
        params={"domain": "delivery", "event_type": "deploy"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["domain"] == "delivery"
    assert payload[0]["event_type"] == "deploy"


def test_trend_direction_values_are_deterministic(writer_client: TestClient) -> None:
    base = datetime.now(UTC) - timedelta(hours=1)
    improving_values = [0.40, 0.45, 0.80, 0.90]
    declining_values = [0.90, 0.80, 0.45, 0.40]

    for idx, value in enumerate(improving_values):
        writer_client.post(
            "/v1/outcomes/events",
            json={
                "domain": "delivery",
                "event_type": "deploy",
                "metric_type": "success_rate",
                "value": value,
                "occurred_at": (base + timedelta(minutes=idx)).isoformat(),
            },
        )
    for idx, value in enumerate(declining_values):
        writer_client.post(
            "/v1/outcomes/events",
            json={
                "domain": "qa",
                "event_type": "test_run",
                "metric_type": "success_rate",
                "value": value,
                "occurred_at": (base + timedelta(minutes=10 + idx)).isoformat(),
            },
        )

    improving = writer_client.get(
        "/v1/outcomes/trends/success_rate",
        params={"domain": "delivery", "window": 4},
    )
    declining = writer_client.get(
        "/v1/outcomes/trends/success_rate",
        params={"domain": "qa", "window": 4},
    )
    stable = writer_client.get(
        "/v1/outcomes/trends/success_rate",
        params={"domain": "unknown-domain", "window": 4},
    )

    assert improving.status_code == 200
    assert improving.json()["direction"] == "improving"
    assert declining.status_code == 200
    assert declining.json()["direction"] == "declining"
    assert stable.status_code == 200
    assert stable.json()["direction"] == "stable"


def test_dashboard_contract(writer_client: TestClient, tenant_b_writer: TestClient) -> None:
    writer_client.post(
        "/v1/outcomes/events",
        json={
            "domain": "delivery",
            "event_type": "deploy",
            "metric_type": "success_rate",
            "value": 0.85,
        },
    )
    writer_client.post(
        "/v1/outcomes/events",
        json={
            "domain": "delivery",
            "event_type": "latency_sample",
            "metric_type": "latency_ms",
            "value": 120.0,
        },
    )
    tenant_b_writer.post(
        "/v1/outcomes/events",
        json={
            "domain": "delivery",
            "event_type": "deploy",
            "metric_type": "success_rate",
            "value": 0.10,
        },
    )

    response = writer_client.get(
        "/v1/outcomes/dashboard",
        params={"window": 10, "recent_limit": 5},
    )
    assert response.status_code == 200
    payload = response.json()
    assert {"trends", "recent_events", "summary"} <= payload.keys()

    summary = payload["summary"]
    assert summary["total_events"] == 2
    assert summary["domains"] == ["delivery"]
    assert set(summary["event_types"]) == {"deploy", "latency_sample"}
    assert summary["metric_counts"]["success_rate"] == 1
    assert summary["metric_counts"]["latency_ms"] == 1

    trends = payload["trends"]
    assert len(trends) == 4
    assert {item["metric_type"] for item in trends} == {
        "success_rate",
        "quality_score",
        "latency_ms",
        "cost_usd",
    }
    assert all(item["direction"] in {"improving", "stable", "declining"} for item in trends)

    recent = payload["recent_events"]
    assert len(recent) == 2
    assert all(item["tenant_id"] == "tenant-a" for item in recent)
