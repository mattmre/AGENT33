"""Read-only restore planning for platform backup archives."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from agent33.backup.service import BackupService, _compute_checksum

if TYPE_CHECKING:
    from pathlib import Path

    from agent33.backup.manifest import BackupAsset


class RestoreAssetPlan(BaseModel):
    """Preview of the action for one backed-up asset."""

    relative_path: str
    asset_type: str
    action: str
    current_exists: bool
    size_bytes: int = 0


class RestoreConflict(BaseModel):
    """Conflict that would need operator review before restore execution."""

    relative_path: str
    conflict_type: str
    message: str
    resolution: str


class RestorePlan(BaseModel):
    """Read-only preview of a potential restore."""

    backup_id: str
    backup_version: str
    current_version: str
    assets_to_restore: list[RestoreAssetPlan] = Field(default_factory=list)
    conflicts: list[RestoreConflict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    estimated_duration: str = ""


class RestorePlanningError(RuntimeError):
    """Raised when a restore plan cannot be generated safely."""


class RestorePlanner:
    """Generate a restore plan from a verified backup archive."""

    def __init__(self, backup_service: BackupService) -> None:
        self._backup_service = backup_service

    async def plan(self, backup_id: str, archive_path: Path) -> RestorePlan:
        """Build a read-only restore plan for a backup."""
        verify_result = await self._backup_service.verify(archive_path)
        if not verify_result.valid:
            failed = [check.message for check in verify_result.checks if not check.passed]
            raise RestorePlanningError(
                "Backup verification failed before restore planning: " + "; ".join(failed)
            )

        manifest = self._backup_service.load_manifest(archive_path)
        conflicts: list[RestoreConflict] = []
        asset_plans: list[RestoreAssetPlan] = []
        actionable_bytes = 0

        if manifest.runtime_version != self._backup_service.runtime_version:
            conflicts.append(
                RestoreConflict(
                    relative_path="",
                    conflict_type="version_mismatch",
                    message=(
                        f"Backup runtime version {manifest.runtime_version} differs from "
                        f"current runtime version {self._backup_service.runtime_version}"
                    ),
                    resolution="review",
                )
            )

        for asset in manifest.assets:
            if not asset.included:
                continue
            plan, asset_conflicts = self._plan_asset(asset)
            asset_plans.append(plan)
            conflicts.extend(asset_conflicts)
            if plan.action != "skip":
                actionable_bytes += asset.size_bytes

        warnings = [
            "Restore execution is not implemented in Track 6B; this plan is read-only.",
            "Create a fresh backup immediately before any future destructive restore attempt.",
            *verify_result.warnings,
        ]
        return RestorePlan(
            backup_id=backup_id,
            backup_version=manifest.runtime_version,
            current_version=self._backup_service.runtime_version,
            assets_to_restore=asset_plans,
            conflicts=conflicts,
            warnings=warnings,
            estimated_duration=_estimate_duration(actionable_bytes),
        )

    def _plan_asset(self, asset: BackupAsset) -> tuple[RestoreAssetPlan, list[RestoreConflict]]:
        target_path = self._backup_service.resolve_target_path(asset.relative_path)
        if target_path is None:
            return (
                RestoreAssetPlan(
                    relative_path=asset.relative_path,
                    asset_type=asset.asset_type,
                    action="skip",
                    current_exists=False,
                    size_bytes=asset.size_bytes,
                ),
                [
                    RestoreConflict(
                        relative_path=asset.relative_path,
                        conflict_type="unmapped_asset",
                        message="No live target is mapped for this backup asset.",
                        resolution="skip",
                    )
                ],
            )

        current_exists = target_path.exists()
        if not current_exists:
            return (
                RestoreAssetPlan(
                    relative_path=asset.relative_path,
                    asset_type=asset.asset_type,
                    action="create",
                    current_exists=False,
                    size_bytes=asset.size_bytes,
                ),
                [],
            )

        conflicts: list[RestoreConflict] = []
        current_type_is_dir = target_path.is_dir()
        if current_type_is_dir != asset.is_directory:
            conflicts.append(
                RestoreConflict(
                    relative_path=asset.relative_path,
                    conflict_type="schema_change",
                    message="Current filesystem entry type differs from the backup asset type.",
                    resolution="overwrite",
                )
            )
            return (
                RestoreAssetPlan(
                    relative_path=asset.relative_path,
                    asset_type=asset.asset_type,
                    action="overwrite",
                    current_exists=True,
                    size_bytes=asset.size_bytes,
                ),
                conflicts,
            )

        try:
            current_checksum = _compute_checksum(target_path)
        except OSError as exc:
            raise RestorePlanningError(
                f"Failed to inspect current asset {asset.relative_path}: {exc}"
            ) from exc
        if current_checksum == asset.checksum:
            return (
                RestoreAssetPlan(
                    relative_path=asset.relative_path,
                    asset_type=asset.asset_type,
                    action="skip",
                    current_exists=True,
                    size_bytes=asset.size_bytes,
                ),
                [],
            )

        conflicts.append(
            RestoreConflict(
                relative_path=asset.relative_path,
                conflict_type="file_modified",
                message="Current asset contents differ from the backup snapshot.",
                resolution="overwrite",
            )
        )
        return (
            RestoreAssetPlan(
                relative_path=asset.relative_path,
                asset_type=asset.asset_type,
                action="overwrite",
                current_exists=True,
                size_bytes=asset.size_bytes,
            ),
            conflicts,
        )


def _estimate_duration(total_bytes: int) -> str:
    """Return a coarse restore duration estimate."""
    if total_bytes <= 0:
        return "No restore actions needed"
    if total_bytes < 1_000_000:
        return "Under 1 minute"
    if total_bytes < 100_000_000:
        return "1-2 minutes"
    return "Several minutes"
