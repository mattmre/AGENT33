"""Pack registry: discover, install, uninstall, enable/disable, search.

The PackRegistry manages installed skill packs and their lifecycle.
It sits between the filesystem (where packs are stored) and the
SkillRegistry (where individual skills are registered).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import structlog

from agent33.packs.loader import (
    compute_pack_checksum,
    load_pack_manifest,
    load_pack_skills,
    validate_pack_directory,
    verify_checksums,
)
from agent33.packs.models import (
    InstalledPack,
    InstallResult,
    PackStatus,
)

if TYPE_CHECKING:
    from pathlib import Path

    from agent33.packs.models import PackSource
    from agent33.skills.definition import SkillDefinition
    from agent33.skills.registry import SkillRegistry

logger = structlog.get_logger()


class PackRegistry:
    """Manages installed skill packs and their lifecycle.

    Pack skills are registered in the existing SkillRegistry using
    qualified names: ``{pack_name}/{skill_name}`` plus an alias
    for the bare skill name (for backward compatibility).
    """

    def __init__(
        self,
        packs_dir: Path,
        skill_registry: SkillRegistry,
    ) -> None:
        self._packs_dir = packs_dir
        self._skill_registry = skill_registry
        self._installed: dict[str, InstalledPack] = {}
        self._enabled: dict[str, set[str]] = {}  # tenant_id -> set of enabled pack names

    # ------------------------------------------------------------------
    # Discovery & Loading
    # ------------------------------------------------------------------

    def discover(self, path: Path | None = None) -> int:
        """Scan a directory for PACK.yaml manifests.

        Each subdirectory containing a PACK.yaml is loaded as a pack.
        Returns the number of packs successfully loaded.
        """
        scan_dir = path or self._packs_dir
        if not scan_dir.is_dir():
            logger.warning("pack_directory_not_found", path=str(scan_dir))
            return 0

        loaded = 0
        for entry in sorted(scan_dir.iterdir()):
            if not entry.is_dir():
                continue

            manifest_path = entry / "PACK.yaml"
            if not manifest_path.is_file():
                manifest_path = entry / "pack.yaml"
                if not manifest_path.is_file():
                    continue

            try:
                pack = self.load_pack(entry)
                self._installed[pack.name] = pack
                loaded += 1
                logger.info(
                    "pack_discovered",
                    name=pack.name,
                    version=pack.version,
                    skills=len(pack.loaded_skill_names),
                )
            except Exception:
                logger.warning("pack_discovery_failed", path=str(entry), exc_info=True)

        return loaded

    def load_pack(self, pack_dir: Path) -> InstalledPack:
        """Load a single pack from a directory containing PACK.yaml.

        Validates the manifest, loads each skill definition via the existing
        loader module, and returns an InstalledPack.

        Raises:
            FileNotFoundError: If PACK.yaml is not found.
            ValueError: If validation fails or required skills cannot load.
        """
        manifest = load_pack_manifest(pack_dir)

        # Verify checksums if present
        checksums_ok, mismatches = verify_checksums(pack_dir)
        if not checksums_ok:
            raise ValueError(
                f"Checksum verification failed for pack '{manifest.name}': "
                + "; ".join(mismatches)
            )

        # Load skills
        skills, errors = load_pack_skills(pack_dir, manifest)
        if errors:
            raise ValueError(
                f"Failed to load required skills for pack '{manifest.name}': "
                + "; ".join(errors)
            )

        # Register skills in SkillRegistry
        loaded_names = self._register_pack_skills(manifest.name, skills)

        # Build InstalledPack

        installed = InstalledPack(
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            license=manifest.license,
            tags=manifest.tags,
            category=manifest.category,
            skills=manifest.skills,
            loaded_skill_names=loaded_names,
            pack_dependencies=manifest.dependencies.packs,
            engine_min_version=manifest.dependencies.engine.get("min_version", ""),
            compatibility=manifest.compatibility,
            installed_at=datetime.now(UTC),
            source="local",
            checksum=compute_pack_checksum(pack_dir),
            pack_dir=pack_dir,
            governance=manifest.governance,
            status=PackStatus.INSTALLED,
        )

        return installed

    def _register_pack_skills(
        self, pack_name: str, skills: list[SkillDefinition]
    ) -> list[str]:
        """Register loaded skills in the SkillRegistry.

        Skills are registered with qualified name ``pack_name/skill_name``
        and also with bare ``skill_name`` as an alias (if not already taken).

        Returns the list of registered qualified names.
        """
        registered: list[str] = []
        for skill in skills:
            # Qualified name: pack_name/skill_name
            qualified_name = f"{pack_name}/{skill.name}"
            qualified_skill = skill.model_copy(update={"name": qualified_name})
            self._skill_registry.register(qualified_skill)
            registered.append(qualified_name)

            # Bare alias (if slot not taken by another pack or standalone skill)
            existing = self._skill_registry.get(skill.name)
            if existing is None:
                self._skill_registry.register(skill)

        return registered

    def _unregister_pack_skills(self, pack: InstalledPack) -> None:
        """Remove pack skills from the SkillRegistry."""
        for qualified_name in pack.loaded_skill_names:
            self._skill_registry.remove(qualified_name)

        # Also remove bare aliases if they belong to this pack
        for skill_entry in pack.skills:
            existing = self._skill_registry.get(skill_entry.name)
            if existing is not None and existing.base_path and pack.pack_dir:
                    try:
                        existing.base_path.resolve().relative_to(pack.pack_dir.resolve())
                        self._skill_registry.remove(skill_entry.name)
                    except ValueError:
                        pass  # Skill belongs to a different source

    # ------------------------------------------------------------------
    # Installation
    # ------------------------------------------------------------------

    def install(self, source: PackSource) -> InstallResult:
        """Install a pack from a local path.

        Steps:
        1. Validate the directory
        2. Parse and validate PACK.yaml
        3. Verify checksums (if CHECKSUMS.sha256 present)
        4. Load skills into SkillRegistry
        5. Register in installed packs

        Marketplace sources are not yet supported.
        """
        from pathlib import Path as _Path

        if source.source_type != "local":
            return InstallResult(
                success=False,
                pack_name=source.name or "unknown",
                errors=[f"Unsupported source type: {source.source_type}"],
            )

        pack_path = _Path(source.path)
        if not pack_path.is_dir():
            return InstallResult(
                success=False,
                pack_name=source.name or "unknown",
                errors=[f"Pack directory not found: {source.path}"],
            )

        # Validate structure
        validation_errors = validate_pack_directory(pack_path)
        if validation_errors:
            return InstallResult(
                success=False,
                pack_name=source.name or "unknown",
                errors=validation_errors,
            )

        try:
            pack = self.load_pack(pack_path)
        except (FileNotFoundError, ValueError) as exc:
            return InstallResult(
                success=False,
                pack_name=source.name or "unknown",
                errors=[str(exc)],
            )

        # Check if already installed
        if pack.name in self._installed:
            existing = self._installed[pack.name]
            return InstallResult(
                success=False,
                pack_name=pack.name,
                version=existing.version,
                errors=[
                    f"Pack '{pack.name}' is already installed at version {existing.version}. "
                    f"Use upgrade to change versions."
                ],
            )

        self._installed[pack.name] = pack

        return InstallResult(
            success=True,
            pack_name=pack.name,
            version=pack.version,
            skills_loaded=len(pack.loaded_skill_names),
        )

    def uninstall(self, name: str) -> bool:
        """Uninstall a pack.

        Checks that no other installed pack depends on this one before
        removing. Returns True if successfully uninstalled.

        Raises:
            ValueError: If pack is not installed or has dependents.
        """
        pack = self._installed.get(name)
        if pack is None:
            raise ValueError(f"Pack '{name}' is not installed")

        # Check for dependents
        dependents = self._find_dependents(name)
        if dependents:
            raise ValueError(
                f"Cannot uninstall '{name}': required by {', '.join(dependents)}"
            )

        # Remove skills from SkillRegistry
        self._unregister_pack_skills(pack)

        # Remove from installed dict
        del self._installed[name]

        # Remove from all tenant enablement sets
        for tenant_set in self._enabled.values():
            tenant_set.discard(name)

        logger.info("pack_uninstalled", name=name, version=pack.version)
        return True

    def _find_dependents(self, name: str) -> list[str]:
        """Find installed packs that depend on the named pack."""
        dependents: list[str] = []
        for pack_name, pack in self._installed.items():
            if pack_name == name:
                continue
            for dep in pack.pack_dependencies:
                if dep.name == name:
                    dependents.append(pack_name)
                    break
        return dependents

    # ------------------------------------------------------------------
    # Enable/Disable (tenant-scoped)
    # ------------------------------------------------------------------

    def enable(self, name: str, tenant_id: str) -> bool:
        """Enable a pack for a specific tenant.

        Returns True if the pack was enabled (or was already enabled).
        Raises ValueError if the pack is not installed.
        """
        if name not in self._installed:
            raise ValueError(f"Pack '{name}' is not installed")

        if tenant_id not in self._enabled:
            self._enabled[tenant_id] = set()

        self._enabled[tenant_id].add(name)
        logger.info("pack_enabled", name=name, tenant_id=tenant_id)
        return True

    def disable(self, name: str, tenant_id: str) -> bool:
        """Disable a pack for a specific tenant.

        Returns True if the pack was disabled (or was already disabled).
        Raises ValueError if the pack is not installed.
        """
        if name not in self._installed:
            raise ValueError(f"Pack '{name}' is not installed")

        if tenant_id in self._enabled:
            self._enabled[tenant_id].discard(name)

        logger.info("pack_disabled", name=name, tenant_id=tenant_id)
        return True

    def is_enabled(self, name: str, tenant_id: str) -> bool:
        """Check if a pack is enabled for a tenant."""
        return name in self._enabled.get(tenant_id, set())

    def list_enabled(self, tenant_id: str) -> list[InstalledPack]:
        """List all packs enabled for a tenant."""
        enabled_names = self._enabled.get(tenant_id, set())
        return [
            self._installed[name]
            for name in sorted(enabled_names)
            if name in self._installed
        ]

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get(self, name: str) -> InstalledPack | None:
        """Look up an installed pack by name."""
        return self._installed.get(name)

    def list_installed(self) -> list[InstalledPack]:
        """List all installed packs sorted by name."""
        return [self._installed[k] for k in sorted(self._installed)]

    @property
    def count(self) -> int:
        """Number of installed packs."""
        return len(self._installed)

    def search(self, query: str) -> list[InstalledPack]:
        """Search installed packs by name, description, or tags."""
        query_lower = query.lower()
        results: list[InstalledPack] = []
        for pack in self._installed.values():
            if (
                query_lower in pack.name.lower()
                or query_lower in pack.description.lower()
                or any(query_lower in t.lower() for t in pack.tags)
            ):
                results.append(pack)
        return sorted(results, key=lambda p: p.name)

    # ------------------------------------------------------------------
    # Upgrade / Downgrade
    # ------------------------------------------------------------------

    def upgrade(
        self, name: str, new_pack_dir: Path, target_version: str | None = None
    ) -> InstallResult:
        """Upgrade a pack to a newer version from a new directory.

        This unloads old skills, loads the new pack, and re-registers skills.
        Tenant enablement is preserved.
        """
        old_pack = self._installed.get(name)
        if old_pack is None:
            return InstallResult(
                success=False,
                pack_name=name,
                errors=[f"Pack '{name}' is not installed"],
            )

        try:
            new_pack = self.load_pack(new_pack_dir)
        except (FileNotFoundError, ValueError) as exc:
            return InstallResult(
                success=False,
                pack_name=name,
                errors=[str(exc)],
            )

        if new_pack.name != name:
            return InstallResult(
                success=False,
                pack_name=name,
                errors=[
                    f"Pack name mismatch: expected '{name}' but found '{new_pack.name}'"
                ],
            )

        if target_version and new_pack.version != target_version:
            return InstallResult(
                success=False,
                pack_name=name,
                errors=[
                    f"Version mismatch: expected '{target_version}' "
                    f"but pack is '{new_pack.version}'"
                ],
            )

        # Unload old skills
        self._unregister_pack_skills(old_pack)

        # Install new version
        self._installed[name] = new_pack

        logger.info(
            "pack_upgraded",
            name=name,
            old_version=old_pack.version,
            new_version=new_pack.version,
        )

        return InstallResult(
            success=True,
            pack_name=name,
            version=new_pack.version,
            skills_loaded=len(new_pack.loaded_skill_names),
        )

    def downgrade(self, name: str, old_pack_dir: Path) -> InstallResult:
        """Downgrade a pack to an older version from a directory.

        Functionally identical to upgrade but semantically signals intent.
        """
        return self.upgrade(name, old_pack_dir)
