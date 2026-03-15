"""Provenance and runtime version API endpoints."""

from __future__ import annotations

import logging
from datetime import datetime  # noqa: TC003
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from agent33.provenance.models import (
    AuditBundle,
    AuditTimelineEntry,
    ProvenanceReceipt,
    ProvenanceSource,
)
from agent33.security.permissions import require_scope

router = APIRouter(tags=["provenance"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_collector(request: Request) -> Any:
    collector = getattr(request.app.state, "provenance_collector", None)
    if collector is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Provenance collector not initialized",
        )
    return collector


def _get_timeline_service(request: Request) -> Any:
    svc = getattr(request.app.state, "audit_timeline_service", None)
    if svc is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit timeline service not initialized",
        )
    return svc


def _get_exporter(request: Request) -> Any:
    exporter = getattr(request.app.state, "audit_exporter", None)
    if exporter is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Audit exporter not initialized",
        )
    return exporter


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ReceiptListResponse(BaseModel):
    """Paginated list of provenance receipts."""

    receipts: list[ProvenanceReceipt]
    count: int


class TimelineResponse(BaseModel):
    """Audit timeline response."""

    entries: list[AuditTimelineEntry]
    count: int


class VersionResponse(BaseModel):
    """Runtime version information."""

    version: str
    git_short_hash: str
    python_version: str
    platform: str


class ExportRequest(BaseModel):
    """Body for triggering an audit export."""

    tenant_id: str = ""
    since: datetime | None = None
    until: datetime | None = None


ExportRequest.model_rebuild()


# ---------------------------------------------------------------------------
# Provenance receipt endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/v1/provenance/receipts",
    response_model=ReceiptListResponse,
    dependencies=[require_scope("provenance:read")],
)
async def list_receipts(
    request: Request,
    source: ProvenanceSource | None = None,
    session_id: str = "",
    tenant_id: str = "",
    since: datetime | None = None,
    limit: int = 100,
) -> ReceiptListResponse:
    """List provenance receipts with optional filters."""
    collector = _get_collector(request)
    receipts = collector.query(
        source=source,
        session_id=session_id,
        tenant_id=tenant_id,
        since=since,
        limit=limit,
    )
    return ReceiptListResponse(receipts=receipts, count=len(receipts))


@router.get(
    "/v1/provenance/receipts/{receipt_id}",
    response_model=ProvenanceReceipt,
    dependencies=[require_scope("provenance:read")],
)
async def get_receipt(
    request: Request,
    receipt_id: str,
) -> ProvenanceReceipt:
    """Retrieve a single provenance receipt by ID."""
    collector = _get_collector(request)
    receipt = collector.get(receipt_id)
    if receipt is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Receipt {receipt_id} not found",
        )
    result: ProvenanceReceipt = receipt
    return result


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


@router.get(
    "/v1/provenance/timeline",
    response_model=TimelineResponse,
    dependencies=[require_scope("provenance:read")],
)
async def timeline(
    request: Request,
    tenant_id: str = "",
    since: datetime | None = None,
    limit: int = 100,
) -> TimelineResponse:
    """Build a human-readable audit timeline."""
    svc = _get_timeline_service(request)
    entries = svc.build(tenant_id=tenant_id, since=since, limit=limit)
    return TimelineResponse(entries=entries, count=len(entries))


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


@router.post(
    "/v1/provenance/export",
    response_model=AuditBundle,
    dependencies=[require_scope("provenance:export")],
)
async def export_audit(
    request: Request,
    body: ExportRequest,
) -> AuditBundle:
    """Generate and return an audit bundle."""
    exporter = _get_exporter(request)
    bundle: AuditBundle = exporter.export(
        tenant_id=body.tenant_id,
        since=body.since,
        until=body.until,
    )
    return bundle


# ---------------------------------------------------------------------------
# Runtime version
# ---------------------------------------------------------------------------


@router.get(
    "/v1/runtime/version",
    response_model=VersionResponse,
    dependencies=[require_scope("provenance:read")],
)
async def runtime_version(
    request: Request,
) -> VersionResponse:
    """Return runtime version info (package version, git hash, Python, platform)."""
    info = getattr(request.app.state, "runtime_version_info", None)
    if info is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Runtime version info not available",
        )
    return VersionResponse(
        version=info.version,
        git_short_hash=info.git_short_hash,
        python_version=info.python_version,
        platform=info.platform,
    )
