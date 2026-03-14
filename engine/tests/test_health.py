"""Health endpoint tests."""

from __future__ import annotations

import contextlib
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient

import pytest

from agent33.main import app


class _AsyncHealthService:
    def __init__(self, status: str) -> None:
        self._status = status

    async def health_snapshot(self) -> dict[str, str]:
        return {"status": self._status}


class _FakeAsyncClient:
    async def __aenter__(self) -> _FakeAsyncClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, url: str, headers=None):  # noqa: ANN001
        return SimpleNamespace(status_code=200)


class _FakeRedisClient:
    async def ping(self) -> None:
        return None

    async def aclose(self) -> None:
        return None


@pytest.fixture(autouse=True)
def _install_phase48_health_services(monkeypatch: pytest.MonkeyPatch) -> None:
    original_voice = getattr(app.state, "voice_sidecar_probe", None)
    original_status_line = getattr(app.state, "status_line_service", None)
    app.state.voice_sidecar_probe = _AsyncHealthService("ok")
    app.state.status_line_service = _AsyncHealthService("ok")
    monkeypatch.setattr(
        "agent33.api.routes.health.httpx.AsyncClient", lambda timeout=3: _FakeAsyncClient()
    )
    monkeypatch.setitem(
        sys.modules,
        "redis.asyncio",
        SimpleNamespace(from_url=lambda *args, **kwargs: _FakeRedisClient()),
    )
    monkeypatch.setitem(
        sys.modules,
        "asyncpg",
        SimpleNamespace(
            connect=_fake_asyncpg_connect,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "nats",
        SimpleNamespace(connect=_fake_nats_connect),
    )
    yield
    if original_voice is not None:
        app.state.voice_sidecar_probe = original_voice
    else:
        with contextlib.suppress(AttributeError):
            del app.state.voice_sidecar_probe
    if original_status_line is not None:
        app.state.status_line_service = original_status_line
    else:
        with contextlib.suppress(AttributeError):
            del app.state.status_line_service


async def _fake_asyncpg_connect(*args, **kwargs):  # noqa: ANN002, ANN003
    class _Conn:
        async def execute(self, query: str) -> None:
            return None

        async def close(self) -> None:
            return None

    return _Conn()


async def _fake_nats_connect(*args, **kwargs):  # noqa: ANN002, ANN003
    class _Conn:
        async def close(self) -> None:
            return None

    return _Conn()


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
    expected = {"ollama", "redis", "postgres", "nats", "voice_sidecar", "status_line"}
    assert expected.issubset(set(data["services"].keys())), (
        f"Service list mismatch. Missing: {expected - set(data['services'].keys())}"
    )
