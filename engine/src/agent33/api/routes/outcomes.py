"""FastAPI routes for outcome metrics events and dashboards."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request

from agent33.outcomes.models import (
    OutcomeEventCreate,
    OutcomeMetricType,
    PackImpactEntry,
    PackImpactResponse,
    ROIRequest,
    ROIResponse,
)
from agent33.outcomes.service import OutcomesService
from agent33.security.permissions import require_scope

if TYPE_CHECKING:
    from agent33.packs.registry import PackRegistry

router = APIRouter(prefix="/v1/outcomes", tags=["outcomes"])

# Module-level fallback; replaced by lifespan via set_outcomes_service().
_service = OutcomesService()


def set_outcomes_service(service: OutcomesService) -> None:
    """Swap the module-level outcomes service (called from lifespan)."""
    global _service
    _service = service


def get_outcomes_service(request: Request) -> OutcomesService:
    """Return the outcomes service from app.state, falling back to module-level."""
    svc: OutcomesService | None = getattr(request.app.state, "outcomes_service", None)
    return svc if svc is not None else _service


def _tenant_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        return ""
    return getattr(user, "tenant_id", "")


@router.post("/events", status_code=201, dependencies=[require_scope("outcomes:write")])
async def record_event(body: OutcomeEventCreate, request: Request) -> dict[str, Any]:
    service = get_outcomes_service(request)
    event = service.record_event(tenant_id=_tenant_id(request), event=body)
    return event.model_dump(mode="json")


@router.get("/events", dependencies=[require_scope("outcomes:read")])
async def list_events(
    request: Request,
    domain: str | None = None,
    event_type: str | None = None,
    metric_type: OutcomeMetricType | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    service = get_outcomes_service(request)
    events = service.list_events(
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
    service = get_outcomes_service(request)
    trend = service.compute_trend(
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
    service = get_outcomes_service(request)
    dashboard = service.get_dashboard(
        tenant_id=_tenant_id(request),
        domain=domain,
        window=window,
        recent_limit=recent_limit,
    )
    return dashboard.model_dump(mode="json")


@router.post("/roi", dependencies=[require_scope("outcomes:read")])
async def compute_roi(body: ROIRequest, request: Request) -> dict[str, Any]:
    """Compute ROI estimate for a domain over a time window."""
    service = get_outcomes_service(request)
    result = service.compute_roi(
        tenant_id=_tenant_id(request),
        domain=body.domain,
        hours_saved_per_success=body.hours_saved_per_success,
        cost_per_hour_usd=body.cost_per_hour_usd,
        window_days=body.window_days,
    )
    return ROIResponse(**result).model_dump(mode="json")


@router.get("/pack-impact", dependencies=[require_scope("outcomes:read")])
async def get_pack_impact(request: Request) -> dict[str, Any]:
    """Compute pack impact by cross-referencing session packs with outcome events."""
    service = get_outcomes_service(request)
    tenant_id = _tenant_id(request)

    # Get pack registry from app.state (optional)
    pack_registry: PackRegistry | None = getattr(request.app.state, "pack_registry", None)
    if pack_registry is None:
        return PackImpactResponse(packs=[]).model_dump(mode="json")

    # Build session -> pack names mapping
    session_packs: dict[str, set[str]] = dict(pack_registry._session_enabled)

    # Get all in-memory success_rate events for this tenant
    success_events = service._filter_events(
        tenant_id=tenant_id, metric_type=OutcomeMetricType.SUCCESS_RATE
    )

    # Group success events by session_id (from metadata)
    session_outcomes: dict[str, list[float]] = {}
    no_session_outcomes: list[float] = []
    for ev in success_events:
        sid = ev.metadata.get("session_id")
        if isinstance(sid, str) and sid:
            session_outcomes.setdefault(sid, []).append(ev.value)
        else:
            no_session_outcomes.append(ev.value)

    # For each known pack, compute success rates with vs without
    all_pack_names: set[str] = set()
    for packs in session_packs.values():
        all_pack_names.update(packs)

    entries: list[PackImpactEntry] = []
    for pack_name in sorted(all_pack_names):
        with_pack_values: list[float] = []
        without_pack_values: list[float] = list(no_session_outcomes)

        for sid, outcomes in session_outcomes.items():
            if pack_name in session_packs.get(sid, set()):
                with_pack_values.extend(outcomes)
            else:
                without_pack_values.extend(outcomes)

        sessions_applied = sum(1 for sid, packs in session_packs.items() if pack_name in packs)
        rate_with = (
            sum(1 for v in with_pack_values if v >= 1.0) / len(with_pack_values)
            if with_pack_values
            else 0.0
        )
        rate_without = (
            sum(1 for v in without_pack_values if v >= 1.0) / len(without_pack_values)
            if without_pack_values
            else 0.0
        )
        entries.append(
            PackImpactEntry(
                pack_name=pack_name,
                sessions_applied=sessions_applied,
                success_rate_with_pack=round(rate_with, 4),
                success_rate_without_pack=round(rate_without, 4),
                delta=round(rate_with - rate_without, 4),
            )
        )

    return PackImpactResponse(packs=entries).model_dump(mode="json")
