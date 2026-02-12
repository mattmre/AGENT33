"""Health endpoint tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "services" in data


def test_health_lists_all_services(client: TestClient) -> None:
    data = client.get("/health").json()
    for svc in ("ollama", "redis", "postgres", "nats"):
        assert svc in data["services"]
