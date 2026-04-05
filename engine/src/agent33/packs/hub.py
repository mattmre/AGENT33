"""Pack Hub: lightweight registry client for browsing and downloading packs.

The hub reads a JSON registry (either from a remote URL or a local cache file)
and provides search, lookup, and download capabilities.  When the remote
registry is unreachable the hub degrades gracefully to the local cache and
never raises network errors to the caller.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class PackHubConfig(BaseModel):
    """Configuration for the pack hub client."""

    registry_url: str = (
        "https://raw.githubusercontent.com/mattmre/agent33-pack-registry/main/registry.json"
    )
    cache_ttl_seconds: int = 3600
    local_cache_path: Path = Field(
        default_factory=lambda: Path.home() / ".agent33" / "pack_cache.json"
    )


class PackHubEntry(BaseModel):
    """A single pack entry in the community registry."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    download_url: str = ""
    sha256: str = ""  # hex digest for integrity check
    install_count: int = 0
    rating: float = 0.0  # 0.0-5.0


class PackRegistryPayload(BaseModel):
    """Top-level schema of the remote registry JSON."""

    schema_version: str = "1"
    updated_at: str = ""
    packs: list[PackHubEntry] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Hub client
# ---------------------------------------------------------------------------


class PackHub:
    """Client for browsing and downloading packs from the community registry."""

    def __init__(self, config: PackHubConfig | None = None) -> None:
        self._config = config or PackHubConfig()
        self._cache: list[PackHubEntry] = []
        self._cache_loaded_at: float = 0.0

    # -- Public API ---------------------------------------------------------

    async def search(
        self,
        query: str,
        tags: list[str] | None = None,
        limit: int = 10,
    ) -> list[PackHubEntry]:
        """Search the registry by name/description/tags.

        Returns up to *limit* matching entries.  If the cache is stale a
        background refresh is attempted; on failure the stale cache is used.
        Never raises on network errors.
        """
        await self._ensure_cache()
        query_lower = query.lower()
        results: list[PackHubEntry] = []

        for entry in self._cache:
            if self._matches(entry, query_lower, tags):
                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    async def get(self, name: str) -> PackHubEntry | None:
        """Look up a single pack by exact name."""
        await self._ensure_cache()
        for entry in self._cache:
            if entry.name == name:
                return entry
        return None

    async def download(self, entry: PackHubEntry, dest_dir: Path) -> Path:
        """Download a pack YAML to *dest_dir* and verify its sha256.

        Raises:
            ValueError: If the download URL is empty, the sha256 doesn't
                match, or the download fails.
        """
        if not entry.download_url:
            raise ValueError(f"Pack '{entry.name}' has no download URL")

        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{entry.name}.yaml"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(entry.download_url)
                resp.raise_for_status()
                content = resp.content
        except Exception as exc:
            raise ValueError(
                f"Failed to download pack '{entry.name}' from {entry.download_url}: {exc}"
            ) from exc

        # Verify sha256
        if entry.sha256:
            actual = hashlib.sha256(content).hexdigest()
            if actual != entry.sha256:
                raise ValueError(
                    f"SHA-256 mismatch for pack '{entry.name}': "
                    f"expected {entry.sha256[:16]}..., got {actual[:16]}..."
                )

        dest_path.write_bytes(content)
        logger.info(
            "pack_hub_downloaded",
            name=entry.name,
            version=entry.version,
            dest=str(dest_path),
        )
        return dest_path

    async def refresh_cache(self) -> None:
        """Fetch the remote registry JSON and save to local cache.

        Silently logs and returns on network errors (never raises).
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(self._config.registry_url)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning(
                "pack_hub_refresh_failed",
                url=self._config.registry_url,
                error=str(exc),
            )
            return

        try:
            payload = PackRegistryPayload.model_validate(data)
        except Exception as exc:
            logger.warning("pack_hub_invalid_payload", error=str(exc))
            return

        self._cache = payload.packs
        self._cache_loaded_at = time.monotonic()

        # Persist to disk
        try:
            self._config.local_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._config.local_cache_path.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8",
            )
            logger.info(
                "pack_hub_cache_saved",
                path=str(self._config.local_cache_path),
                pack_count=len(self._cache),
            )
        except OSError as exc:
            logger.warning(
                "pack_hub_cache_write_failed",
                path=str(self._config.local_cache_path),
                error=str(exc),
            )

    def list_cached(self) -> list[PackHubEntry]:
        """Return entries from the in-memory cache without a network call.

        If the in-memory cache is empty, attempts to load from the local
        cache file on disk.
        """
        if not self._cache:
            self._load_disk_cache()
        return list(self._cache)

    # -- Internal -----------------------------------------------------------

    async def _ensure_cache(self) -> None:
        """Populate the cache if empty or stale."""
        now = time.monotonic()
        if self._cache and (now - self._cache_loaded_at) < self._config.cache_ttl_seconds:
            return  # fresh enough

        # Try disk cache first
        if not self._cache:
            self._load_disk_cache()

        # Attempt remote refresh (best-effort)
        await self.refresh_cache()

    def _load_disk_cache(self) -> None:
        """Load the local cache JSON from disk."""
        cache_path = self._config.local_cache_path
        if not cache_path.is_file():
            return

        try:
            raw = cache_path.read_text(encoding="utf-8")
            data: dict[str, Any] = json.loads(raw)
            payload = PackRegistryPayload.model_validate(data)
            self._cache = payload.packs
            self._cache_loaded_at = time.monotonic()
            logger.debug(
                "pack_hub_disk_cache_loaded",
                path=str(cache_path),
                pack_count=len(self._cache),
            )
        except Exception as exc:
            logger.warning(
                "pack_hub_disk_cache_load_failed",
                path=str(cache_path),
                error=str(exc),
            )

    @staticmethod
    def _matches(
        entry: PackHubEntry,
        query_lower: str,
        tags: list[str] | None,
    ) -> bool:
        """Check whether an entry matches the search criteria."""
        text_match = (
            query_lower in entry.name.lower()
            or query_lower in entry.description.lower()
            or any(query_lower in t.lower() for t in entry.tags)
        )
        if not text_match:
            return False

        if tags:
            entry_tags_lower = {t.lower() for t in entry.tags}
            if not all(t.lower() in entry_tags_lower for t in tags):
                return False

        return True
