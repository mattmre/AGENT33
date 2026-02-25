"""Health endpoint tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] in ("healthy", "degraded")
    assert isinstance(data["services"], dict)
    allowed_statuses = {"ok", "degraded", "unavailable", "configured", "unconfigured"}
    for svc_name, svc_status in data["services"].items():
        if svc_name.startswith("channel:"):
            assert isinstance(svc_status, str) and svc_status
            continue
        assert svc_status in allowed_statuses, (
            f"Unexpected status {svc_status!r} for service {svc_name!r}"
        )


def test_health_lists_all_services(client: TestClient) -> None:
    data = client.get("/health").json()
    expected = {"ollama", "redis", "postgres", "nats"}
    assert expected.issubset(set(data["services"].keys())), (
        f"Service list mismatch. Missing: {expected - set(data['services'].keys())}"
    )
