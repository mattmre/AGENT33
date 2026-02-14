"""Improvement service — orchestrates research intake, lessons, metrics, and checklists."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from agent33.improvement.checklists import ChecklistEvaluator, build_checklist
from agent33.improvement.metrics import MetricsTracker, default_metrics
from agent33.improvement.models import (
    ChecklistPeriod,
    ImprovementChecklist,
    IntakeStatus,
    LessonActionStatus,
    LessonLearned,
    MetricsSnapshot,
    ResearchIntake,
    RoadmapRefresh,
)

logger = logging.getLogger(__name__)


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

    def __init__(self) -> None:
        self._intakes: dict[str, ResearchIntake] = {}
        self._lessons: dict[str, LessonLearned] = {}
        self._checklists: dict[str, ImprovementChecklist] = {}
        self._refreshes: dict[str, RoadmapRefresh] = {}
        self._metrics_tracker = MetricsTracker()
        self._checklist_evaluator = ChecklistEvaluator()

    # ----- Research Intake -------------------------------------------------

    def submit_intake(self, intake: ResearchIntake) -> ResearchIntake:
        """Submit a new research intake."""
        intake.disposition.status = IntakeStatus.SUBMITTED
        self._intakes[intake.intake_id] = intake
        logger.info("intake_submitted", intake_id=intake.intake_id)
        return intake

    def get_intake(self, intake_id: str) -> ResearchIntake | None:
        return self._intakes.get(intake_id)

    def list_intakes(
        self,
        status: IntakeStatus | None = None,
        research_type: str | None = None,
    ) -> list[ResearchIntake]:
        result = list(self._intakes.values())
        if status is not None:
            result = [
                i for i in result if i.disposition.status == status
            ]
        if research_type is not None:
            result = [
                i
                for i in result
                if i.classification.research_type.value == research_type
            ]
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
            raise ValueError(
                f"Cannot transition from {current.value} to {new_status.value}"
            )

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
            result = [
                lesson for lesson in result if lesson.phase == phase
            ]
        if event_type is not None:
            result = [
                lesson
                for lesson in result
                if lesson.event_type.value == event_type
            ]
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

    def verify_lesson(
        self, lesson_id: str, evidence: str = ""
    ) -> LessonLearned:
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

    def list_checklists(
        self, period: ChecklistPeriod | None = None
    ) -> list[ImprovementChecklist]:
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
        item = self._checklist_evaluator.complete_item(
            checklist, check_id, notes
        )
        if item is None:
            raise ValueError(f"Check {check_id} not found in checklist")
        return checklist

    def evaluate_checklist(
        self, checklist_id: str
    ) -> tuple[bool, list[str]]:
        """Evaluate a checklist for completion."""
        checklist = self._checklists.get(checklist_id)
        if checklist is None:
            raise ValueError(f"Checklist {checklist_id} not found")
        return self._checklist_evaluator.evaluate(checklist)

    # ----- Metrics ---------------------------------------------------------

    def save_metrics_snapshot(
        self, snapshot: MetricsSnapshot
    ) -> MetricsSnapshot:
        """Save a metrics snapshot."""
        return self._metrics_tracker.save_snapshot(snapshot)

    def latest_metrics(self) -> MetricsSnapshot | None:
        """Return the latest metrics snapshot."""
        return self._metrics_tracker.latest()

    def list_metrics_snapshots(
        self, limit: int = 10
    ) -> list[MetricsSnapshot]:
        return self._metrics_tracker.list_snapshots(limit)

    def get_metric_trend(
        self, metric_id: str, periods: int = 4
    ) -> tuple[str, list[float]]:
        """Return (trend, values) for a metric."""
        trend, values = self._metrics_tracker.get_trend(metric_id, periods)
        return trend.value, values

    def create_default_snapshot(
        self, period: str = ""
    ) -> MetricsSnapshot:
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

    def list_refreshes(
        self, scope: str | None = None
    ) -> list[RoadmapRefresh]:
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
