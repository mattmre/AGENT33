"""Session analytics and insights API routes.

Phase 57 -- Hermes Adoption Roadmap.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from agent33.observability.insights import InsightsEngine, InsightsReport
from agent33.observability.metrics import CostTracker, MetricsCollector
from agent33.security.permissions import require_scope

router = APIRouter(prefix="/v1/insights", tags=["insights"])

# Module-level singletons; replaced at app startup via set_insights_engine().
_metrics = MetricsCollector()
_cost_tracker: CostTracker | None = None
_engine = InsightsEngine(_metrics, _cost_tracker)


def set_insights_engine(engine: InsightsEngine) -> None:
    """Swap the global insights engine (called during app init)."""
    global _engine
    _engine = engine


def set_insights_dependencies(
    metrics: MetricsCollector,
    cost_tracker: CostTracker | None = None,
) -> None:
    """Set the metrics collector and cost tracker, rebuilding the engine."""
    global _metrics, _cost_tracker, _engine
    _metrics = metrics
    _cost_tracker = cost_tracker
    _engine = InsightsEngine(_metrics, _cost_tracker)


def _serialize_report(report: InsightsReport) -> dict[str, Any]:
    """Convert an InsightsReport to a JSON-safe dictionary."""
    return {
        "total_sessions": report.total_sessions,
        "total_tokens": report.total_tokens,
        "total_cost_usd": float(report.total_cost_usd),
        "avg_session_duration_seconds": report.avg_session_duration_seconds,
        "tool_usage": report.tool_usage,
        "model_usage": report.model_usage,
        "daily_activity": report.daily_activity,
        "period_days": report.period_days,
        "generated_at": report.generated_at,
    }


@router.get(
    "",
    dependencies=[require_scope("agents:read")],
)
async def get_insights(
    days: int = Query(default=30, ge=1, le=365, description="Lookback period in days"),
    tenant_id: str | None = Query(default=None, description="Optional tenant filter"),
) -> dict[str, Any]:
    """Return a consolidated analytics report.

    Aggregates session counts, token usage, cost attribution, tool/model
    breakdowns, and daily activity histograms for the requested period.
    """
    report = _engine.generate(days=days, tenant_id=tenant_id)
    return _serialize_report(report)
