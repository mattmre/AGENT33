"""Tests for plugin doctor diagnostics."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from agent33.plugins.config_store import PluginConfigStore
from agent33.plugins.context import PluginContext
from agent33.plugins.doctor import PluginDoctor
from agent33.plugins.installer import PluginInstaller, PluginInstallMode
from agent33.plugins.registry import PluginRegistry
from agent33.services.orchestration_state import OrchestrationStateStore
from agent33.skills.registry import SkillRegistry

if TYPE_CHECKING:
    from pathlib import Path


def _write_plugin(base_dir: Path, name: str, *, permissions: list[str] | None = None) -> Path:
    plugin_dir = base_dir / name
    plugin_dir.mkdir(parents=True, exist_ok=True)
    permissions_yaml = ""
    for permission in permissions or []:
        permissions_yaml += f"permissions:\n  - {permission}\n"
    (plugin_dir / "plugin.yaml").write_text(
        "\n".join(
            [
                f"name: {name}",
                "version: 1.0.0",
                f"description: Test plugin {name}",
                'entry_point: "plugin:Plugin"',
                permissions_yaml.rstrip(),
            ]
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    (plugin_dir / "plugin.py").write_text(
        "\n".join(
            [
                "from agent33.plugins.base import PluginBase",
                "",
                "class Plugin(PluginBase):",
                "    async def on_load(self):",
                "        return None",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return plugin_dir


def _context_factory(manifest, plugin_dir: Path) -> PluginContext:  # type: ignore[no-untyped-def]
    return PluginContext(
        plugin_name=manifest.name,
        plugin_dir=plugin_dir,
        granted_permissions=frozenset(),
        skill_registry=SkillRegistry(),
        tool_registry=MagicMock(),
        agent_registry=MagicMock(),
    )


class TestPluginDoctor:
    async def test_diagnose_reports_missing_install_source(self, tmp_path) -> None:
        source = _write_plugin(tmp_path / "sources", "alpha-plugin")
        state_store = OrchestrationStateStore(str(tmp_path / "plugin_state.json"))
        registry = PluginRegistry()
        installer = PluginInstaller(
            registry,
            plugins_dir=tmp_path / "managed",
            context_factory=_context_factory,
            state_store=state_store,
        )
        await installer.install_from_local(source, mode=PluginInstallMode.LINK, enable=False)
        doctor = PluginDoctor(registry, installer=installer)

        shutil.rmtree(source)

        report = await doctor.diagnose("alpha-plugin")

        assert report.overall_status == "broken"
        assert any(check.name == "source" and check.status == "error" for check in report.checks)

    async def test_diagnose_includes_permission_inventory(self, tmp_path) -> None:
        source = _write_plugin(tmp_path / "sources", "beta-plugin", permissions=["config:read"])
        state_store = OrchestrationStateStore(str(tmp_path / "plugin_state.json"))
        config_store = PluginConfigStore(state_store)
        config_store.put("beta-plugin", permission_overrides={"config:read": False})
        registry = PluginRegistry()

        def context_factory(manifest, plugin_dir: Path) -> PluginContext:  # type: ignore[no-untyped-def]
            return PluginContext(
                plugin_name=manifest.name,
                plugin_dir=plugin_dir,
                granted_permissions=frozenset(),
                skill_registry=SkillRegistry(),
                tool_registry=MagicMock(),
                agent_registry=MagicMock(),
            )

        installer = PluginInstaller(
            registry,
            plugins_dir=tmp_path / "managed",
            context_factory=context_factory,
            state_store=state_store,
        )
        await installer.install_from_local(source, enable=False)

        report = await PluginDoctor(
            registry, config_store=config_store, installer=installer
        ).diagnose("beta-plugin")

        assert report.permissions.requested == ["config:read"]
        assert report.permissions.plugin_name == "beta-plugin"
        assert report.permissions.granted == []
        assert report.permissions.denied == ["config:read"]
