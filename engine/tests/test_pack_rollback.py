"""Tests for pack rollback support."""

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

from agent33.packs.models import PackSource
from agent33.packs.registry import PackRegistry
from agent33.packs.rollback import PackRollbackManager
from agent33.services.orchestration_state import OrchestrationStateStore
from agent33.skills.registry import SkillRegistry

if TYPE_CHECKING:
    from pathlib import Path


def _write_pack(base: Path, *, name: str, version: str) -> Path:
    pack_dir = base / name
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / "PACK.yaml").write_text(
        textwrap.dedent(
            f"""\
            name: {name}
            version: {version}
            description: Pack {name}
            author: tester
            skills:
              - name: skill-1
                path: skills/skill-1
            """
        ),
        encoding="utf-8",
    )
    skill_dir = pack_dir / "skills" / "skill-1"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: skill-1\ndescription: Skill\n---\n# Skill\n",
        encoding="utf-8",
    )
    return pack_dir


def test_pack_rollback_restores_archived_version_and_enablement(tmp_path: Path) -> None:
    skill_registry = SkillRegistry()
    pack_registry = PackRegistry(packs_dir=tmp_path / "packs", skill_registry=skill_registry)
    v1 = _write_pack(tmp_path / "sources" / "v1", name="ops-pack", version="1.0.0")
    v2 = _write_pack(tmp_path / "sources" / "v2", name="ops-pack", version="2.0.0")
    state_store = OrchestrationStateStore(str(tmp_path / "rollback-state.json"))
    rollback_manager = PackRollbackManager(
        pack_registry,
        archive_dir=tmp_path / "archive",
        state_store=state_store,
    )

    install_result = pack_registry.install(PackSource(source_type="local", path=str(v1)))
    assert install_result.success is True
    pack_registry.enable("ops-pack", "tenant-a")

    rollback_manager.archive_current("ops-pack")
    upgrade_result = pack_registry.upgrade("ops-pack", v2, "2.0.0")
    assert upgrade_result.success is True

    rollback_result, archived = rollback_manager.rollback("ops-pack", version="1.0.0")

    assert rollback_result.success is True
    assert archived.version == "1.0.0"
    assert pack_registry.get("ops-pack").version == "1.0.0"  # type: ignore[union-attr]
    assert pack_registry.is_enabled("ops-pack", "tenant-a") is True
