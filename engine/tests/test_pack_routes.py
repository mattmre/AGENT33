"""Tests for pack management API endpoints.

Tests cover: list packs, get pack, install, uninstall, enable, disable,
search, and sync endpoints with proper auth and tenant scoping.
"""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

if TYPE_CHECKING:
    from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent33.api.routes.packs import router
from agent33.packs.registry import PackRegistry
from agent33.skills.registry import SkillRegistry


def _write_pack(base: Path, *, name: str = "test-pack") -> Path:
    """Create a minimal valid pack directory."""
    pack_dir = base / name
    pack_dir.mkdir(parents=True, exist_ok=True)

    (pack_dir / "PACK.yaml").write_text(
        textwrap.dedent(f"""\
        name: {name}
        version: 1.0.0
        description: Pack {name}
        author: tester
        tags:
          - test
        skills:
          - name: skill-1
            path: skills/skill-1
        """),
        encoding="utf-8",
    )
    sdir = pack_dir / "skills" / "skill-1"
    sdir.mkdir(parents=True)
    (sdir / "SKILL.md").write_text(
        f"---\nname: skill-1\ndescription: Skill from {name}\n---\n# S1\n",
        encoding="utf-8",
    )
    return pack_dir


def _create_test_app(pack_registry: PackRegistry | None = None) -> FastAPI:
    """Create a minimal FastAPI app with the packs router for testing."""
    app = FastAPI()
    app.include_router(router)

    if pack_registry is not None:
        app.state.pack_registry = pack_registry

    # Mock auth middleware: inject a fake user with tenant_id
    from starlette.middleware.base import BaseHTTPMiddleware

    class FakeAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Any, call_next: Any) -> Any:
            user = MagicMock()
            user.tenant_id = "test-tenant"
            user.scopes = [
                "agents:read", "agents:write", "admin",
            ]
            request.state.user = user
            return await call_next(request)

    app.add_middleware(FakeAuthMiddleware)
    return app


class TestPackRoutesWithoutRegistry:
    """Test endpoints when pack registry is not initialized."""

    def test_list_packs_no_registry(self) -> None:
        app = _create_test_app(pack_registry=None)
        client = TestClient(app)
        resp = client.get("/v1/packs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["packs"] == []
        assert data["count"] == 0

    def test_search_no_registry(self) -> None:
        app = _create_test_app(pack_registry=None)
        client = TestClient(app)
        resp = client.get("/v1/packs/search", params={"q": "test"})
        assert resp.status_code == 200
        assert resp.json()["results"] == []


class TestPackRoutesWithRegistry:
    """Test endpoints with a functioning pack registry."""

    def _setup(self, tmp_path: Path) -> tuple[TestClient, PackRegistry, Path]:
        packs_dir = tmp_path / "packs"
        packs_dir.mkdir()
        skill_reg = SkillRegistry()
        pack_reg = PackRegistry(packs_dir=packs_dir, skill_registry=skill_reg)
        app = _create_test_app(pack_registry=pack_reg)
        client = TestClient(app)
        return client, pack_reg, packs_dir

    def test_list_packs_empty(self, tmp_path: Path) -> None:
        client, _, _ = self._setup(tmp_path)
        resp = client.get("/v1/packs")
        assert resp.status_code == 200
        assert resp.json()["count"] == 0

    def test_list_packs_with_installed(self, tmp_path: Path) -> None:
        client, pack_reg, packs_dir = self._setup(tmp_path)
        _write_pack(packs_dir, name="my-pack")
        pack_reg.discover()

        resp = client.get("/v1/packs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["packs"][0]["name"] == "my-pack"

    def test_get_pack_found(self, tmp_path: Path) -> None:
        client, pack_reg, packs_dir = self._setup(tmp_path)
        _write_pack(packs_dir, name="detail-pack")
        pack_reg.discover()

        resp = client.get("/v1/packs/detail-pack")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "detail-pack"
        assert data["version"] == "1.0.0"
        assert data["author"] == "tester"
        assert data["enabled_for_tenant"] is False

    def test_get_pack_not_found(self, tmp_path: Path) -> None:
        client, _, _ = self._setup(tmp_path)
        resp = client.get("/v1/packs/nonexistent")
        assert resp.status_code == 404

    def test_install_pack(self, tmp_path: Path) -> None:
        client, pack_reg, packs_dir = self._setup(tmp_path)
        pack_path = _write_pack(tmp_path / "source", name="new-pack")

        resp = client.post(
            "/v1/packs/install",
            json={"source_type": "local", "path": str(pack_path)},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["pack_name"] == "new-pack"
        assert data["skills_loaded"] == 1

    def test_install_invalid_path(self, tmp_path: Path) -> None:
        client, _, _ = self._setup(tmp_path)
        resp = client.post(
            "/v1/packs/install",
            json={"source_type": "local", "path": "/nonexistent/path"},
        )
        assert resp.status_code == 400

    def test_uninstall_pack(self, tmp_path: Path) -> None:
        client, pack_reg, packs_dir = self._setup(tmp_path)
        _write_pack(packs_dir, name="removable")
        pack_reg.discover()

        resp = client.delete("/v1/packs/removable")
        assert resp.status_code == 204

    def test_uninstall_not_found(self, tmp_path: Path) -> None:
        client, _, _ = self._setup(tmp_path)
        resp = client.delete("/v1/packs/ghost")
        assert resp.status_code == 404

    def test_enable_pack(self, tmp_path: Path) -> None:
        client, pack_reg, packs_dir = self._setup(tmp_path)
        _write_pack(packs_dir, name="enableable")
        pack_reg.discover()

        resp = client.post("/v1/packs/enableable/enable")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["action"] == "enabled"
        assert data["pack_name"] == "enableable"

    def test_enable_not_installed(self, tmp_path: Path) -> None:
        client, _, _ = self._setup(tmp_path)
        resp = client.post("/v1/packs/ghost/enable")
        assert resp.status_code == 404

    def test_disable_pack(self, tmp_path: Path) -> None:
        client, pack_reg, packs_dir = self._setup(tmp_path)
        _write_pack(packs_dir, name="disableable")
        pack_reg.discover()
        pack_reg.enable("disableable", "test-tenant")

        resp = client.post("/v1/packs/disableable/disable")
        assert resp.status_code == 200
        data = resp.json()
        assert data["action"] == "disabled"

    def test_search_packs(self, tmp_path: Path) -> None:
        client, pack_reg, packs_dir = self._setup(tmp_path)
        _write_pack(packs_dir, name="kubernetes-ops")
        _write_pack(packs_dir, name="data-analysis")
        pack_reg.discover()

        resp = client.get("/v1/packs/search", params={"q": "kubernetes"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["name"] == "kubernetes-ops"

    def test_list_enabled_packs(self, tmp_path: Path) -> None:
        client, pack_reg, packs_dir = self._setup(tmp_path)
        _write_pack(packs_dir, name="enabled-pack")
        pack_reg.discover()
        pack_reg.enable("enabled-pack", "test-tenant")

        resp = client.get("/v1/packs/enabled")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["tenant_id"] == "test-tenant"

    def test_sync_pack(self, tmp_path: Path) -> None:
        client, pack_reg, packs_dir = self._setup(tmp_path)
        _write_pack(packs_dir, name="syncable")
        pack_reg.discover()

        resp = client.post("/v1/packs/syncable/sync")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["pack_name"] == "syncable"
