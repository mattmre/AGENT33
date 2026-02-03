"""Source management API endpoints for ingestion configuration."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent33.db.models import Source, SourceType
from agent33.db.session import get_session
from agent33.ingestion.manager import IngestionManager, create_default_sources
from agent33.tenancy.middleware import get_current_tenant
from agent33.tenancy.models import TenantContext

logger = structlog.get_logger()
router = APIRouter(prefix="/api/sources", tags=["sources"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class SourceCreate(BaseModel):
    """Request body for creating a source."""

    name: str
    source_type: SourceType
    url: str | None = None
    config: dict[str, Any] = {}
    is_active: bool = True


class SourceUpdate(BaseModel):
    """Request body for updating a source."""

    name: str | None = None
    url: str | None = None
    config: dict[str, Any] | None = None
    is_active: bool | None = None


class SourceResponse(BaseModel):
    """Response model for a source."""

    id: str
    name: str
    source_type: str
    url: str | None
    config: dict[str, Any]
    is_active: bool
    last_fetched_at: str | None
    last_error: str | None
    items_fetched: int
    created_at: str

    class Config:
        from_attributes = True


class SourceListResponse(BaseModel):
    """Response model for listing sources."""

    items: list[SourceResponse]
    total: int


class IngestResponse(BaseModel):
    """Response from running ingestion."""

    status: str
    items_fetched: int | None = None
    new_facts: int | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=SourceListResponse)
async def list_sources(
    source_type: SourceType | None = None,
    is_active: bool | None = None,
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_current_tenant),
) -> SourceListResponse:
    """List all sources, optionally filtered by type or status."""
    tenant_id = str(tenant.tenant_id)

    stmt = select(Source).where(Source.tenant_id == tenant_id)

    if source_type:
        stmt = stmt.where(Source.source_type == source_type)
    if is_active is not None:
        stmt = stmt.where(Source.is_active == is_active)

    stmt = stmt.order_by(Source.created_at.desc())

    result = await session.execute(stmt)
    sources = result.scalars().all()

    items = [
        SourceResponse(
            id=s.id,
            name=s.name,
            source_type=s.source_type.value,
            url=s.url,
            config=s.config or {},
            is_active=s.is_active,
            last_fetched_at=s.last_fetched_at.isoformat() if s.last_fetched_at else None,
            last_error=s.last_error,
            items_fetched=s.items_fetched,
            created_at=s.created_at.isoformat(),
        )
        for s in sources
    ]

    return SourceListResponse(items=items, total=len(items))


@router.post("", response_model=SourceResponse)
async def create_source(
    body: SourceCreate,
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_current_tenant),
) -> SourceResponse:
    """Create a new ingestion source."""
    tenant_id = str(tenant.tenant_id)

    source = Source(
        tenant_id=tenant_id,
        name=body.name,
        source_type=body.source_type,
        url=body.url,
        config=body.config,
        is_active=body.is_active,
    )
    session.add(source)
    await session.flush()

    return SourceResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type.value,
        url=source.url,
        config=source.config or {},
        is_active=source.is_active,
        last_fetched_at=None,
        last_error=None,
        items_fetched=0,
        created_at=source.created_at.isoformat(),
    )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: str,
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_current_tenant),
) -> SourceResponse:
    """Get a source by ID."""
    tenant_id = str(tenant.tenant_id)
    stmt = select(Source).where(Source.id == source_id, Source.tenant_id == tenant_id)
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return SourceResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type.value,
        url=source.url,
        config=source.config or {},
        is_active=source.is_active,
        last_fetched_at=source.last_fetched_at.isoformat() if source.last_fetched_at else None,
        last_error=source.last_error,
        items_fetched=source.items_fetched,
        created_at=source.created_at.isoformat(),
    )


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: str,
    body: SourceUpdate,
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_current_tenant),
) -> SourceResponse:
    """Update a source."""
    tenant_id = str(tenant.tenant_id)
    stmt = select(Source).where(Source.id == source_id, Source.tenant_id == tenant_id)
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if body.name is not None:
        source.name = body.name
    if body.url is not None:
        source.url = body.url
    if body.config is not None:
        source.config = body.config
    if body.is_active is not None:
        source.is_active = body.is_active

    return SourceResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type.value,
        url=source.url,
        config=source.config or {},
        is_active=source.is_active,
        last_fetched_at=source.last_fetched_at.isoformat() if source.last_fetched_at else None,
        last_error=source.last_error,
        items_fetched=source.items_fetched,
        created_at=source.created_at.isoformat(),
    )


@router.delete("/{source_id}")
async def delete_source(
    source_id: str,
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_current_tenant),
) -> dict[str, str]:
    """Delete a source."""
    tenant_id = str(tenant.tenant_id)
    stmt = select(Source).where(Source.id == source_id, Source.tenant_id == tenant_id)
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await session.delete(source)
    return {"status": "deleted", "id": source_id}


@router.post("/{source_id}/ingest", response_model=IngestResponse)
async def run_ingestion(
    source_id: str,
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_current_tenant),
) -> IngestResponse:
    """Run ingestion for a specific source."""
    tenant_id = str(tenant.tenant_id)

    # Verify source belongs to tenant
    stmt = select(Source).where(Source.id == source_id, Source.tenant_id == tenant_id)
    result = await session.execute(stmt)
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    manager = IngestionManager(tenant_id)

    try:
        result = await manager.run_source(source_id)
        return IngestResponse(
            status=result.get("status", "success"),
            items_fetched=result.get("items_fetched"),
            new_facts=result.get("new_facts"),
        )
    except Exception as e:
        logger.error("ingestion_failed", source_id=source_id, error=str(e))
        return IngestResponse(status="error", error=str(e))


@router.post("/ingest-all", response_model=dict)
async def run_all_ingestion(
    source_type: SourceType | None = Query(None),
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_current_tenant),
) -> dict[str, Any]:
    """Run ingestion for all active sources."""
    tenant_id = str(tenant.tenant_id)

    manager = IngestionManager(tenant_id)
    result = await manager.run_all_sources(source_type)

    return result


@router.post("/setup-defaults", response_model=SourceListResponse)
async def setup_default_sources(
    session: AsyncSession = Depends(get_session),
    tenant: TenantContext = Depends(get_current_tenant),
) -> SourceListResponse:
    """Create default ingestion sources (GDELT, popular RSS feeds)."""
    tenant_id = str(tenant.tenant_id)

    # Check if sources already exist
    stmt = select(Source).where(Source.tenant_id == tenant_id).limit(1)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Sources already exist. Delete existing sources first or add new ones individually.",
        )

    sources = await create_default_sources(tenant_id)

    items = [
        SourceResponse(
            id=s.id,
            name=s.name,
            source_type=s.source_type.value,
            url=s.url,
            config=s.config or {},
            is_active=s.is_active,
            last_fetched_at=None,
            last_error=None,
            items_fetched=0,
            created_at=s.created_at.isoformat(),
        )
        for s in sources
    ]

    return SourceListResponse(items=items, total=len(items))
