"""FastAPI router for component security scan runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agent33.component_security.models import (
    FindingSeverity,
    RunStatus,
    ScanOptions,
    ScanTarget,
    SecurityProfile,
)
from agent33.security.permissions import require_scope
from agent33.services.pentagi_integration import (
    PentAGIService,
    PentAGIServiceError,
    RunNotFoundError,
    RunStateError,
)

router = APIRouter(prefix="/v1/component-security", tags=["component-security"])
_WORKSPACE_ROOT = Path(__file__).resolve().parents[5]
_service = PentAGIService(allowed_roots=[str(_WORKSPACE_ROOT)])


def get_component_security_service() -> PentAGIService:
    """Return singleton component security service."""
    return _service


def _tenant_id(request: Request) -> str:
    """Extract tenant ID from authenticated principal."""
    user = getattr(request.state, "user", None)
    if user is None:
        return ""
    return getattr(user, "tenant_id", "")


class CreateSecurityRunRequest(BaseModel):
    """Request payload for creating a component security run."""

    target: ScanTarget
    profile: SecurityProfile = SecurityProfile.QUICK
    options: ScanOptions = Field(default_factory=ScanOptions)
    requested_by: str = ""
    session_id: str = ""
    release_candidate_id: str = ""
    execute_now: bool = True


@router.post("/runs", status_code=201, dependencies=[require_scope("component-security:write")])
async def create_run(body: CreateSecurityRunRequest, request: Request) -> dict[str, Any]:
    """Create a new component security run and optionally execute it immediately."""
    run = _service.create_run(
        target=body.target,
        profile=body.profile,
        options=body.options,
        tenant_id=_tenant_id(request),
        requested_by=body.requested_by,
        session_id=body.session_id,
        release_candidate_id=body.release_candidate_id,
    )
    if body.execute_now:
        try:
            run = _service.launch_scan(run.id, tenant_id=_tenant_id(request))
        except PentAGIServiceError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    return run.model_dump(mode="json")


@router.get("/runs", dependencies=[require_scope("component-security:read")])
async def list_runs(
    request: Request,
    status: RunStatus | None = None,
    profile: SecurityProfile | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """List component security runs for current tenant."""
    tenant_id = _tenant_id(request)
    runs = _service.list_runs(
        tenant_id=tenant_id if tenant_id else None,
        status=status,
        profile=profile,
        limit=limit,
    )
    return [run.model_dump(mode="json") for run in runs]


@router.get("/runs/{run_id}", dependencies=[require_scope("component-security:read")])
async def get_run(run_id: str, request: Request) -> dict[str, Any]:
    """Get component security run details by ID."""
    try:
        run = _service.get_run(run_id, tenant_id=_tenant_id(request) or None)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return run.model_dump(mode="json")


@router.get("/runs/{run_id}/findings", dependencies=[require_scope("component-security:read")])
async def get_findings(
    run_id: str,
    request: Request,
    min_severity: FindingSeverity | None = None,
) -> dict[str, Any]:
    """Fetch findings for a run."""
    try:
        findings = _service.fetch_findings(
            run_id,
            tenant_id=_tenant_id(request) or None,
            min_severity=min_severity,
        )
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "findings": [finding.model_dump(mode="json") for finding in findings],
        "total_count": len(findings),
    }


@router.post("/runs/{run_id}/cancel", dependencies=[require_scope("component-security:write")])
async def cancel_run(run_id: str, request: Request) -> dict[str, Any]:
    """Cancel a running or pending run."""
    try:
        run = _service.cancel_run(run_id, tenant_id=_tenant_id(request) or None)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RunStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return run.model_dump(mode="json")


@router.delete("/runs/{run_id}", dependencies=[require_scope("component-security:write")])
async def delete_run(run_id: str, request: Request) -> dict[str, str]:
    """Delete a run and associated findings."""
    try:
        _service.delete_run(run_id, tenant_id=_tenant_id(request) or None)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": run_id}


@router.get("/runs/{run_id}/status", dependencies=[require_scope("component-security:read")])
async def get_run_status(run_id: str, request: Request) -> dict[str, str]:
    """Get status for polling clients."""
    try:
        run = _service.get_run(run_id, tenant_id=_tenant_id(request) or None)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"run_id": run.id, "status": run.status.value}
