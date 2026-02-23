"""FastAPI router for component security scan runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agent33.component_security.llm_security import LLMSecurityScanner
from agent33.component_security.mcp_scanner import MCPSecurityScanner
from agent33.component_security.models import (
    FindingSeverity,
    FindingsSummary,
    RunStatus,
    ScanOptions,
    ScanTarget,
    SecurityFinding,
    SecurityProfile,
)
from agent33.security.permissions import require_scope
from agent33.services.security_scan import (
    RunNotFoundError,
    RunStateError,
    SecurityScanError,
    SecurityScanService,
)

router = APIRouter(prefix="/v1/component-security", tags=["component-security"])
_WORKSPACE_ROOT = Path(__file__).resolve().parents[5]
_service = SecurityScanService(allowed_roots=[str(_WORKSPACE_ROOT)])
_mcp_scanner = MCPSecurityScanner()
_llm_scanner = LLMSecurityScanner()


def get_component_security_service() -> SecurityScanService:
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
        except SecurityScanError as exc:
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


@router.get(
    "/runs/{run_id}/sarif",
    dependencies=[require_scope("component-security:read")],
)
async def get_run_sarif(run_id: str, request: Request) -> dict[str, Any]:
    """Export findings as SARIF 2.1.0 JSON."""
    try:
        sarif = _service.sarif_export(
            run_id, tenant_id=_tenant_id(request) or None
        )
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return sarif


# ---------------------------------------------------------------------------
# MCP security server management endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/mcp-servers",
    status_code=201,
    dependencies=[require_scope("component-security:write")],
)
async def register_mcp_server(body: dict[str, Any]) -> dict[str, Any]:
    """Register an MCP security server."""
    name = body.get("name", "")
    transport = body.get("transport", "")
    config = body.get("config", {})
    if not name or not transport:
        raise HTTPException(status_code=400, detail="name and transport are required")
    try:
        server = _mcp_scanner.register_server(name, transport, config)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return server.model_dump(mode="json")


@router.get(
    "/mcp-servers",
    dependencies=[require_scope("component-security:read")],
)
async def list_mcp_servers() -> list[dict[str, Any]]:
    """List registered MCP security servers."""
    return [s.model_dump(mode="json") for s in _mcp_scanner.list_servers()]


@router.delete(
    "/mcp-servers/{name}",
    dependencies=[require_scope("component-security:write")],
)
async def remove_mcp_server(name: str) -> dict[str, str]:
    """Remove a registered MCP security server."""
    if not _mcp_scanner.unregister_server(name):
        raise HTTPException(status_code=404, detail=f"MCP server not found: {name}")
    return {"deleted": name}


# ---------------------------------------------------------------------------
# AI/LLM security scanning endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/runs/{run_id}/llm-scan",
    dependencies=[require_scope("component-security:write")],
)
async def run_llm_scan(run_id: str, request: Request) -> dict[str, Any]:
    """Trigger AI-specific security scan for a run."""
    try:
        run = _service.get_run(run_id, tenant_id=_tenant_id(request) or None)
    except RunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # Run prompt injection scan on run metadata text fields
    findings: list[SecurityFinding] = []
    text_fields = [
        run.metadata.requested_by,
        run.metadata.session_id,
        run.target.repository_path,
        run.target.branch,
    ]
    for field in text_fields:
        if field:
            findings.extend(
                _llm_scanner.scan_prompt_safety(field, run_id=run.id, source="run_metadata")
            )

    # Store findings alongside existing ones
    existing = _service._findings.get(run.id, [])
    existing.extend(findings)
    _service._findings[run.id] = existing

    run.findings_count = len(existing)
    run.findings_summary = FindingsSummary.from_findings(existing)

    return {
        "run_id": run.id,
        "llm_findings": len(findings),
        "total_findings": len(existing),
    }
