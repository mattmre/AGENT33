"""FastAPI router for review automation and two-layer signoff."""

# NOTE: no ``from __future__ import annotations`` — Pydantic needs these
# types at runtime for request-body validation.

from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agent33.review.models import (
    L1ChecklistResults,
    L2ChecklistResults,
    ReviewDecision,
    RiskTrigger,
)
from agent33.review.service import (
    ReviewNotFoundError,
    ReviewService,
    ReviewStateError,
)
from agent33.security.permissions import require_scope

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/reviews", tags=["reviews"])

# Singleton service (same pattern as workflows registry)
_service = ReviewService()


def get_review_service() -> ReviewService:
    """Return the review service singleton (for testing injection)."""
    return _service


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class CreateReviewRequest(BaseModel):
    task_id: str
    branch: str = ""
    pr_number: int | None = None


class AssessRiskRequest(BaseModel):
    triggers: list[RiskTrigger]


class SubmitL1Request(BaseModel):
    decision: ReviewDecision
    checklist: L1ChecklistResults | None = None
    issues: list[str] = Field(default_factory=list)
    comments: str = ""


class SubmitL2Request(BaseModel):
    decision: ReviewDecision
    checklist: L2ChecklistResults | None = None
    issues: list[str] = Field(default_factory=list)
    comments: str = ""


class ApproveRequest(BaseModel):
    approver_id: str
    conditions: list[str] = Field(default_factory=list)


class ReviewSummary(BaseModel):
    id: str
    task_id: str
    state: str
    risk_level: str
    l1_required: bool
    l2_required: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_tenant_id(request: Request) -> str:
    """Extract tenant_id from the authenticated user."""
    user = getattr(request.state, "user", None)
    if user is not None:
        return getattr(user, "tenant_id", "")
    return ""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.post("/", status_code=201, dependencies=[require_scope("workflows:write")])
async def create_review(
    body: CreateReviewRequest, request: Request
) -> dict[str, Any]:
    """Create a new review record in DRAFT state."""
    tenant_id = _get_tenant_id(request)
    record = _service.create(
        task_id=body.task_id,
        branch=body.branch,
        pr_number=body.pr_number,
        tenant_id=tenant_id,
    )
    return {"id": record.id, "state": record.state.value, "task_id": record.task_id}


@router.get("/", dependencies=[require_scope("workflows:read")])
async def list_reviews(request: Request) -> list[ReviewSummary]:
    """List all reviews (filtered by tenant)."""
    tenant_id = _get_tenant_id(request)
    records = _service.list_all(tenant_id=tenant_id if tenant_id else None)
    return [
        ReviewSummary(
            id=r.id,
            task_id=r.task_id,
            state=r.state.value,
            risk_level=r.risk_assessment.risk_level.value,
            l1_required=r.risk_assessment.l1_required,
            l2_required=r.risk_assessment.l2_required,
        )
        for r in records
    ]


@router.get("/{review_id}", dependencies=[require_scope("workflows:read")])
async def get_review(review_id: str) -> dict[str, Any]:
    """Get a review record by ID."""
    try:
        record = _service.get(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return record.model_dump(mode="json")


@router.delete("/{review_id}", dependencies=[require_scope("workflows:write")])
async def delete_review(review_id: str) -> dict[str, str]:
    """Delete a review record."""
    try:
        _service.delete(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": review_id}


@router.post(
    "/{review_id}/assess", dependencies=[require_scope("workflows:write")]
)
async def assess_risk(review_id: str, body: AssessRiskRequest) -> dict[str, Any]:
    """Run risk assessment on a review."""
    try:
        record = _service.assess_risk(review_id, body.triggers)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "id": record.id,
        "risk_level": record.risk_assessment.risk_level.value,
        "l1_required": record.risk_assessment.l1_required,
        "l2_required": record.risk_assessment.l2_required,
        "triggers": [t.value for t in record.risk_assessment.triggers_identified],
    }


@router.post(
    "/{review_id}/ready", dependencies=[require_scope("workflows:write")]
)
async def mark_ready(review_id: str) -> dict[str, Any]:
    """Move review from DRAFT to READY."""
    try:
        record = _service.mark_ready(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReviewStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": record.id, "state": record.state.value}


@router.post(
    "/{review_id}/assign-l1", dependencies=[require_scope("workflows:write")]
)
async def assign_l1(review_id: str) -> dict[str, Any]:
    """Assign L1 reviewer and move to L1_REVIEW."""
    try:
        record = _service.assign_l1(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReviewStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": record.id,
        "state": record.state.value,
        "l1_reviewer": record.l1_review.reviewer_id,
        "l1_role": record.l1_review.reviewer_role,
    }


@router.post(
    "/{review_id}/l1", dependencies=[require_scope("workflows:write")]
)
async def submit_l1(review_id: str, body: SubmitL1Request) -> dict[str, Any]:
    """Submit L1 review decision."""
    try:
        record = _service.submit_l1(
            review_id,
            decision=body.decision,
            checklist=body.checklist,
            issues=body.issues or None,
            comments=body.comments,
        )
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReviewStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": record.id,
        "state": record.state.value,
        "decision": body.decision.value,
    }


@router.post(
    "/{review_id}/assign-l2", dependencies=[require_scope("workflows:write")]
)
async def assign_l2(review_id: str) -> dict[str, Any]:
    """Assign L2 reviewer and move to L2_REVIEW."""
    try:
        record = _service.assign_l2(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReviewStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": record.id,
        "state": record.state.value,
        "l2_reviewer": record.l2_review.reviewer_id,
        "l2_role": record.l2_review.reviewer_role,
    }


@router.post(
    "/{review_id}/l2", dependencies=[require_scope("workflows:write")]
)
async def submit_l2(review_id: str, body: SubmitL2Request) -> dict[str, Any]:
    """Submit L2 review decision."""
    try:
        record = _service.submit_l2(
            review_id,
            decision=body.decision,
            checklist=body.checklist,
            issues=body.issues or None,
            comments=body.comments,
        )
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReviewStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": record.id,
        "state": record.state.value,
        "decision": body.decision.value,
    }


@router.post(
    "/{review_id}/approve", dependencies=[require_scope("workflows:write")]
)
async def approve_review(
    review_id: str, body: ApproveRequest
) -> dict[str, Any]:
    """Record final signoff on an approved review."""
    try:
        record = _service.approve(
            review_id,
            approver_id=body.approver_id,
            conditions=body.conditions or None,
        )
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReviewStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "id": record.id,
        "state": record.state.value,
        "approved_by": record.final_signoff.approved_by,
        "approval_type": record.final_signoff.approval_type,
    }


@router.post(
    "/{review_id}/merge", dependencies=[require_scope("workflows:write")]
)
async def merge_review(review_id: str) -> dict[str, Any]:
    """Mark a review as merged (final state)."""
    try:
        record = _service.merge(review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ReviewStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"id": record.id, "state": record.state.value}
