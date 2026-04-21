"""FastAPI routes for the candidate asset ingestion lifecycle.

Provides four REST endpoints:
- ``POST /v1/ingestion/candidates``           — ingest a new candidate
- ``GET  /v1/ingestion/candidates/{id}``      — get by ID
- ``GET  /v1/ingestion/candidates``           — list (by status or tenant)
- ``POST /v1/ingestion/candidates/{id}/transition`` — apply a lifecycle transition

Auth: write endpoints require ``ingestion:write`` scope; read endpoints
require ``ingestion:read`` scope.

CLEAN-ROOM RESTRICTION
=======================
No code in this file may originate from the EvoMap/Evolver project.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agent33.ingestion.models import CandidateAsset, CandidateStatus, ConfidenceLevel
from agent33.ingestion.service import IngestionService
from agent33.ingestion.state_machine import CandidateTransitionError
from agent33.security.permissions import require_scope

if TYPE_CHECKING:
    pass

router = APIRouter(prefix="/v1/ingestion", tags=["ingestion"])
logger = structlog.get_logger()

# Module-level fallback; replaced by lifespan via set_ingestion_service().
_service = IngestionService()


def set_ingestion_service(service: IngestionService) -> None:
    """Swap the module-level ingestion service (called from lifespan)."""
    global _service
    _service = service


def get_ingestion_service(request: Request) -> IngestionService:
    """Return the ingestion service from app.state, falling back to module-level."""
    svc: IngestionService | None = getattr(request.app.state, "ingestion_service", None)
    return svc if svc is not None else _service


# ------------------------------------------------------------------
# Request / Response bodies
# ------------------------------------------------------------------


class IngestRequest(BaseModel):
    """Request body for creating a new candidate asset."""

    name: str = Field(..., min_length=1, max_length=128)
    asset_type: str = Field(..., min_length=1)
    source_uri: str | None = None
    tenant_id: str = Field(..., min_length=1)
    confidence: ConfidenceLevel = ConfidenceLevel.LOW
    metadata: dict[str, Any] = Field(default_factory=dict)


class TransitionRequest(BaseModel):
    """Request body for applying a lifecycle transition."""

    target_status: CandidateStatus
    operator: str | None = None
    reason: str | None = None


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post(
    "/candidates",
    status_code=201,
    dependencies=[require_scope("ingestion:write")],
)
async def ingest_candidate(body: IngestRequest, request: Request) -> dict[str, Any]:
    """Create a new candidate asset in ``CANDIDATE`` status."""
    svc = get_ingestion_service(request)
    asset = svc.ingest(
        name=body.name,
        asset_type=body.asset_type,
        source_uri=body.source_uri,
        tenant_id=body.tenant_id,
        confidence=body.confidence,
        metadata=body.metadata,
    )
    return asset.model_dump(mode="json")


@router.get(
    "/candidates/{asset_id}",
    dependencies=[require_scope("ingestion:read")],
)
async def get_candidate(asset_id: str, request: Request) -> dict[str, Any]:
    """Retrieve a candidate asset by ID."""
    svc = get_ingestion_service(request)
    asset = svc.get(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Candidate asset {asset_id!r} not found.")
    return asset.model_dump(mode="json")


@router.get(
    "/candidates",
    dependencies=[require_scope("ingestion:read")],
)
async def list_candidates(
    request: Request,
    status: CandidateStatus | None = None,
    tenant_id: str | None = None,
) -> list[dict[str, Any]]:
    """List candidate assets, optionally filtered by status or tenant."""
    svc = get_ingestion_service(request)
    if status is not None:
        assets = svc.list_by_status(status)
    elif tenant_id is not None:
        assets = svc.list_by_tenant(tenant_id)
    else:
        # Return all assets across all statuses
        assets = [a for status_val in CandidateStatus for a in svc.list_by_status(status_val)]
    return [a.model_dump(mode="json") for a in assets]


@router.post(
    "/candidates/{asset_id}/transition",
    dependencies=[require_scope("ingestion:write")],
)
async def transition_candidate(
    asset_id: str,
    body: TransitionRequest,
    request: Request,
) -> dict[str, Any]:
    """Apply a lifecycle transition to a candidate asset.

    Returns the updated asset on success.  Returns 404 if the asset is not
    found, and 422 if the requested transition is not permitted.
    """
    svc = get_ingestion_service(request)

    # Resolve the asset first so we can give a clean 404.
    asset = svc.get(asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail=f"Candidate asset {asset_id!r} not found.")

    target = body.target_status

    try:
        if target == CandidateStatus.VALIDATED:
            updated = svc.validate(asset_id, operator=body.operator)
        elif target == CandidateStatus.PUBLISHED:
            updated = svc.promote(asset_id, operator=body.operator)
        elif target == CandidateStatus.REVOKED:
            reason = body.reason or "No reason supplied."
            updated = svc.revoke(asset_id, reason=reason, operator=body.operator)
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Cannot transition to {target.value!r}: not a supported target status.",
            )
    except CandidateTransitionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return updated.model_dump(mode="json")
