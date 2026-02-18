"""FastAPI routes for outcome metrics events and dashboards."""

from typing import Any

from fastapi import APIRouter, Request

from agent33.outcomes.models import OutcomeEventCreate, OutcomeMetricType
from agent33.outcomes.service import OutcomesService
from agent33.security.permissions import require_scope

router = APIRouter(prefix="/v1/outcomes", tags=["outcomes"])
_service = OutcomesService()


def get_outcomes_service() -> OutcomesService:
    """Return singleton outcomes service."""
    return _service


def _tenant_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        return ""
    return getattr(user, "tenant_id", "")


@router.post("/events", status_code=201, dependencies=[require_scope("outcomes:write")])
async def record_event(body: OutcomeEventCreate, request: Request) -> dict[str, Any]:
    event = _service.record_event(tenant_id=_tenant_id(request), event=body)
    return event.model_dump(mode="json")


@router.get("/events", dependencies=[require_scope("outcomes:read")])
async def list_events(
    request: Request,
    domain: str | None = None,
    event_type: str | None = None,
    metric_type: OutcomeMetricType | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    events = _service.list_events(
        tenant_id=_tenant_id(request),
        domain=domain,
        event_type=event_type,
        metric_type=metric_type,
        limit=limit,
    )
    return [event.model_dump(mode="json") for event in events]


@router.get("/trends/{metric_type}", dependencies=[require_scope("outcomes:read")])
async def get_trend(
    metric_type: OutcomeMetricType,
    request: Request,
    domain: str | None = None,
    window: int = 20,
) -> dict[str, Any]:
    trend = _service.compute_trend(
        tenant_id=_tenant_id(request),
        metric_type=metric_type,
        domain=domain,
        window=window,
    )
    return trend.model_dump(mode="json")


@router.get("/dashboard", dependencies=[require_scope("outcomes:read")])
async def get_dashboard(
    request: Request,
    domain: str | None = None,
    window: int = 20,
    recent_limit: int = 10,
) -> dict[str, Any]:
    dashboard = _service.get_dashboard(
        tenant_id=_tenant_id(request),
        domain=domain,
        window=window,
        recent_limit=recent_limit,
    )
    return dashboard.model_dump(mode="json")
