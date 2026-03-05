"""FastAPI router for HITL tool-approval lifecycle operations."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agent33.security.permissions import require_scope
from agent33.tools.approvals import ApprovalStatus, ToolApprovalService

router = APIRouter(prefix="/v1/approvals/tools", tags=["tool-approvals"])

_service = ToolApprovalService()


def set_tool_approval_service(service: ToolApprovalService) -> None:
    """Inject a shared approval service instance (called from lifespan)."""
    global _service  # noqa: PLW0603
    _service = service


def get_tool_approval_service() -> ToolApprovalService:
    """Return singleton approval service."""
    return _service


def _reset_tool_approval_service() -> None:
    """Reset singleton approval service for tests."""
    global _service  # noqa: PLW0603
    _service = ToolApprovalService()


def _get_token_payload(request: Request) -> Any:
    """Extract token payload previously set by auth middleware."""
    payload = getattr(request.state, "user", None)
    if payload is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return payload


class DecisionRequest(BaseModel):
    decision: Literal["approve", "reject"] = "approve"
    review_note: str = ""


@router.get("", dependencies=[require_scope("workflows:read")])
async def list_tool_approvals(
    request: Request,
    status: str | None = None,
    requested_by: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    token_payload = _get_token_payload(request)
    tenant_id = token_payload.tenant_id or ""
    status_filter: ApprovalStatus | None = None
    if status is not None:
        try:
            status_filter = ApprovalStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid status value: {status}") from exc
    records = _service.list_requests(
        status=status_filter,
        requested_by=requested_by,
        tenant_id=tenant_id,
        limit=limit,
    )
    return [record.model_dump(mode="json") for record in records]


@router.get("/{approval_id}", dependencies=[require_scope("workflows:read")])
async def get_tool_approval(request: Request, approval_id: str) -> dict[str, Any]:
    token_payload = _get_token_payload(request)
    tenant_id = token_payload.tenant_id or ""
    record = _service.get_request(approval_id)
    if record is None or (tenant_id and record.tenant_id != tenant_id):
        raise HTTPException(status_code=404, detail=f"Approval request not found: {approval_id}")
    return record.model_dump(mode="json")


@router.post("/{approval_id}/decision", dependencies=[require_scope("tools:execute")])
async def decide_tool_approval(
    request: Request, approval_id: str, body: DecisionRequest
) -> dict[str, Any]:
    token_payload = _get_token_payload(request)
    tenant_id = token_payload.tenant_id or ""
    reviewed_by = token_payload.sub or ""
    record = _service.get_request(approval_id)
    if record is None or (tenant_id and record.tenant_id != tenant_id):
        raise HTTPException(status_code=404, detail=f"Approval request not found: {approval_id}")
    record = _service.decide(
        approval_id,
        approved=body.decision == "approve",
        reviewed_by=reviewed_by,
        review_note=body.review_note,
    )
    if record is None:
        raise HTTPException(status_code=404, detail=f"Approval request not found: {approval_id}")
    return record.model_dump(mode="json")
