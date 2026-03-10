"""Operator control plane API routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request, status

from agent33.operator.models import (
    BackupListResponse,
    DiagnosticResult,
    OperatorConfig,
    ResetRequest,
    ResetResult,
    SessionListResponse,
    SystemStatus,
    ToolSummaryResponse,
)
from agent33.security.permissions import require_scope

if TYPE_CHECKING:
    from agent33.operator.service import OperatorService

router = APIRouter(prefix="/v1/operator", tags=["operator"])


def _get_operator_service(request: Request) -> OperatorService:
    """Extract the OperatorService from app.state."""
    svc: OperatorService | None = getattr(request.app.state, "operator_service", None)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operator service not initialized",
        )
    return svc


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


@router.get(
    "/status",
    response_model=SystemStatus,
    dependencies=[require_scope("operator:read")],
)
async def operator_status(request: Request) -> SystemStatus:
    """Aggregated system health, subsystem inventories, and runtime info."""
    svc = _get_operator_service(request)
    return await svc.get_status()


# ---------------------------------------------------------------------------
# Config (redacted)
# ---------------------------------------------------------------------------


@router.get(
    "/config",
    response_model=OperatorConfig,
    dependencies=[require_scope("operator:read")],
)
async def operator_config(request: Request) -> OperatorConfig:
    """Effective runtime configuration with secrets redacted."""
    svc = _get_operator_service(request)
    return svc.get_config()


# ---------------------------------------------------------------------------
# Doctor (diagnostics)
# ---------------------------------------------------------------------------


@router.get(
    "/doctor",
    response_model=DiagnosticResult,
    dependencies=[require_scope("operator:read")],
)
async def operator_doctor(request: Request) -> DiagnosticResult:
    """Run diagnostic checks and return results with severity and remediation."""
    svc = _get_operator_service(request)
    return await svc.run_doctor()


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


@router.post(
    "/reset",
    response_model=ResetResult,
    dependencies=[require_scope("operator:write")],
)
async def operator_reset(request: Request, body: ResetRequest) -> ResetResult:
    """Reset specified operator state (clear caches, re-discover registries)."""
    svc = _get_operator_service(request)
    return await svc.reset(body.targets)


# ---------------------------------------------------------------------------
# Tools summary
# ---------------------------------------------------------------------------


@router.get(
    "/tools/summary",
    response_model=ToolSummaryResponse,
    dependencies=[require_scope("operator:read")],
)
async def operator_tools_summary(request: Request) -> ToolSummaryResponse:
    """Lightweight listing of registered tools."""
    svc = _get_operator_service(request)
    return svc.get_tools_summary()


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    dependencies=[require_scope("operator:read")],
)
async def operator_sessions(
    request: Request,
    status_filter: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> SessionListResponse:
    """Session catalog (lightweight, full management in Track Phase 8)."""
    svc = _get_operator_service(request)
    return await svc.get_sessions(
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# Backups (skeleton)
# ---------------------------------------------------------------------------


@router.get(
    "/backups",
    response_model=BackupListResponse,
    dependencies=[require_scope("operator:read")],
)
async def operator_backups(request: Request) -> BackupListResponse:
    """Backup catalog (skeleton until Track Phase 6)."""
    svc = _get_operator_service(request)
    return svc.get_backups()
