"""Tests for remote pack marketplace sources."""

from __future__ import annotations

import json
import textwrap
import zipfile
from pathlib import Path

from agent33.packs.remote_marketplace import RemoteMarketplaceConfig, RemotePackMarketplace


def _write_pack(base: Path, *, name: str, version: str) -> Path:
    pack_dir = base / f"{name}-{version}"
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


def _zip_pack(pack_dir: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w") as archive:
        for path in pack_dir.rglob("*"):
            archive.write(path, arcname=str(Path(pack_dir.name) / path.relative_to(pack_dir)))


def test_remote_marketplace_lists_and_resolves_pack(tmp_path: Path) -> None:
    pack_dir = _write_pack(tmp_path / "packs", name="remote-pack", version="1.2.0")
    archive_path = tmp_path / "remote-pack-1.2.0.zip"
    _zip_pack(pack_dir, archive_path)
    index_path = tmp_path / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "packs": [
                    {
                        "name": "remote-pack",
                        "description": "Remote pack",
                        "versions": [
                            {
                                "version": "1.2.0",
                                "download_url": archive_path.as_uri(),
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    marketplace = RemotePackMarketplace(
        RemoteMarketplaceConfig(name="community", index_url=index_path.as_uri()),
        cache_dir=tmp_path / "cache",
    )

    packs = marketplace.list_packs()
    assert [record.name for record in packs] == ["remote-pack"]
    assert packs[0].versions[0].source_name == "community"

    resolved = marketplace.resolve("remote-pack", "1.2.0")
    assert resolved is not None
    assert (resolved.pack_dir / "PACK.yaml").is_file()
