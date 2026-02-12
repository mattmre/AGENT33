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
    for svc_name, svc_status in data["services"].items():
        assert svc_status in ("ok", "degraded", "unavailable"), (
            f"Unexpected status {svc_status!r} for service {svc_name!r}"
        )


def test_health_lists_all_services(client: TestClient) -> None:
    data = client.get("/health").json()
    expected = {"ollama", "redis", "postgres", "nats"}
    assert expected.issubset(data["services"].keys()), (
        f"Missing services: {expected - data['services'].keys()}"
    )
