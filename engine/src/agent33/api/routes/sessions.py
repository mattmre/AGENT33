"""Session management API endpoints (Phase 44).

Provides CRUD, replay, task tracking, and crash recovery for operator sessions.
"""

from __future__ import annotations

import logging
from datetime import datetime  # noqa: TC003 -- Pydantic models need runtime type
from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from agent33.api.routes.tenant_access import require_tenant_context, tenant_filter_for_request
from agent33.security.permissions import check_permission, require_scope
from agent33.sessions.models import OperatorSessionStatus

router = APIRouter(prefix="/v1/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-level service accessor
# ---------------------------------------------------------------------------

_session_service: Any = None


def set_session_service(service: Any) -> None:
    """Set the session service instance (called from lifespan)."""
    global _session_service  # noqa: PLW0603
    _session_service = service


def _get_session_service(request: Request) -> Any:
    """Extract session service from app state or module-level fallback."""
    if hasattr(request.app.state, "operator_session_service"):
        svc = request.app.state.operator_session_service
    else:
        svc = _session_service
    if svc is None:
        raise HTTPException(status_code=503, detail="Operator session service not initialized")
    return svc


def _tenant_id_for_create(request: Request) -> str:
    """Return the tenant binding for newly created sessions."""
    tenant_id, scopes = require_tenant_context(request)
    is_admin = check_permission("admin", scopes) if scopes else False
    if is_admin:
        return ""
    return tenant_id


def _tenant_filter(request: Request) -> str | None:
    """Return the effective tenant filter for the current caller."""
    return tenant_filter_for_request(request)


async def _get_accessible_session(request: Request, session_id: str) -> tuple[Any, Any]:
    """Load a session and enforce tenant ownership for non-admin callers."""
    svc = _get_session_service(request)
    try:
        session = await svc.get_session(session_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from None
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    tenant_id = _tenant_filter(request)
    if tenant_id is not None and session.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    return svc, session


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class SessionCreateRequest(BaseModel):
    """Body for creating a new operator session."""

    purpose: str = ""
    context: dict[str, Any] = Field(default_factory=dict)


class SessionEndRequest(BaseModel):
    """Body for ending a session."""

    status: Literal["completed", "suspended"] = "completed"


class SessionResponse(BaseModel):
    """Response representing an operator session."""

    session_id: str
    purpose: str
    status: str
    started_at: datetime
    updated_at: datetime
    ended_at: datetime | None
    task_count: int
    tasks_completed: int
    event_count: int
    parent_session_id: str | None
    tenant_id: str = ""


class TaskCreateRequest(BaseModel):
    """Body for adding a task to a session."""

    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskUpdateRequest(BaseModel):
    """Body for updating a task status."""

    status: Literal["pending", "in_progress", "done", "blocked"]


class TaskResponse(BaseModel):
    """Response representing a session task."""

    task_id: str
    description: str
    status: str
    created_at: datetime
    completed_at: datetime | None
    metadata: dict[str, Any]


class ReplayEventResponse(BaseModel):
    """Response representing a replay event."""

    event_id: str
    event_type: str
    timestamp: datetime
    session_id: str
    data: dict[str, Any]
    correlation_id: str


class ReplaySummaryResponse(BaseModel):
    """Response representing a replay summary."""

    total_events: int
    by_type: dict[str, int]
    duration_seconds: float
    first_event_at: str = ""
    last_event_at: str = ""


# Rebuild Pydantic models so they resolve 'datetime' under PEP 563
SessionResponse.model_rebuild()
TaskResponse.model_rebuild()
ReplayEventResponse.model_rebuild()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _session_to_response(session: Any) -> SessionResponse:
    return SessionResponse(
        session_id=session.session_id,
        purpose=session.purpose,
        status=session.status.value,
        started_at=session.started_at,
        updated_at=session.updated_at,
        ended_at=session.ended_at,
        task_count=session.task_count,
        tasks_completed=session.tasks_completed,
        event_count=session.event_count,
        parent_session_id=session.parent_session_id,
        tenant_id=session.tenant_id,
    )


def _task_to_response(task: Any) -> TaskResponse:
    return TaskResponse(
        task_id=task.task_id,
        description=task.description,
        status=task.status,
        created_at=task.created_at,
        completed_at=task.completed_at,
        metadata=task.metadata,
    )


# ---------------------------------------------------------------------------
# Session CRUD
# ---------------------------------------------------------------------------


@router.post("/", status_code=201, dependencies=[require_scope("sessions:write")])
async def create_session(
    body: SessionCreateRequest,
    request: Request,
) -> SessionResponse:
    """Create a new operator session."""
    svc = _get_session_service(request)
    session = await svc.start_session(
        purpose=body.purpose,
        context=body.context,
        tenant_id=_tenant_id_for_create(request),
    )
    return _session_to_response(session)


@router.get("/", dependencies=[require_scope("sessions:read")])
async def list_sessions(
    request: Request,
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
) -> list[SessionResponse]:
    """List operator sessions with optional filters."""
    svc = _get_session_service(request)
    status_enum = OperatorSessionStatus(status) if status else None
    sessions = await svc.list_sessions(
        status=status_enum,
        limit=limit,
        tenant_id=_tenant_filter(request),
    )
    return [_session_to_response(s) for s in sessions]


@router.get("/incomplete", dependencies=[require_scope("sessions:read")])
async def list_incomplete_sessions(request: Request) -> list[SessionResponse]:
    """List sessions eligible for resume (crashed or suspended)."""
    svc = _get_session_service(request)
    tenant_id = _tenant_filter(request)
    crashed = await svc.detect_incomplete_sessions(tenant_id=tenant_id)
    suspended = await svc.list_sessions(
        status=OperatorSessionStatus.SUSPENDED,
        limit=50,
        tenant_id=tenant_id,
    )
    all_incomplete = crashed + suspended
    return [_session_to_response(s) for s in all_incomplete]


@router.get("/{session_id}", dependencies=[require_scope("sessions:read")])
async def get_session(session_id: str, request: Request) -> SessionResponse:
    """Get session details by ID."""
    _svc, session = await _get_accessible_session(request, session_id)
    return _session_to_response(session)


@router.post(
    "/{session_id}/resume",
    dependencies=[require_scope("sessions:write")],
)
async def resume_session(session_id: str, request: Request) -> SessionResponse:
    """Resume an incomplete session."""
    svc, _session = await _get_accessible_session(request, session_id)
    try:
        session = await svc.resume_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _session_to_response(session)


@router.post(
    "/{session_id}/end",
    dependencies=[require_scope("sessions:write")],
)
async def end_session(
    session_id: str,
    body: SessionEndRequest,
    request: Request,
) -> SessionResponse:
    """End an active session."""
    svc, _session = await _get_accessible_session(request, session_id)
    status_enum = OperatorSessionStatus(body.status)
    try:
        session = await svc.end_session(session_id, status=status_enum)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from None
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _session_to_response(session)


@router.post(
    "/{session_id}/checkpoint",
    dependencies=[require_scope("sessions:write")],
)
async def checkpoint_session(session_id: str, request: Request) -> dict[str, str]:
    """Trigger a manual checkpoint for the session."""
    svc, _session = await _get_accessible_session(request, session_id)
    try:
        await svc.checkpoint(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from None
    return {"status": "checkpointed", "session_id": session_id}


# ---------------------------------------------------------------------------
# Task endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{session_id}/tasks/",
    status_code=201,
    dependencies=[require_scope("sessions:write")],
)
async def add_task(
    session_id: str,
    body: TaskCreateRequest,
    request: Request,
) -> TaskResponse:
    """Add a task to the session."""
    svc, _session = await _get_accessible_session(request, session_id)
    try:
        task = await svc.add_task(session_id, description=body.description, metadata=body.metadata)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from None
    return _task_to_response(task)


@router.get(
    "/{session_id}/tasks/",
    dependencies=[require_scope("sessions:read")],
)
async def list_tasks(session_id: str, request: Request) -> list[TaskResponse]:
    """List all tasks for a session."""
    svc, _session = await _get_accessible_session(request, session_id)
    try:
        tasks = await svc.list_tasks(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found") from None
    return [_task_to_response(t) for t in tasks]


@router.put(
    "/{session_id}/tasks/{task_id}",
    dependencies=[require_scope("sessions:write")],
)
async def update_task(
    session_id: str,
    task_id: str,
    body: TaskUpdateRequest,
    request: Request,
) -> TaskResponse:
    """Update a task's status."""
    svc, _session = await _get_accessible_session(request, session_id)
    try:
        task = await svc.update_task(session_id, task_id, status=body.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    return _task_to_response(task)


# ---------------------------------------------------------------------------
# Replay endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{session_id}/replay/",
    dependencies=[require_scope("sessions:read")],
)
async def get_replay(
    session_id: str,
    request: Request,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[ReplayEventResponse]:
    """Get replay events with pagination."""
    svc, _session = await _get_accessible_session(request, session_id)
    events = await svc.get_replay(session_id, offset=offset, limit=limit)
    return [
        ReplayEventResponse(
            event_id=e.event_id,
            event_type=e.event_type.value,
            timestamp=e.timestamp,
            session_id=e.session_id,
            data=e.data,
            correlation_id=e.correlation_id,
        )
        for e in events
    ]


@router.get(
    "/{session_id}/replay/summary",
    dependencies=[require_scope("sessions:read")],
)
async def get_replay_summary(
    session_id: str,
    request: Request,
) -> ReplaySummaryResponse:
    """Get a summary of the session replay log."""
    svc, _session = await _get_accessible_session(request, session_id)
    summary = await svc.get_replay_summary(session_id)
    return ReplaySummaryResponse(**summary)
