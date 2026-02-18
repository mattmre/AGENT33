"""Domain models for outcomes events, trends, and dashboard views."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class OutcomeMetricType(StrEnum):
    """Supported metric families for outcome events."""

    SUCCESS_RATE = "success_rate"
    QUALITY_SCORE = "quality_score"
    LATENCY_MS = "latency_ms"
    COST_USD = "cost_usd"


class TrendDirection(StrEnum):
    """Direction values for trends."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class OutcomeEventCreate(BaseModel):
    """Request payload used to record an outcome event."""

    domain: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    metric_type: OutcomeMetricType
    value: float
    occurred_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutcomeEvent(BaseModel):
    """Tenant-scoped event record for outcome metrics."""

    id: str = Field(default_factory=lambda: _new_id("outcome"))
    tenant_id: str = ""
    domain: str
    event_type: str
    metric_type: OutcomeMetricType
    value: float
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutcomeTrend(BaseModel):
    """Trend contract for a single metric + domain window query."""

    metric_type: OutcomeMetricType
    domain: str = "all"
    window: int = Field(default=20, ge=1)
    direction: TrendDirection = TrendDirection.STABLE
    sample_size: int = 0
    values: list[float] = Field(default_factory=list)
    previous_avg: float = 0.0
    current_avg: float = 0.0


class OutcomeSummary(BaseModel):
    """Summary payload used by dashboard responses."""

    total_events: int = 0
    domains: list[str] = Field(default_factory=list)
    event_types: list[str] = Field(default_factory=list)
    metric_counts: dict[str, int] = Field(default_factory=dict)


class OutcomeDashboard(BaseModel):
    """Dashboard contract with trend snapshots and recent events."""

    trends: list[OutcomeTrend] = Field(default_factory=list)
    recent_events: list[OutcomeEvent] = Field(default_factory=list)
    summary: OutcomeSummary = Field(default_factory=OutcomeSummary)
