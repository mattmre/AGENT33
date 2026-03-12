"""FastAPI router for local skill pack management.

Provides 8 endpoints for listing, installing, uninstalling, enabling,
disabling, searching, and syncing skill packs.  All pack state changes
are tenant-scoped via the authenticated user's tenant_id.
"""

# NOTE: no ``from __future__ import annotations`` -- Pydantic needs these
# types at runtime for request-body validation.

from contextlib import suppress
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Query, Request

from agent33.packs.api_models import (
    EnableDisableResponse,
    EnablementMatrixResponse,
    EnablementMatrixUpdateRequest,
    InstallRequest,
    InstallResponse,
    PackDetail,
    PackRollbackResponse,
    PackSkillInfo,
    PackSummary,
    PackTrustResponse,
    PackUpgradeRequest,
    TrustPolicyResponse,
    TrustPolicyUpdateRequest,
)
from agent33.packs.models import PackSource
from agent33.packs.provenance import evaluate_trust
from agent33.security.permissions import require_scope

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/packs", tags=["packs"])


def _get_pack_registry(request: Request) -> Any:
    """Retrieve PackRegistry from app state.

    Returns None if not initialized (graceful degradation).
    """
    return getattr(request.app.state, "pack_registry", None)


def _get_pack_trust_manager(request: Request) -> Any:
    """Retrieve the pack trust manager from app state."""
    return getattr(request.app.state, "pack_trust_manager", None)


def _get_pack_rollback_manager(request: Request) -> Any:
    """Retrieve the pack rollback manager from app state."""
    return getattr(request.app.state, "pack_rollback_manager", None)


def _tenant_id(request: Request) -> str:
    """Extract tenant ID from authenticated principal."""
    user = getattr(request.state, "user", None)
    if user is None:
        return "default"
    return getattr(user, "tenant_id", None) or "default"


def _pack_to_summary(pack: Any) -> PackSummary:
    """Convert InstalledPack to PackSummary."""
    return PackSummary(
        name=pack.name,
        version=pack.version,
        description=pack.description,
        author=pack.author,
        tags=pack.tags,
        category=pack.category,
        skills_count=len(pack.loaded_skill_names),
        status=pack.status.value if hasattr(pack.status, "value") else str(pack.status),
    )


def _pack_to_detail(pack: Any) -> PackDetail:
    """Convert InstalledPack to PackDetail."""
    return PackDetail(
        name=pack.name,
        version=pack.version,
        description=pack.description,
        author=pack.author,
        license=pack.license,
        tags=pack.tags,
        category=pack.category,
        skills=[
            PackSkillInfo(
                name=s.name,
                path=s.path,
                description=s.description,
                required=s.required,
            )
            for s in pack.skills
        ],
        loaded_skill_names=pack.loaded_skill_names,
        engine_min_version=pack.engine_min_version,
        installed_at=pack.installed_at,
        source=pack.source,
        source_reference=pack.source_reference,
        checksum=pack.checksum,
        status=pack.status.value if hasattr(pack.status, "value") else str(pack.status),
        provenance=pack.provenance,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", dependencies=[require_scope("agents:read")])
async def list_packs(request: Request) -> dict[str, Any]:
    """List all installed packs."""
    registry = _get_pack_registry(request)
    if registry is None:
        return {"packs": [], "count": 0}

    packs = registry.list_installed()
    return {
        "packs": [_pack_to_summary(p).model_dump() for p in packs],
        "count": len(packs),
    }


@router.get("/enabled", dependencies=[require_scope("agents:read")])
async def list_enabled_packs(request: Request) -> dict[str, Any]:
    """List packs enabled for the current tenant."""
    registry = _get_pack_registry(request)
    if registry is None:
        return {"packs": [], "count": 0, "tenant_id": _tenant_id(request)}

    tenant = _tenant_id(request)
    packs = registry.list_enabled(tenant)
    return {
        "packs": [_pack_to_summary(p).model_dump() for p in packs],
        "count": len(packs),
        "tenant_id": tenant,
    }


@router.get("/search", dependencies=[require_scope("agents:read")])
async def search_packs(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
) -> dict[str, Any]:
    """Search installed packs by name, description, or tags."""
    registry = _get_pack_registry(request)
    if registry is None:
        return {"results": [], "count": 0, "query": q}

    results = registry.search(q)
    return {
        "results": [_pack_to_summary(p).model_dump() for p in results],
        "count": len(results),
        "query": q,
    }


@router.get("/{name}", dependencies=[require_scope("agents:read")])
async def get_pack(name: str, request: Request) -> dict[str, Any]:
    """Get details of an installed pack."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")

    pack = registry.get(name)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"Pack '{name}' not found")

    tenant = _tenant_id(request)
    detail = _pack_to_detail(pack)
    return {
        **detail.model_dump(mode="json"),
        "enabled_for_tenant": registry.is_enabled(name, tenant),
    }


@router.post("/install", status_code=201, dependencies=[require_scope("agents:write")])
async def install_pack(body: InstallRequest, request: Request) -> dict[str, Any]:
    """Install a pack from a local path."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")

    source = PackSource(
        source_type=body.source_type,
        path=body.path,
        name=body.name,
        version=body.version,
    )

    result = registry.install(source)
    response = InstallResponse(
        success=result.success,
        pack_name=result.pack_name,
        version=result.version,
        skills_loaded=result.skills_loaded,
        errors=result.errors,
        warnings=result.warnings,
    )

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Failed to install pack '{result.pack_name}'",
                "errors": result.errors,
            },
        )

    return response.model_dump()


@router.post("/{name}/upgrade", dependencies=[require_scope("agents:write")])
async def upgrade_pack(
    name: str,
    body: PackUpgradeRequest,
    request: Request,
) -> dict[str, Any]:
    """Upgrade an installed pack from a local or marketplace source."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")
    rollback_manager = _get_pack_rollback_manager(request)
    if rollback_manager is not None:
        with suppress(ValueError):
            rollback_manager.archive_current(name)

    source = PackSource(
        source_type=body.source_type,
        path=body.path,
        name=body.name or name,
        version=body.version,
    )
    result = registry.upgrade_from_source(name, source)
    response = InstallResponse(
        success=result.success,
        pack_name=result.pack_name,
        version=result.version,
        skills_loaded=result.skills_loaded,
        errors=result.errors,
        warnings=result.warnings,
    )
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Failed to upgrade pack '{name}'",
                "errors": result.errors,
            },
        )
    return response.model_dump()


@router.delete("/{name}", status_code=204, dependencies=[require_scope("agents:write")])
async def uninstall_pack(name: str, request: Request) -> None:
    """Uninstall a pack and remove its skills."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")

    try:
        registry.uninstall(name)
    except ValueError as exc:
        if "not installed" in str(exc):
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if "required by" in str(exc):
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{name}/enable", dependencies=[require_scope("agents:write")])
async def enable_pack(name: str, request: Request) -> dict[str, Any]:
    """Enable a pack for the current tenant."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")

    tenant = _tenant_id(request)
    try:
        registry.enable(name, tenant)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return EnableDisableResponse(
        success=True,
        pack_name=name,
        tenant_id=tenant,
        action="enabled",
    ).model_dump()


@router.post("/{name}/disable", dependencies=[require_scope("agents:write")])
async def disable_pack(name: str, request: Request) -> dict[str, Any]:
    """Disable a pack for the current tenant."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")

    tenant = _tenant_id(request)
    try:
        registry.disable(name, tenant)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return EnableDisableResponse(
        success=True,
        pack_name=name,
        tenant_id=tenant,
        action="disabled",
    ).model_dump()


@router.post("/{name}/sync", dependencies=[require_scope("agents:write")])
async def sync_pack(name: str, request: Request) -> dict[str, Any]:
    """Re-scan and reload a pack from disk.

    Useful after editing pack skills on the filesystem.
    """
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")

    pack = registry.get(name)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"Pack '{name}' not found")

    result = registry.upgrade(name, pack.pack_dir)
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Failed to sync pack '{name}'",
                "errors": result.errors,
            },
        )

    return {
        "success": True,
        "pack_name": name,
        "version": result.version,
        "skills_loaded": result.skills_loaded,
    }


@router.get(
    "/{name}/trust",
    response_model=PackTrustResponse,
    dependencies=[require_scope("agents:read")],
)
async def get_pack_trust(name: str, request: Request) -> PackTrustResponse:
    """Return provenance and policy evaluation for one installed pack."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")
    pack = registry.get(name)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"Pack '{name}' not found")

    policy = registry.trust_policy
    decision = evaluate_trust(pack.provenance, policy)
    return PackTrustResponse(
        pack_name=pack.name,
        installed_version=pack.version,
        source=pack.source,
        source_reference=pack.source_reference,
        provenance=pack.provenance,
        policy=policy,
        allowed=decision.allowed,
        reason=decision.reason,
    )


@router.get(
    "/trust/policy",
    response_model=TrustPolicyResponse,
    dependencies=[require_scope("agents:read")],
)
async def get_pack_trust_policy(request: Request) -> TrustPolicyResponse:
    """Return the active trust policy for pack installation."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")
    return TrustPolicyResponse(policy=registry.trust_policy)


@router.put(
    "/trust/policy",
    response_model=TrustPolicyResponse,
    dependencies=[require_scope("admin")],
)
async def update_pack_trust_policy(
    body: TrustPolicyUpdateRequest,
    request: Request,
) -> TrustPolicyResponse:
    """Update the active trust policy for pack installation."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")
    manager = _get_pack_trust_manager(request)
    if manager is None:
        raise HTTPException(status_code=503, detail="Pack trust manager not initialized")
    policy = manager.update_policy(
        require_signature=body.require_signature,
        min_trust_level=body.min_trust_level,
        allowed_signers=body.allowed_signers,
    )
    registry.set_trust_policy(policy)
    return TrustPolicyResponse(policy=policy)


@router.get(
    "/enablement/matrix",
    response_model=EnablementMatrixResponse,
    dependencies=[require_scope("agents:read")],
)
async def get_enablement_matrix(request: Request) -> EnablementMatrixResponse:
    """Return operator-visible pack enablement state across tenants."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")
    matrix = registry.get_enablement_matrix()
    return EnablementMatrixResponse(
        packs=sorted(matrix),
        tenants=sorted({tenant for tenant_map in matrix.values() for tenant in tenant_map}),
        matrix=matrix,
    )


@router.put(
    "/enablement/matrix",
    response_model=EnablementMatrixResponse,
    dependencies=[require_scope("admin")],
)
async def update_enablement_matrix(
    body: EnablementMatrixUpdateRequest,
    request: Request,
) -> EnablementMatrixResponse:
    """Apply operator-managed enablement changes across tenants."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")
    try:
        registry.apply_enablement_matrix(body.matrix)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    matrix = registry.get_enablement_matrix()
    return EnablementMatrixResponse(
        packs=sorted(matrix),
        tenants=sorted({tenant for tenant_map in matrix.values() for tenant in tenant_map}),
        matrix=matrix,
    )


@router.post(
    "/{name}/rollback",
    response_model=PackRollbackResponse,
    dependencies=[require_scope("agents:write")],
)
async def rollback_pack(
    name: str,
    request: Request,
    version: str = Query(default=""),
) -> PackRollbackResponse:
    """Rollback an installed pack to an archived revision."""
    manager = _get_pack_rollback_manager(request)
    if manager is None:
        raise HTTPException(status_code=503, detail="Pack rollback manager not initialized")
    try:
        result, revision = manager.rollback(name, version=version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result.success:
        raise HTTPException(
            status_code=400,
            detail={
                "message": f"Failed to rollback pack '{name}'",
                "errors": result.errors,
            },
        )
    return PackRollbackResponse(
        success=True,
        pack_name=name,
        version=result.version,
        restored_from_version=revision.version,
        errors=[],
    )
