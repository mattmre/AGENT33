"""FastAPI routes for outcome metrics events and dashboards."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from agent33.evaluation.ppack_ab_models import (
    GitHubIssuePublishResult,
)
from agent33.evaluation.ppack_ab_persistence import PPackABPersistence
from agent33.evaluation.ppack_ab_service import PPackABService
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
_ppack_ab_service = PPackABService(
    outcomes_service=_service,
    persistence=PPackABPersistence(":memory:"),
)


def set_outcomes_service(service: OutcomesService) -> None:
    """Swap the module-level outcomes service (called from lifespan)."""
    global _service
    _service = service


def set_ppack_ab_service(service: PPackABService) -> None:
    """Swap the module-level P-PACK A/B service (called from lifespan)."""
    global _ppack_ab_service
    _ppack_ab_service = service


def get_outcomes_service(request: Request) -> OutcomesService:
    """Return the outcomes service from app.state, falling back to module-level."""
    svc: OutcomesService | None = getattr(request.app.state, "outcomes_service", None)
    return svc if svc is not None else _service


def get_ppack_ab_service(request: Request) -> PPackABService:
    """Return the P-PACK A/B service from app.state, falling back to module-level."""
    svc: PPackABService | None = getattr(request.app.state, "ppack_ab_service", None)
    return svc if svc is not None else _ppack_ab_service


def _tenant_id(request: Request) -> str:
    user = getattr(request.state, "user", None)
    if user is None:
        return ""
    return getattr(user, "tenant_id", "")


class PPackABAssignmentRequest(BaseModel):
    session_id: str = Field(min_length=1)


class PPackABReportRequest(BaseModel):
    domain: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    metric_types: list[OutcomeMetricType] = Field(
        default_factory=lambda: [
            OutcomeMetricType.SUCCESS_RATE,
            OutcomeMetricType.QUALITY_SCORE,
            OutcomeMetricType.LATENCY_MS,
            OutcomeMetricType.COST_USD,
        ]
    )
    open_github_issue: bool = False


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


@router.post(
    "/ppack-v3/assignments",
    status_code=201,
    dependencies=[require_scope("outcomes:write")],
)
async def assign_ppack_variant(
    body: PPackABAssignmentRequest,
    request: Request,
) -> dict[str, Any]:
    try:
        assignment = get_ppack_ab_service(request).assign_variant(
            tenant_id=_tenant_id(request),
            session_id=body.session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return assignment.model_dump(mode="json")


@router.get(
    "/ppack-v3/assignments/{session_id}",
    dependencies=[require_scope("outcomes:read")],
)
async def get_ppack_assignment(session_id: str, request: Request) -> dict[str, Any]:
    assignment = get_ppack_ab_service(request).get_assignment(
        tenant_id=_tenant_id(request),
        session_id=session_id,
    )
    if assignment is None:
        raise HTTPException(status_code=404, detail="P-PACK v3 assignment not found")
    return assignment.model_dump(mode="json")


@router.post(
    "/ppack-v3/report",
    dependencies=[require_scope("outcomes:read")],
)
async def generate_ppack_report(
    body: PPackABReportRequest,
    request: Request,
) -> dict[str, Any]:
    service = get_ppack_ab_service(request)
    try:
        report = service.generate_report(
            tenant_id=_tenant_id(request),
            domain=body.domain,
            since=body.since,
            until=body.until,
            metric_types=body.metric_types,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    issue_result = GitHubIssuePublishResult(reason="GitHub alert not requested")
    if body.open_github_issue:
        issue_result = await service.publish_github_issue(report)
    payload = report.model_dump(mode="json")
    payload["github_issue"] = issue_result.model_dump(mode="json")
    return payload


@router.get(
    "/ppack-v3/reports/{report_id}",
    dependencies=[require_scope("outcomes:read")],
)
async def get_ppack_report(report_id: str, request: Request) -> dict[str, Any]:
    report = get_ppack_ab_service(request).get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="P-PACK v3 report not found")
    return report.model_dump(mode="json")
