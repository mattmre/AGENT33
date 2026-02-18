"""In-memory outcomes service for event tracking and trend dashboards."""

from __future__ import annotations

from datetime import UTC, datetime

from agent33.outcomes.models import (
    OutcomeDashboard,
    OutcomeEvent,
    OutcomeEventCreate,
    OutcomeMetricType,
    OutcomeSummary,
    OutcomeTrend,
    TrendDirection,
)


class OutcomesService:
    """Store tenant-scoped outcome events and derive trend views."""

    def __init__(self) -> None:
        self._events: dict[str, OutcomeEvent] = {}

    def record_event(self, *, tenant_id: str, event: OutcomeEventCreate) -> OutcomeEvent:
        """Record an outcome event under a tenant."""
        created = OutcomeEvent(
            tenant_id=tenant_id,
            domain=event.domain,
            event_type=event.event_type,
            metric_type=event.metric_type,
            value=event.value,
            occurred_at=event.occurred_at or datetime.now(UTC),
            metadata=dict(event.metadata),
        )
        self._events[created.id] = created
        return created

    def list_events(
        self,
        *,
        tenant_id: str,
        domain: str | None = None,
        event_type: str | None = None,
        metric_type: OutcomeMetricType | None = None,
        limit: int = 50,
    ) -> list[OutcomeEvent]:
        """List tenant-scoped events with optional domain/event/metric filters."""
        events = self._filter_events(
            tenant_id=tenant_id,
            domain=domain,
            event_type=event_type,
            metric_type=metric_type,
        )
        events.sort(key=lambda item: item.occurred_at, reverse=True)
        return events[: max(limit, 0)]

    def compute_trend(
        self,
        *,
        tenant_id: str,
        metric_type: OutcomeMetricType,
        domain: str | None = None,
        window: int = 20,
    ) -> OutcomeTrend:
        """Compute trend direction for metric/domain over the requested window."""
        events = self._filter_events(
            tenant_id=tenant_id,
            domain=domain,
            metric_type=metric_type,
        )
        events.sort(key=lambda item: item.occurred_at)
        window = max(window, 1)
        values = [item.value for item in events[-window:]]

        if len(values) < 2:
            previous_avg = values[-1] if values else 0.0
            current_avg = previous_avg
            direction = TrendDirection.STABLE
        else:
            midpoint = len(values) // 2
            previous = values[:midpoint]
            current = values[midpoint:]
            previous_avg = sum(previous) / len(previous)
            current_avg = sum(current) / len(current)
            direction = self._compute_direction(metric_type, previous_avg, current_avg)

        return OutcomeTrend(
            metric_type=metric_type,
            domain=domain or "all",
            window=window,
            direction=direction,
            sample_size=len(values),
            values=values,
            previous_avg=previous_avg,
            current_avg=current_avg,
        )

    def get_dashboard(
        self,
        *,
        tenant_id: str,
        domain: str | None = None,
        window: int = 20,
        recent_limit: int = 10,
    ) -> OutcomeDashboard:
        """Return dashboard payload with trends, recent events, and summary."""
        filtered = self._filter_events(tenant_id=tenant_id, domain=domain)
        recent_events = sorted(filtered, key=lambda item: item.occurred_at, reverse=True)[
            : max(recent_limit, 0)
        ]

        metric_counts: dict[str, int] = {}
        for metric in OutcomeMetricType:
            metric_counts[metric.value] = len(
                [item for item in filtered if item.metric_type == metric]
            )

        summary = OutcomeSummary(
            total_events=len(filtered),
            domains=sorted({item.domain for item in filtered}),
            event_types=sorted({item.event_type for item in filtered}),
            metric_counts=metric_counts,
        )

        trends = [
            self.compute_trend(
                tenant_id=tenant_id,
                metric_type=metric,
                domain=domain,
                window=window,
            )
            for metric in OutcomeMetricType
        ]
        return OutcomeDashboard(trends=trends, recent_events=recent_events, summary=summary)

    def _filter_events(
        self,
        *,
        tenant_id: str,
        domain: str | None = None,
        event_type: str | None = None,
        metric_type: OutcomeMetricType | None = None,
    ) -> list[OutcomeEvent]:
        events = [item for item in self._events.values() if item.tenant_id == tenant_id]
        if domain is not None:
            events = [item for item in events if item.domain == domain]
        if event_type is not None:
            events = [item for item in events if item.event_type == event_type]
        if metric_type is not None:
            events = [item for item in events if item.metric_type == metric_type]
        return events

    @staticmethod
    def _compute_direction(
        metric_type: OutcomeMetricType, previous_avg: float, current_avg: float
    ) -> TrendDirection:
        delta = current_avg - previous_avg
        if metric_type in {OutcomeMetricType.LATENCY_MS, OutcomeMetricType.COST_USD}:
            delta = -delta

        baseline = abs(previous_avg) or 1.0
        ratio = delta / baseline
        if ratio > 0.05:
            return TrendDirection.IMPROVING
        if ratio < -0.05:
            return TrendDirection.DECLINING
        return TrendDirection.STABLE
