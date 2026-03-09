"""Local marketplace catalog for skill pack discovery and installation."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003 -- Pydantic needs Path at runtime

import structlog
from pydantic import BaseModel, Field

from agent33.packs.loader import load_pack_manifest
from agent33.packs.version import Version

logger = structlog.get_logger()


class MarketplacePackVersion(BaseModel):
    """A single marketplace pack version."""

    version: str
    pack_dir: Path
    description: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    category: str = ""
    skills_count: int = 0

    model_config = {"arbitrary_types_allowed": True}


class MarketplacePackRecord(BaseModel):
    """Marketplace listing grouped by pack name."""

    name: str
    description: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    category: str = ""
    latest_version: str
    versions: list[MarketplacePackVersion] = Field(default_factory=list)


class LocalPackMarketplace:
    """Filesystem-backed marketplace catalog for pack discovery."""

    def __init__(self, root_dir: Path) -> None:
        self._root_dir = root_dir
        self._records: dict[str, MarketplacePackRecord] = {}

    def refresh(self) -> None:
        """Rebuild the marketplace catalog from disk."""
        grouped: dict[str, list[MarketplacePackVersion]] = {}
        manifest_dirs: set[Path] = set()
        if self._root_dir.is_dir():
            manifest_dirs.update(path.parent for path in self._root_dir.rglob("PACK.yaml"))
            manifest_dirs.update(path.parent for path in self._root_dir.rglob("pack.yaml"))

        for pack_dir in sorted(manifest_dirs):
            try:
                manifest = load_pack_manifest(pack_dir)
                Version.parse(manifest.version)
            except Exception:
                logger.warning(
                    "marketplace_manifest_load_failed",
                    path=str(pack_dir),
                    exc_info=True,
                )
                continue

            grouped.setdefault(manifest.name, []).append(
                MarketplacePackVersion(
                    version=manifest.version,
                    pack_dir=pack_dir,
                    description=manifest.description,
                    author=manifest.author,
                    tags=manifest.tags,
                    category=manifest.category,
                    skills_count=len(manifest.skills),
                )
            )

        records: dict[str, MarketplacePackRecord] = {}
        for name, versions in grouped.items():
            ordered = sorted(versions, key=lambda item: Version.parse(item.version), reverse=True)
            latest = ordered[0]
            records[name] = MarketplacePackRecord(
                name=name,
                description=latest.description,
                author=latest.author,
                tags=list(latest.tags),
                category=latest.category,
                latest_version=latest.version,
                versions=ordered,
            )

        self._records = records

    def list_packs(self) -> list[MarketplacePackRecord]:
        """List marketplace packs sorted by name."""
        self.refresh()
        return [self._records[name] for name in sorted(self._records)]

    def search(self, query: str) -> list[MarketplacePackRecord]:
        """Search marketplace packs by name, description, or tags."""
        query_lower = query.lower()
        return [
            record
            for record in self.list_packs()
            if query_lower in record.name.lower()
            or query_lower in record.description.lower()
            or any(query_lower in tag.lower() for tag in record.tags)
        ]

    def get_pack(self, name: str) -> MarketplacePackRecord | None:
        """Return a single marketplace pack by name."""
        self.refresh()
        return self._records.get(name)

    def list_versions(self, name: str) -> list[MarketplacePackVersion]:
        """List versions for a marketplace pack, newest first."""
        record = self.get_pack(name)
        if record is None:
            return []
        return list(record.versions)

    def resolve(self, name: str, version: str = "") -> Path | None:
        """Resolve a marketplace pack name/version to a concrete directory."""
        versions = self.list_versions(name)
        if not versions:
            return None
        if not version:
            return versions[0].pack_dir
        for item in versions:
            if item.version == version:
                return item.pack_dir
        return None
