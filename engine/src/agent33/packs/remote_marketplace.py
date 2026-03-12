"""Remote marketplace source support for pack discovery and download."""

from __future__ import annotations

import json
import shutil
import zipfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast
from urllib.parse import urlparse
from urllib.request import url2pathname

import httpx
import structlog
from pydantic import BaseModel, Field

from agent33.packs.marketplace import (
    MarketplacePackRecord,
    MarketplacePackVersion,
    MarketplaceResolvedPack,
)
from agent33.packs.provenance import PackProvenance, TrustLevel
from agent33.packs.version import Version

logger = structlog.get_logger()


class RemoteMarketplaceConfig(BaseModel):
    """Configuration for a remote marketplace source."""

    name: str
    index_url: str
    auth_token: str = ""
    trust_level: TrustLevel = TrustLevel.COMMUNITY
    cache_ttl_seconds: int = 3600


class RemotePackIndex(BaseModel):
    """Cached remote marketplace index."""

    source: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    packs: list[MarketplacePackRecord] = Field(default_factory=list)


class RemotePackMarketplace:
    """Marketplace backed by a remote JSON index and downloadable zip archives."""

    def __init__(self, config: RemoteMarketplaceConfig, *, cache_dir: Path) -> None:
        self._config = config
        self._cache_dir = cache_dir / config.name
        self._index: RemotePackIndex | None = None
        self.source_name = config.name

    def invalidate(self) -> None:
        """Discard the cached index."""
        self._index = None

    def refresh(self) -> None:
        """Fetch the latest index immediately."""
        self._index = self._fetch_index()

    def _ensure_index(self) -> RemotePackIndex:
        if self._index is None or self._is_stale(self._index):
            self._index = self._fetch_index()
        return self._index

    def _is_stale(self, index: RemotePackIndex) -> bool:
        return datetime.now(UTC) - index.fetched_at > timedelta(
            seconds=self._config.cache_ttl_seconds
        )

    def _fetch_index(self) -> RemotePackIndex:
        payload = self._read_json(self._config.index_url)
        packs: list[MarketplacePackRecord] = []
        raw_packs = payload.get("packs", [])
        if not isinstance(raw_packs, list):
            raw_packs = []

        for item in raw_packs:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            if not name:
                continue
            versions: list[MarketplacePackVersion] = []
            raw_versions = item.get("versions", [])
            if not isinstance(raw_versions, list):
                raw_versions = []
            for raw_version in raw_versions:
                if not isinstance(raw_version, dict):
                    continue
                version = str(raw_version.get("version", "")).strip()
                download_url = str(raw_version.get("download_url", "")).strip()
                if not version or not download_url:
                    continue
                try:
                    Version.parse(version)
                except ValueError:
                    continue
                provenance = None
                raw_provenance = raw_version.get("provenance")
                if isinstance(raw_provenance, dict):
                    try:
                        provenance = PackProvenance.model_validate(raw_provenance)
                    except Exception:
                        provenance = None
                raw_tags = raw_version.get("tags", item.get("tags", []))
                if not isinstance(raw_tags, list):
                    raw_tags = []
                versions.append(
                    MarketplacePackVersion(
                        version=version,
                        description=str(
                            raw_version.get("description", item.get("description", ""))
                        ),
                        author=str(raw_version.get("author", item.get("author", ""))),
                        tags=[str(tag) for tag in raw_tags],
                        category=str(raw_version.get("category", item.get("category", ""))),
                        skills_count=int(raw_version.get("skills_count", 0)),
                        source_name=self.source_name,
                        source_type="remote",
                        trust_level=(
                            provenance.trust_level if provenance else self._config.trust_level
                        ),
                        download_url=download_url,
                        provenance=provenance,
                    )
                )

            if not versions:
                continue

            ordered = sorted(
                versions,
                key=lambda pack_version: Version.parse(pack_version.version),
                reverse=True,
            )
            latest = ordered[0]
            packs.append(
                MarketplacePackRecord(
                    name=name,
                    description=str(item.get("description", latest.description)),
                    author=str(item.get("author", latest.author)),
                    tags=[str(tag) for tag in item.get("tags", latest.tags)],
                    category=str(item.get("category", latest.category)),
                    latest_version=latest.version,
                    versions=ordered,
                )
            )

        return RemotePackIndex(
            source=self.source_name,
            packs=sorted(packs, key=lambda record: record.name),
        )

    def list_packs(self) -> list[MarketplacePackRecord]:
        return list(self._ensure_index().packs)

    def search(self, query: str) -> list[MarketplacePackRecord]:
        query_lower = query.lower()
        return [
            record
            for record in self.list_packs()
            if query_lower in record.name.lower()
            or query_lower in record.description.lower()
            or any(query_lower in tag.lower() for tag in record.tags)
        ]

    def get_pack(self, name: str) -> MarketplacePackRecord | None:
        for record in self.list_packs():
            if record.name == name:
                return record
        return None

    def list_versions(self, name: str) -> list[MarketplacePackVersion]:
        record = self.get_pack(name)
        if record is None:
            return []
        return list(record.versions)

    def resolve(self, name: str, version: str = "") -> MarketplaceResolvedPack | None:
        versions = self.list_versions(name)
        if not versions:
            return None
        selected = (
            versions[0]
            if not version
            else next(
                (item for item in versions if item.version == version),
                None,
            )
        )
        if selected is None:
            return None
        pack_dir = self._download_and_extract(name, selected)
        return MarketplaceResolvedPack(
            pack_dir=pack_dir,
            version=selected.version,
            source_name=selected.source_name,
            source_type=selected.source_type,
            provenance=selected.provenance,
        )

    def _download_and_extract(self, name: str, version: MarketplacePackVersion) -> Path:
        target_dir = self._cache_dir / name / version.version
        manifest_path = target_dir / "PACK.yaml"
        if not manifest_path.is_file():
            manifest_path = target_dir / "pack.yaml"
        if manifest_path.is_file():
            return target_dir

        self._cache_dir.mkdir(parents=True, exist_ok=True)
        archive_path = target_dir.with_suffix(".zip")
        if archive_path.exists():
            archive_path.unlink()
        if target_dir.exists():
            shutil.rmtree(target_dir)

        self._download_file(version.download_url, archive_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(target_dir)
        archive_path.unlink(missing_ok=True)

        nested_manifest = next(
            (path.parent for path in target_dir.rglob("PACK.yaml")),
            None,
        ) or next((path.parent for path in target_dir.rglob("pack.yaml")), None)
        if nested_manifest is not None and nested_manifest != target_dir:
            temp_dir = target_dir.with_name(f"{target_dir.name}-tmp")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            nested_manifest.replace(temp_dir)
            shutil.rmtree(target_dir)
            temp_dir.replace(target_dir)

        manifest_path = target_dir / "PACK.yaml"
        if not manifest_path.is_file():
            manifest_path = target_dir / "pack.yaml"
        if not manifest_path.is_file():
            raise ValueError(
                f"Downloaded archive for '{name}' {version.version} did not contain PACK.yaml"
            )
        return target_dir

    def _read_json(self, url: str) -> dict[str, object]:
        parsed = urlparse(url)
        if parsed.scheme in ("", "file"):
            path = self._path_from_url(url)
            return cast("dict[str, object]", json.loads(path.read_text(encoding="utf-8")))
        headers = (
            {"Authorization": f"Bearer {self._config.auth_token}"}
            if self._config.auth_token
            else None
        )
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            return cast("dict[str, object]", response.json())

    def _download_file(self, url: str, destination: Path) -> None:
        parsed = urlparse(url)
        if parsed.scheme in ("", "file"):
            source_path = self._path_from_url(url)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_path, destination)
            return
        headers = (
            {"Authorization": f"Bearer {self._config.auth_token}"}
            if self._config.auth_token
            else None
        )
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(response.content)

    @staticmethod
    def _path_from_url(url: str) -> Path:
        parsed = urlparse(url)
        if parsed.scheme == "file":
            return Path(url2pathname(parsed.path))
        return Path(url)
