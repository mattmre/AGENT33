"""FastAPI router for operations hub aggregation and lifecycle controls."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

import structlog
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agent33.autonomy.service import InvalidStateTransitionError
from agent33.security.permissions import require_scope
from agent33.services.operations_hub import (
    OperationsHubService,
    ProcessNotFoundError,
    UnsupportedControlError,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/operations", tags=["operations"])
_service = OperationsHubService()
_ALLOWED_INCLUDE = {"traces", "budgets", "improvements", "workflows"}


class ProcessControlRequest(BaseModel):
    """Request body for process control actions."""

    action: Literal["pause", "resume", "cancel"]
    reason: str = ""


def get_operations_hub_service() -> OperationsHubService:
    """Return singleton operations hub service."""
    return _service


def _tenant_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        return ""
    return getattr(user, "tenant_id", "")


def _parse_since(value: str | None) -> datetime | None:
    if value is None:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid since timestamp") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


@router.get("/hub", dependencies=[require_scope("workflows:read")])
async def get_hub(
    request: Request,
    include: str | None = None,
    since: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """Return a unified operations-hub process view."""
    include_set: set[str] | None = None
    if include is not None:
        include_set = {item.strip().lower() for item in include.split(",") if item.strip()}
        invalid = include_set - _ALLOWED_INCLUDE
        if invalid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid include values: {', '.join(sorted(invalid))}",
            )

    hub = _service.get_hub(
        tenant_id=_tenant_id(request),
        include=include_set,
        since=_parse_since(since),
        status=status,
        limit=limit,
    )
    logger.info(
        "operations_hub_read",
        tenant_id=_tenant_id(request),
        active_count=hub["active_count"],
    )
    return hub


@router.get("/processes/{process_id}", dependencies=[require_scope("workflows:read")])
async def get_process(process_id: str, request: Request) -> dict[str, Any]:
    """Return detail for a single process."""
    try:
        return _service.get_process(process_id, tenant_id=_tenant_id(request))
    except ProcessNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Process not found") from exc


@router.post("/processes/{process_id}/control", dependencies=[require_scope("workflows:execute")])
async def control_process(
    process_id: str,
    body: ProcessControlRequest,
    request: Request,
) -> dict[str, Any]:
    """Execute lifecycle controls against a process."""
    try:
        return _service.control_process(
            process_id,
            body.action,
            tenant_id=_tenant_id(request),
        )
    except ProcessNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Process not found") from exc
    except (UnsupportedControlError, InvalidStateTransitionError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
