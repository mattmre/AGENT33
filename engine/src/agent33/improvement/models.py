"""Data models for continuous improvement, research intake, and lessons learned."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ResearchType(StrEnum):
    """Research intake classification type."""

    EXTERNAL = "external"
    INTERNAL = "internal"
    COMPETITIVE = "competitive"
    USER = "user"
    TECHNICAL = "technical"


class ResearchUrgency(StrEnum):
    """Urgency level for research intake."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IntakeStatus(StrEnum):
    """Research intake lifecycle status."""

    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    ANALYZING = "analyzing"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    REJECTED = "rejected"
    TRACKED = "tracked"


class LessonEventType(StrEnum):
    """What kind of event triggered the lesson."""

    SUCCESS = "success"
    FAILURE = "failure"
    OBSERVATION = "observation"


class LessonActionStatus(StrEnum):
    """Status of a lesson-learned action item."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    WONT_FIX = "wont_fix"


class MetricTrend(StrEnum):
    """Direction of a metric over time."""

    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class ChecklistPeriod(StrEnum):
    """Which periodic checklist this belongs to."""

    PER_RELEASE = "per_release"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class RefreshScope(StrEnum):
    """Roadmap refresh scope."""

    MICRO = "micro"
    MINOR = "minor"
    MAJOR = "major"
    AD_HOC = "ad_hoc"


# ---------------------------------------------------------------------------
# Research Intake models
# ---------------------------------------------------------------------------


class IntakeClassification(BaseModel):
    """Classification section of a research intake."""

    research_type: ResearchType = ResearchType.EXTERNAL
    category: str = ""
    urgency: ResearchUrgency = ResearchUrgency.MEDIUM


class IntakeContent(BaseModel):
    """Content section of a research intake."""

    title: str
    summary: str = ""
    source: str = ""
    source_date: str = ""


class IntakeRelevance(BaseModel):
    """Relevance section of a research intake."""

    impact_areas: list[str] = Field(default_factory=list)
    affected_phases: list[int] = Field(default_factory=list)
    affected_agents: list[str] = Field(default_factory=list)
    priority_score: int = 5  # 1-10


class IntakeAnalysis(BaseModel):
    """Analysis section of a research intake."""

    key_findings: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)


class IntakeDisposition(BaseModel):
    """Disposition section of a research intake."""

    status: IntakeStatus = IntakeStatus.SUBMITTED
    decision_date: datetime | None = None
    decision_by: str = ""
    rationale: str = ""
    action_items: list[str] = Field(default_factory=list)


class IntakeTracking(BaseModel):
    """Tracking section of a research intake."""

    backlog_refs: list[str] = Field(default_factory=list)
    roadmap_impact: str = "tbd"  # yes | no | tbd
    implementation_target: str = ""


class ResearchIntake(BaseModel):
    """A research intake record (RI-*)."""

    intake_id: str = Field(default_factory=lambda: _new_id("RI"))
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    submitted_by: str = ""

    classification: IntakeClassification = Field(
        default_factory=IntakeClassification,
    )
    content: IntakeContent = Field(
        default_factory=lambda: IntakeContent(title="Untitled"),
    )
    relevance: IntakeRelevance = Field(default_factory=IntakeRelevance)
    analysis: IntakeAnalysis = Field(default_factory=IntakeAnalysis)
    disposition: IntakeDisposition = Field(default_factory=IntakeDisposition)
    tracking: IntakeTracking = Field(default_factory=IntakeTracking)


# ---------------------------------------------------------------------------
# Lessons Learned models
# ---------------------------------------------------------------------------


class LessonAction(BaseModel):
    """An action item attached to a lesson learned."""

    description: str
    status: LessonActionStatus = LessonActionStatus.PENDING
    owner: str = ""
    target_date: str = ""


class LessonLearned(BaseModel):
    """A lesson-learned record (LL-*)."""

    lesson_id: str = Field(default_factory=lambda: _new_id("LL"))
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    recorded_by: str = ""

    # Context
    phase: str = ""
    release: str = ""
    event_type: LessonEventType = LessonEventType.OBSERVATION

    # Description
    what_happened: str = ""
    root_cause: str = ""
    impact: str = ""

    # Learning
    insight: str = ""
    recommendation: str = ""
    applies_to: list[str] = Field(default_factory=list)

    # Actions
    actions: list[LessonAction] = Field(default_factory=list)

    # Verification
    implemented: bool = False
    verified_at: datetime | None = None
    evidence: str = ""


# ---------------------------------------------------------------------------
# Improvement Metrics
# ---------------------------------------------------------------------------


class ImprovementMetric(BaseModel):
    """A single improvement metric value (IM-01..IM-05)."""

    metric_id: str
    name: str
    baseline: float = 0.0
    current: float = 0.0
    target: float = 0.0
    unit: str = ""
    trend: MetricTrend = MetricTrend.STABLE


class MetricsSnapshot(BaseModel):
    """A point-in-time snapshot of all improvement metrics."""

    snapshot_id: str = Field(default_factory=lambda: _new_id("MSN"))
    period: str = ""  # e.g. "2026-Q1"
    captured_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metrics: list[ImprovementMetric] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Improvement Checklists
# ---------------------------------------------------------------------------


class ChecklistItem(BaseModel):
    """A single improvement checklist item (CI-01..CI-15)."""

    check_id: str
    name: str
    completed: bool = False
    notes: str = ""


class ImprovementChecklist(BaseModel):
    """A periodic improvement checklist."""

    checklist_id: str = Field(default_factory=lambda: _new_id("CKL"))
    period: ChecklistPeriod
    reference: str = ""  # e.g. release version or "2026-01"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    items: list[ChecklistItem] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Roadmap Refresh
# ---------------------------------------------------------------------------


class RoadmapRefresh(BaseModel):
    """A roadmap refresh event record."""

    refresh_id: str = Field(default_factory=lambda: _new_id("RMR"))
    scope: RefreshScope = RefreshScope.MICRO
    scheduled_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    participants: list[str] = Field(default_factory=list)
    activities: list[str] = Field(default_factory=list)
    outcome: str = ""
    changes_made: list[str] = Field(default_factory=list)
