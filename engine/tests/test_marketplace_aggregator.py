"""Tests for aggregated local and remote marketplace views."""

from __future__ import annotations

import json
import textwrap
import zipfile
from pathlib import Path

from agent33.packs.marketplace import LocalPackMarketplace
from agent33.packs.marketplace_aggregator import MarketplaceAggregator
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


def test_marketplace_aggregator_merges_sources(tmp_path: Path) -> None:
    _write_pack(tmp_path / "local", name="ops-pack", version="1.0.0")
    remote_pack = _write_pack(tmp_path / "remote", name="ops-pack", version="2.0.0")
    archive_path = tmp_path / "ops-pack-2.0.0.zip"
    _zip_pack(remote_pack, archive_path)
    index_path = tmp_path / "index.json"
    index_path.write_text(
        json.dumps(
            {
                "packs": [
                    {
                        "name": "ops-pack",
                        "versions": [{"version": "2.0.0", "download_url": archive_path.as_uri()}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    aggregator = MarketplaceAggregator(
        [
            LocalPackMarketplace(tmp_path / "local"),
            RemotePackMarketplace(
                RemoteMarketplaceConfig(name="community", index_url=index_path.as_uri()),
                cache_dir=tmp_path / "cache",
            ),
        ]
    )

    record = aggregator.get_pack("ops-pack")
    assert record is not None
    assert record.latest_version == "2.0.0"
    assert sorted({item.source_name for item in record.versions}) == ["community", "local"]
