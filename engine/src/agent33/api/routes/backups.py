"""FastAPI routes for platform backup management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from agent33.backup.manifest import (
    BackupDetailResponse,
    BackupInventoryResponse,
    BackupListResponse,
    BackupMode,
    BackupResult,
    VerifyResult,
)
from agent33.backup.service import BackupService
from agent33.security.permissions import require_scope

router = APIRouter(prefix="/v1/backups", tags=["backups"])


class CreateBackupRequest(BaseModel):
    """Request body for backup archive creation."""

    mode: BackupMode = BackupMode.FULL
    label: str = ""


def get_backup_service(request: Request) -> BackupService:
    """Return the app-scoped backup service."""
    svc: BackupService | None = getattr(request.app.state, "backup_service", None)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backup service not initialized",
        )
    return svc


BackupServiceDependency = Annotated[BackupService, Depends(get_backup_service)]


def _requested_by(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        return ""
    return getattr(user, "sub", "") or ""


@router.get(
    "",
    response_model=BackupListResponse,
    dependencies=[require_scope("operator:read")],
)
async def list_backups(svc: BackupServiceDependency) -> BackupListResponse:
    """List available backup archives."""
    return svc.list_backups()


@router.get(
    "/inventory",
    response_model=BackupInventoryResponse,
    dependencies=[require_scope("operator:read")],
)
async def get_backup_inventory(
    svc: BackupServiceDependency,
    mode: BackupMode = BackupMode.FULL,
) -> BackupInventoryResponse:
    """Preview the assets that would be included in a backup."""
    return svc.inventory(mode=mode)


@router.post(
    "",
    response_model=BackupResult,
    dependencies=[require_scope("operator:write")],
)
async def create_backup(
    request: Request,
    body: CreateBackupRequest,
    svc: BackupServiceDependency,
) -> BackupResult:
    """Create a new platform backup archive."""
    return await svc.create(
        mode=body.mode,
        label=body.label,
        creator=_requested_by(request),
    )


@router.get(
    "/{backup_id}",
    response_model=BackupDetailResponse,
    dependencies=[require_scope("operator:read")],
)
async def get_backup_detail(
    backup_id: str,
    svc: BackupServiceDependency,
) -> BackupDetailResponse:
    """Return one backup manifest and summary."""
    detail = svc.get_backup_detail(backup_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Backup not found")
    return detail


@router.post(
    "/{backup_id}/verify",
    response_model=VerifyResult,
    dependencies=[require_scope("operator:read")],
)
async def verify_backup(
    backup_id: str,
    svc: BackupServiceDependency,
) -> VerifyResult:
    """Verify an existing backup archive."""
    archive_path = svc.resolve_backup_path(backup_id)
    if archive_path is None:
        raise HTTPException(status_code=404, detail="Backup not found")
    return await svc.verify(archive_path)
