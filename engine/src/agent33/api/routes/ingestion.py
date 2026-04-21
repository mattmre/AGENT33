"""FastAPI routes for the candidate asset ingestion lifecycle.

Provides REST endpoints:
- ``POST /v1/ingestion/candidates``                     — ingest a new candidate
- ``GET  /v1/ingestion/candidates/{id}``                — get by ID
- ``GET  /v1/ingestion/candidates``                     — list (by status or tenant)
- ``POST /v1/ingestion/candidates/{id}/transition``     — apply a lifecycle transition
- ``POST /v1/ingestion/intake``                         — batch intake via pipeline
- ``GET  /v1/ingestion/intake/stats``                   — pipeline stats for tenant
- ``POST /v1/ingestion/mailbox``                        — post an operator event
- ``GET  /v1/ingestion/mailbox/drain``                  — drain inbox for tenant
- ``GET  /v1/ingestion/heartbeat``                      — unauthenticated liveness check
- ``GET  /v1/ingestion/metrics``                        — task metrics summary

Auth: write endpoints require ``ingestion:write`` scope; read endpoints
require ``ingestion:read`` scope.  Heartbeat is public.

CLEAN-ROOM RESTRICTION
=======================
No code in this file may originate from the EvoMap/Evolver project.
"""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agent33.ingestion.intake import IntakePipeline
from agent33.ingestion.mailbox import IngestionMailbox
from agent33.ingestion.metrics import TaskMetricsCollector
from agent33.ingestion.models import CandidateStatus, ConfidenceLevel
from agent33.ingestion.service import IngestionService
from agent33.ingestion.state_machine import CandidateTransitionError
from agent33.security.permissions import require_scope

router = APIRouter(prefix="/v1/ingestion", tags=["ingestion"])
logger = structlog.get_logger()

# Module-level fallbacks; replaced by lifespan via set_ingestion_service() /
# set_intake_pipeline() / set_ingestion_mailbox() / set_task_metrics().
_service = IngestionService()
_intake_pipeline = IntakePipeline(_service)
_ingestion_mailbox = IngestionMailbox(pipeline=_intake_pipeline)
_task_metrics = TaskMetricsCollector()


def set_ingestion_service(service: IngestionService) -> None:
    """Swap the module-level ingestion service (called from lifespan)."""
    global _service
    _service = service


def set_intake_pipeline(pipeline: IntakePipeline) -> None:
    """Swap the module-level intake pipeline (called from lifespan)."""
    global _intake_pipeline
    _intake_pipeline = pipeline


def set_ingestion_mailbox(mailbox: IngestionMailbox) -> None:
    """Swap the module-level ingestion mailbox (called from lifespan)."""
    global _ingestion_mailbox
    _ingestion_mailbox = mailbox


def set_task_metrics(metrics: TaskMetricsCollector) -> None:
    """Swap the module-level task metrics collector (called from lifespan)."""
    global _task_metrics
    _task_metrics = metrics


def get_ingestion_service(request: Request) -> IngestionService:
    """Return the ingestion service from app.state, falling back to module-level."""
    svc: IngestionService | None = getattr(request.app.state, "ingestion_service", None)
    return svc if svc is not None else _service


def get_intake_pipeline(request: Request) -> IntakePipeline:
    """Return the intake pipeline from app.state, falling back to module-level."""
    pipeline: IntakePipeline | None = getattr(request.app.state, "intake_pipeline", None)
    return pipeline if pipeline is not None else _intake_pipeline


def get_ingestion_mailbox(request: Request) -> IngestionMailbox:
    """Return the ingestion mailbox from app.state, falling back to module-level."""
    mailbox: IngestionMailbox | None = getattr(request.app.state, "ingestion_mailbox", None)
    return mailbox if mailbox is not None else _ingestion_mailbox


def get_task_metrics(request: Request) -> TaskMetricsCollector:
    """Return the task metrics collector from app.state, falling back to module-level."""
    metrics: TaskMetricsCollector | None = getattr(request.app.state, "task_metrics", None)
    return metrics if metrics is not None else _task_metrics


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


class IntakeRequest(BaseModel):
    """Request body for the batch intake endpoint."""

    assets: list[dict[str, Any]] = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    tenant_id: str = Field(..., min_length=1)


class MailboxPostRequest(BaseModel):
    """Request body for posting an event to the ingestion mailbox."""

    event_type: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    sender: str = Field(..., min_length=1)


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


@router.post(
    "/intake",
    status_code=201,
    dependencies=[require_scope("ingestion:write")],
)
async def batch_intake(body: IntakeRequest, request: Request) -> dict[str, Any]:
    """Submit a batch of assets through the intake pipeline.

    Each asset is routed by confidence level:
    - HIGH → auto-advanced to VALIDATED
    - MEDIUM → stays CANDIDATE with ``review_required=True`` in metadata
    - LOW → stays CANDIDATE with ``review_required=True`` and ``quarantine=True``

    Individual failures do not abort the batch; errors are captured in the
    asset's ``metadata.intake_error`` field.

    Returns a dict with ``assets`` (list of created asset dicts) and ``stats``
    (counts by status for the given tenant).
    """
    pipeline = get_intake_pipeline(request)
    created = pipeline.batch_submit(body.assets, source=body.source, tenant_id=body.tenant_id)
    stats = pipeline.get_pipeline_stats(body.tenant_id)
    return {
        "assets": [a.model_dump(mode="json") for a in created],
        "stats": stats,
    }


@router.get(
    "/intake/stats",
    dependencies=[require_scope("ingestion:read")],
)
async def intake_stats(request: Request, tenant_id: str) -> dict[str, Any]:
    """Return per-status asset counts for the given tenant.

    Query parameter:
    - ``tenant_id``: The tenant scope to aggregate counts for.
    """
    pipeline = get_intake_pipeline(request)
    return pipeline.get_pipeline_stats(tenant_id)


@router.post(
    "/mailbox",
    status_code=202,
    dependencies=[require_scope("ingestion:write")],
)
async def post_mailbox_event(body: MailboxPostRequest, request: Request) -> dict[str, str]:
    """Deposit an operator event into the ingestion mailbox.

    ``candidate_asset`` events are forwarded immediately to the intake pipeline.
    All other event types are held in the in-memory inbox until drained.

    Returns ``{"status": "accepted", "event_id": "<uuid4>"}`` on success.
    Returns 422 if the event fails validation.
    """
    mailbox = get_ingestion_mailbox(request)
    metrics = get_task_metrics(request)

    import time

    start = time.monotonic()
    try:
        result = mailbox.post(
            {"event_type": body.event_type, "payload": body.payload},
            sender=body.sender,
            tenant_id=_resolve_tenant_id(request),
        )
        latency_ms = (time.monotonic() - start) * 1000
        metrics.record(
            body.event_type,
            _resolve_tenant_id(request),
            success=True,
            latency_ms=latency_ms,
        )
    except ValueError as exc:
        metrics.record(body.event_type, _resolve_tenant_id(request), success=False)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return result


@router.get(
    "/mailbox/drain",
    dependencies=[require_scope("ingestion:read")],
)
async def drain_mailbox(request: Request) -> list[dict[str, Any]]:
    """Drain and return all queued inbox events for the authenticated tenant.

    Events that were routed to the intake pipeline are not returned here.
    """
    mailbox = get_ingestion_mailbox(request)
    return mailbox.drain(_resolve_tenant_id(request))


@router.get("/heartbeat")
async def heartbeat(request: Request) -> dict[str, Any]:
    """Return a combined liveness snapshot.  This endpoint is unauthenticated.

    Merges :meth:`IngestionMailbox.heartbeat` with
    :meth:`IntakePipeline.get_pipeline_stats` using the ``"system"`` tenant
    to provide a broad operational view.
    """
    mailbox = get_ingestion_mailbox(request)
    pipeline = get_intake_pipeline(request)
    hb = mailbox.heartbeat()
    pipeline_stats = pipeline.get_pipeline_stats("system")
    return {**hb, "pipeline_stats": pipeline_stats}


@router.get(
    "/metrics",
    dependencies=[require_scope("ingestion:read")],
)
async def task_metrics(request: Request) -> dict[str, Any]:
    """Return the task metrics summary for the authenticated tenant."""
    metrics = get_task_metrics(request)
    return metrics.summary(_resolve_tenant_id(request))


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _resolve_tenant_id(request: Request) -> str:
    """Extract tenant_id from the authenticated request state, or use 'unknown'."""
    user = getattr(request.state, "user", None)
    if user is None:
        return "unknown"
    return str(getattr(user, "tenant_id", None) or getattr(user, "sub", "unknown"))
