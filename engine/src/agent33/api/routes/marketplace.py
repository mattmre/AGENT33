"""FastAPI router for marketplace pack discovery and installation."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from agent33.packs.api_models import (
    InstallResponse,
    MarketplaceInstallRequest,
    MarketplacePackDetail,
    MarketplacePackSummary,
    MarketplacePackVersionInfo,
)
from agent33.packs.models import PackSource
from agent33.security.permissions import require_scope

router = APIRouter(prefix="/v1/marketplace", tags=["marketplace"])


def _get_pack_marketplace(request: Request) -> Any:
    """Retrieve the marketplace catalog from app state."""
    return getattr(request.app.state, "pack_marketplace", None)


def _get_pack_registry(request: Request) -> Any:
    """Retrieve the pack registry from app state."""
    return getattr(request.app.state, "pack_registry", None)


def _record_to_summary(record: Any) -> MarketplacePackSummary:
    """Convert a marketplace record to API summary form."""
    return MarketplacePackSummary(
        name=record.name,
        description=record.description,
        author=record.author,
        tags=record.tags,
        category=record.category,
        latest_version=record.latest_version,
        versions_count=len(record.versions),
    )


def _record_to_detail(record: Any) -> MarketplacePackDetail:
    """Convert a marketplace record to API detail form."""
    return MarketplacePackDetail(
        name=record.name,
        description=record.description,
        author=record.author,
        tags=record.tags,
        category=record.category,
        latest_version=record.latest_version,
        versions=[
            MarketplacePackVersionInfo(
                version=item.version,
                description=item.description,
                author=item.author,
                tags=item.tags,
                category=item.category,
                skills_count=item.skills_count,
            )
            for item in record.versions
        ],
    )


@router.get("/packs", dependencies=[require_scope("agents:read")])
async def list_marketplace_packs(request: Request) -> dict[str, Any]:
    """List marketplace packs."""
    marketplace = _get_pack_marketplace(request)
    if marketplace is None:
        return {"packs": [], "count": 0}

    packs = marketplace.list_packs()
    return {
        "packs": [_record_to_summary(pack).model_dump() for pack in packs],
        "count": len(packs),
    }


@router.get("/packs/{name}", dependencies=[require_scope("agents:read")])
async def get_marketplace_pack(name: str, request: Request) -> dict[str, Any]:
    """Get detail for a marketplace pack."""
    marketplace = _get_pack_marketplace(request)
    if marketplace is None:
        raise HTTPException(status_code=503, detail="Marketplace catalog not initialized")

    pack = marketplace.get_pack(name)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"Marketplace pack '{name}' not found")
    return _record_to_detail(pack).model_dump()


@router.get("/packs/{name}/versions", dependencies=[require_scope("agents:read")])
async def list_marketplace_versions(name: str, request: Request) -> dict[str, Any]:
    """List all versions for a marketplace pack."""
    marketplace = _get_pack_marketplace(request)
    if marketplace is None:
        return {"name": name, "versions": [], "count": 0}

    versions = marketplace.list_versions(name)
    if not versions:
        raise HTTPException(status_code=404, detail=f"Marketplace pack '{name}' not found")
    return {
        "name": name,
        "versions": [
            MarketplacePackVersionInfo(
                version=item.version,
                description=item.description,
                author=item.author,
                tags=item.tags,
                category=item.category,
                skills_count=item.skills_count,
            ).model_dump()
            for item in versions
        ],
        "count": len(versions),
    }


@router.get("/search", dependencies=[require_scope("agents:read")])
async def search_marketplace(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
) -> dict[str, Any]:
    """Search marketplace packs."""
    marketplace = _get_pack_marketplace(request)
    if marketplace is None:
        return {"results": [], "count": 0, "query": q}

    results = marketplace.search(q)
    return {
        "results": [_record_to_summary(pack).model_dump() for pack in results],
        "count": len(results),
        "query": q,
    }


@router.post("/install", status_code=201, dependencies=[require_scope("agents:write")])
async def install_marketplace_pack(
    body: MarketplaceInstallRequest,
    request: Request,
) -> dict[str, Any]:
    """Install a pack from the configured marketplace."""
    registry = _get_pack_registry(request)
    if registry is None:
        raise HTTPException(status_code=503, detail="Pack registry not initialized")

    result = registry.install(PackSource(source_type="marketplace", **body.model_dump()))
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
                "message": f"Failed to install marketplace pack '{result.pack_name}'",
                "errors": result.errors,
            },
        )

    return response.model_dump()
