"""Improvement service — orchestrates research intake, lessons, metrics, and checklists."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from agent33.improvement.checklists import ChecklistEvaluator, build_checklist
from agent33.improvement.metrics import MetricsTracker, default_metrics
from agent33.improvement.models import (
    ChecklistPeriod,
    ImprovementChecklist,
    IntakeClassification,
    IntakeContent,
    IntakeRelevance,
    IntakeStatus,
    LearningSignal,
    LearningSignalSeverity,
    LearningSignalType,
    LearningSummary,
    LessonActionStatus,
    LessonLearned,
    MetricsSnapshot,
    ResearchIntake,
    RoadmapRefresh,
)
from agent33.improvement.persistence import (
    InMemoryLearningSignalStore,
    LearningPersistenceState,
    LearningSignalStore,
)
from agent33.improvement.quality import enrich_learning_signal

logger = logging.getLogger(__name__)

_SEVERITY_RANK: dict[LearningSignalSeverity, int] = {
    LearningSignalSeverity.LOW: 1,
    LearningSignalSeverity.MEDIUM: 2,
    LearningSignalSeverity.HIGH: 3,
    LearningSignalSeverity.CRITICAL: 4,
}


# Valid intake status transitions
_INTAKE_TRANSITIONS: dict[IntakeStatus, set[IntakeStatus]] = {
    IntakeStatus.SUBMITTED: {IntakeStatus.TRIAGED},
    IntakeStatus.TRIAGED: {IntakeStatus.ANALYZING},
    IntakeStatus.ANALYZING: {
        IntakeStatus.ACCEPTED,
        IntakeStatus.DEFERRED,
        IntakeStatus.REJECTED,
    },
    IntakeStatus.ACCEPTED: {IntakeStatus.TRACKED},
    IntakeStatus.DEFERRED: {IntakeStatus.TRIAGED},  # can re-triage
    IntakeStatus.REJECTED: set(),
    IntakeStatus.TRACKED: set(),
}


class ImprovementService:
    """In-memory service for continuous improvement operations."""

    def __init__(self, learning_store: LearningSignalStore | None = None) -> None:
        self._intakes: dict[str, ResearchIntake] = {}
        self._lessons: dict[str, LessonLearned] = {}
        self._checklists: dict[str, ImprovementChecklist] = {}
        self._refreshes: dict[str, RoadmapRefresh] = {}
        self._learning_signals: dict[str, LearningSignal] = {}
        self._learning_signal_intake_map: dict[str, str] = {}
        self._learning_store = learning_store or InMemoryLearningSignalStore()
        self._load_learning_state()
        self._metrics_tracker = MetricsTracker()
        self._checklist_evaluator = ChecklistEvaluator()

    # ----- Research Intake -------------------------------------------------

    def submit_intake(self, intake: ResearchIntake) -> ResearchIntake:
        """Submit a new research intake."""
        intake.disposition.status = IntakeStatus.SUBMITTED
        self._intakes[intake.intake_id] = intake
        if intake.generated_from_signal_id is not None:
            self._persist_learning_state()
        logger.info("intake_submitted", intake_id=intake.intake_id)
        return intake

    def get_intake(self, intake_id: str) -> ResearchIntake | None:
        return self._intakes.get(intake_id)

    def list_intakes(
        self,
        status: IntakeStatus | None = None,
        research_type: str | None = None,
        tenant_id: str | None = None,
    ) -> list[ResearchIntake]:
        result = list(self._intakes.values())
        if status is not None:
            result = [i for i in result if i.disposition.status == status]
        if research_type is not None:
            result = [i for i in result if i.classification.research_type.value == research_type]
        if tenant_id is not None:
            result = [i for i in result if i.tenant_id == tenant_id]
        return result

    def transition_intake(
        self,
        intake_id: str,
        new_status: IntakeStatus,
        *,
        decision_by: str = "",
        rationale: str = "",
        action_items: list[str] | None = None,
    ) -> ResearchIntake:
        """Transition an intake through the lifecycle state machine."""
        intake = self._intakes.get(intake_id)
        if intake is None:
            raise ValueError(f"Intake {intake_id} not found")

        current = intake.disposition.status
        allowed = _INTAKE_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise ValueError(f"Cannot transition from {current.value} to {new_status.value}")

        intake.disposition.status = new_status
        if decision_by:
            intake.disposition.decision_by = decision_by
        if rationale:
            intake.disposition.rationale = rationale
        if action_items:
            intake.disposition.action_items = action_items
        if new_status in (
            IntakeStatus.ACCEPTED,
            IntakeStatus.DEFERRED,
            IntakeStatus.REJECTED,
        ):
            intake.disposition.decision_date = datetime.now(UTC)

        logger.info(
            "intake_transitioned",
            intake_id=intake_id,
            from_status=current.value,
            to_status=new_status.value,
        )
        if intake.generated_from_signal_id is not None:
            self._persist_learning_state()
        return intake

    # ----- Lessons Learned -------------------------------------------------

    def record_lesson(self, lesson: LessonLearned) -> LessonLearned:
        """Record a new lesson learned."""
        self._lessons[lesson.lesson_id] = lesson
        logger.info("lesson_recorded", lesson_id=lesson.lesson_id)
        return lesson

    def get_lesson(self, lesson_id: str) -> LessonLearned | None:
        return self._lessons.get(lesson_id)

    def list_lessons(
        self,
        phase: str | None = None,
        event_type: str | None = None,
    ) -> list[LessonLearned]:
        result = list(self._lessons.values())
        if phase is not None:
            result = [lesson for lesson in result if lesson.phase == phase]
        if event_type is not None:
            result = [lesson for lesson in result if lesson.event_type.value == event_type]
        return result

    def complete_lesson_action(
        self,
        lesson_id: str,
        action_index: int,
    ) -> LessonLearned:
        """Mark a specific action item as completed."""
        lesson = self._lessons.get(lesson_id)
        if lesson is None:
            raise ValueError(f"Lesson {lesson_id} not found")
        if action_index < 0 or action_index >= len(lesson.actions):
            raise ValueError(f"Action index {action_index} out of range")
        lesson.actions[action_index].status = LessonActionStatus.COMPLETED
        return lesson

    def verify_lesson(self, lesson_id: str, evidence: str = "") -> LessonLearned:
        """Mark a lesson as implemented and verified."""
        lesson = self._lessons.get(lesson_id)
        if lesson is None:
            raise ValueError(f"Lesson {lesson_id} not found")
        lesson.implemented = True
        lesson.verified_at = datetime.now(UTC)
        if evidence:
            lesson.evidence = evidence
        return lesson

    # ----- Improvement Checklists ------------------------------------------

    def create_checklist(
        self, period: ChecklistPeriod, reference: str = ""
    ) -> ImprovementChecklist:
        """Create a new periodic improvement checklist."""
        checklist = build_checklist(period, reference)
        self._checklists[checklist.checklist_id] = checklist
        return checklist

    def get_checklist(self, checklist_id: str) -> ImprovementChecklist | None:
        return self._checklists.get(checklist_id)

    def list_checklists(self, period: ChecklistPeriod | None = None) -> list[ImprovementChecklist]:
        result = list(self._checklists.values())
        if period is not None:
            result = [c for c in result if c.period == period]
        return result

    def complete_checklist_item(
        self,
        checklist_id: str,
        check_id: str,
        notes: str = "",
    ) -> ImprovementChecklist:
        """Mark a checklist item as completed."""
        checklist = self._checklists.get(checklist_id)
        if checklist is None:
            raise ValueError(f"Checklist {checklist_id} not found")
        item = self._checklist_evaluator.complete_item(checklist, check_id, notes)
        if item is None:
            raise ValueError(f"Check {check_id} not found in checklist")
        return checklist

    def evaluate_checklist(self, checklist_id: str) -> tuple[bool, list[str]]:
        """Evaluate a checklist for completion."""
        checklist = self._checklists.get(checklist_id)
        if checklist is None:
            raise ValueError(f"Checklist {checklist_id} not found")
        return self._checklist_evaluator.evaluate(checklist)

    # ----- Metrics ---------------------------------------------------------

    def save_metrics_snapshot(self, snapshot: MetricsSnapshot) -> MetricsSnapshot:
        """Save a metrics snapshot."""
        return self._metrics_tracker.save_snapshot(snapshot)

    def latest_metrics(self) -> MetricsSnapshot | None:
        """Return the latest metrics snapshot."""
        return self._metrics_tracker.latest()

    def list_metrics_snapshots(self, limit: int = 10) -> list[MetricsSnapshot]:
        return self._metrics_tracker.list_snapshots(limit)

    def get_metric_trend(self, metric_id: str, periods: int = 4) -> tuple[str, list[float]]:
        """Return (trend, values) for a metric."""
        trend, values = self._metrics_tracker.get_trend(metric_id, periods)
        return trend.value, values

    def create_default_snapshot(self, period: str = "") -> MetricsSnapshot:
        """Create a snapshot with the five canonical metrics at defaults."""
        snapshot = MetricsSnapshot(
            period=period,
            metrics=default_metrics(),
        )
        return self._metrics_tracker.save_snapshot(snapshot)

    # ----- Roadmap Refresh -------------------------------------------------

    def record_refresh(self, refresh: RoadmapRefresh) -> RoadmapRefresh:
        """Record a roadmap refresh event."""
        self._refreshes[refresh.refresh_id] = refresh
        logger.info(
            "roadmap_refresh_recorded",
            refresh_id=refresh.refresh_id,
            scope=refresh.scope.value,
        )
        return refresh

    def get_refresh(self, refresh_id: str) -> RoadmapRefresh | None:
        return self._refreshes.get(refresh_id)

    def list_refreshes(self, scope: str | None = None) -> list[RoadmapRefresh]:
        result = list(self._refreshes.values())
        if scope is not None:
            result = [r for r in result if r.scope.value == scope]
        return result

    def complete_refresh(
        self,
        refresh_id: str,
        outcome: str = "",
        changes: list[str] | None = None,
    ) -> RoadmapRefresh:
        """Mark a roadmap refresh as completed."""
        refresh = self._refreshes.get(refresh_id)
        if refresh is None:
            raise ValueError(f"Refresh {refresh_id} not found")
        refresh.completed_at = datetime.now(UTC)
        if outcome:
            refresh.outcome = outcome
        if changes:
            refresh.changes_made = changes
        return refresh

    # ----- Learning Signals -------------------------------------------------

    def record_learning_signal(self, signal: LearningSignal) -> LearningSignal:
        """Record a learning signal."""
        enrich_learning_signal(signal)
        self._learning_signals[signal.signal_id] = signal
        self._persist_learning_state()
        logger.info(
            "learning_signal_recorded",
            signal_id=signal.signal_id,
            signal_type=signal.signal_type.value,
            severity=signal.severity.value,
        )
        return signal

    def list_learning_signals(
        self,
        signal_type: LearningSignalType | None = None,
        severity: LearningSignalSeverity | None = None,
        limit: int | None = 50,
        tenant_id: str | None = None,
    ) -> list[LearningSignal]:
        """List learning signals with optional filters."""
        result = list(self._learning_signals.values())
        if signal_type is not None:
            result = [s for s in result if s.signal_type == signal_type]
        if severity is not None:
            result = [s for s in result if s.severity == severity]
        if tenant_id is not None:
            result = [s for s in result if s.tenant_id == tenant_id]
        result.sort(key=lambda s: s.recorded_at, reverse=True)
        if limit is None:
            return result
        return result[: max(0, limit)]

    def summarize_learning_signals(
        self,
        limit: int = 50,
        *,
        tenant_id: str | None = None,
        window_days: int | None = None,
    ) -> LearningSummary:
        """Summarize recent learning signals."""
        now = datetime.now(UTC)
        all_scoped = self.list_learning_signals(limit=None, tenant_id=tenant_id)
        summary_signals = all_scoped
        previous_window_total: int | None = None
        trend_delta: int | None = None
        trend_direction = "stable"
        window_start_at: datetime | None = None

        if window_days is not None and window_days > 0:
            window_start_at = now - timedelta(days=window_days)
            previous_window_start = window_start_at - timedelta(days=window_days)
            summary_signals = [
                signal for signal in all_scoped if signal.recorded_at >= window_start_at
            ]
            previous_window_total = len(
                [
                    signal
                    for signal in all_scoped
                    if previous_window_start <= signal.recorded_at < window_start_at
                ]
            )
            trend_delta = len(summary_signals) - previous_window_total
            if trend_delta > 0:
                trend_direction = "up"
            elif trend_delta < 0:
                trend_direction = "down"

        signals = summary_signals[: max(0, limit)]
        counts_by_type: dict[str, int] = {}
        counts_by_severity: dict[str, int] = {}
        counts_by_tenant: dict[str, int] = {}
        latest_recorded_at = signals[0].recorded_at if signals else None

        quality_total = 0.0
        high_quality_signals = 0
        for signal in signals:
            stype = signal.signal_type.value
            ssev = signal.severity.value
            counts_by_type[stype] = counts_by_type.get(stype, 0) + 1
            counts_by_severity[ssev] = counts_by_severity.get(ssev, 0) + 1
            counts_by_tenant[signal.tenant_id] = counts_by_tenant.get(signal.tenant_id, 0) + 1
            quality_total += signal.quality_score
            if signal.quality_label == "high":
                high_quality_signals += 1

        return LearningSummary(
            total_signals=len(signals),
            counts_by_type=counts_by_type,
            counts_by_severity=counts_by_severity,
            counts_by_tenant=counts_by_tenant,
            latest_recorded_at=latest_recorded_at,
            average_quality_score=(round(quality_total / len(signals), 3) if signals else 0.0),
            high_quality_signals=high_quality_signals,
            tenant_id=tenant_id,
            window_days=window_days,
            window_start_at=window_start_at,
            previous_window_total=previous_window_total,
            trend_delta=trend_delta,
            trend_direction=trend_direction,
        )

    def generate_intakes_from_learning_signals(
        self,
        *,
        min_severity: LearningSignalSeverity = LearningSignalSeverity.HIGH,
        max_items: int = 3,
        tenant_id: str | None = None,
    ) -> list[ResearchIntake]:
        """Generate research intakes from qualifying signals.

        Uses an internal idempotency map so each signal produces at most one intake.
        """
        if max_items <= 0:
            return []

        created: list[ResearchIntake] = []
        candidates = self.list_learning_signals(limit=None, tenant_id=tenant_id)
        candidates.sort(
            key=lambda signal: (
                _SEVERITY_RANK[signal.severity],
                signal.quality_score,
                signal.recorded_at,
            ),
            reverse=True,
        )
        for signal in candidates:
            if _SEVERITY_RANK[signal.severity] < _SEVERITY_RANK[min_severity]:
                continue
            if signal.signal_id in self._learning_signal_intake_map:
                continue

            urgency = (
                "high"
                if signal.severity
                in {LearningSignalSeverity.HIGH, LearningSignalSeverity.CRITICAL}
                else "medium"
            )
            priority_score = {
                LearningSignalSeverity.LOW: 3,
                LearningSignalSeverity.MEDIUM: 5,
                LearningSignalSeverity.HIGH: 8,
                LearningSignalSeverity.CRITICAL: 10,
            }[signal.severity]
            priority_score = min(
                10,
                max(1, priority_score + round(signal.quality_score * 2)),
            )

            intake = self.submit_intake(
                ResearchIntake(
                    submitted_by="learning-service",
                    tenant_id=signal.tenant_id,
                    generated_from_signal_id=signal.signal_id,
                    automated_quality_score=signal.quality_score,
                    automated_quality_label=signal.quality_label,
                    classification=IntakeClassification(
                        research_type="internal",
                        category=f"learning:{signal.signal_type.value}",
                        urgency=urgency,
                    ),
                    content=IntakeContent(
                        title=f"Learning signal: {signal.summary}",
                        summary=signal.details or signal.summary,
                        source=signal.source,
                    ),
                    relevance=IntakeRelevance(
                        priority_score=priority_score,
                        impact_areas=[f"quality:{signal.quality_label}"],
                    ),
                )
            )
            self._learning_signal_intake_map[signal.signal_id] = intake.intake_id
            signal.related_intake_id = intake.intake_id
            signal.intake_generated = True
            created.append(intake)
            if len(created) >= max_items:
                break
        if created:
            self._persist_learning_state()
        return created

    def _load_learning_state(self) -> None:
        state = self._learning_store.load()
        self._learning_signals = {signal.signal_id: signal for signal in state.signals}
        self._learning_signal_intake_map = dict(state.signal_intake_map)
        for intake in state.generated_intakes:
            self._intakes[intake.intake_id] = intake

    def _persist_learning_state(self) -> None:
        generated_intakes = [
            intake
            for intake in self._intakes.values()
            if intake.generated_from_signal_id is not None
        ]
        signals = sorted(self._learning_signals.values(), key=lambda signal: signal.signal_id)
        generated_intakes.sort(key=lambda intake: intake.intake_id)
        self._learning_store.save(
            LearningPersistenceState(
                signals=signals,
                generated_intakes=generated_intakes,
                signal_intake_map=dict(self._learning_signal_intake_map),
            )
        )
