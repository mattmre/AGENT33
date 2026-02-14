"""Review service: orchestrates the two-layer review lifecycle.

Provides CRUD, risk assessment, reviewer assignment, and state transitions
for :class:`ReviewRecord` instances.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from agent33.review.assignment import ReviewerAssigner
from agent33.review.models import (
    FinalSignoff,
    L1ChecklistResults,
    L2ChecklistResults,
    ReviewDecision,
    ReviewRecord,
    RiskTrigger,
    SignoffState,
)
from agent33.review.risk import RiskAssessor
from agent33.review.state_machine import InvalidTransitionError, SignoffStateMachine

logger = logging.getLogger(__name__)


class ReviewNotFoundError(Exception):
    """Raised when a review record is not found."""


class ReviewStateError(Exception):
    """Raised when an operation is invalid for the current review state."""


class ReviewService:
    """In-memory review lifecycle manager.

    Thread-safety note: the service is *not* thread-safe.  For concurrent
    access behind an async web server this is acceptable because the event
    loop is single-threaded.
    """

    def __init__(self) -> None:
        self._reviews: dict[str, ReviewRecord] = {}
        self._risk_assessor = RiskAssessor()
        self._assigner = ReviewerAssigner()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(
        self,
        task_id: str,
        branch: str = "",
        pr_number: int | None = None,
        tenant_id: str = "",
    ) -> ReviewRecord:
        """Create a new review record in DRAFT state."""
        record = ReviewRecord(
            task_id=task_id,
            branch=branch,
            pr_number=pr_number,
            tenant_id=tenant_id,
        )
        self._reviews[record.id] = record
        logger.info("review_created id=%s task=%s", record.id, task_id)
        return record

    def get(self, review_id: str) -> ReviewRecord:
        """Retrieve a review by ID or raise :class:`ReviewNotFoundError`."""
        record = self._reviews.get(review_id)
        if record is None:
            raise ReviewNotFoundError(f"Review not found: {review_id}")
        return record

    def list_all(self, tenant_id: str | None = None) -> list[ReviewRecord]:
        """Return all reviews, optionally filtered by tenant."""
        if tenant_id is not None:
            return [r for r in self._reviews.values() if r.tenant_id == tenant_id]
        return list(self._reviews.values())

    def delete(self, review_id: str) -> None:
        """Remove a review record."""
        if review_id not in self._reviews:
            raise ReviewNotFoundError(f"Review not found: {review_id}")
        del self._reviews[review_id]
        logger.info("review_deleted id=%s", review_id)

    # ------------------------------------------------------------------
    # Risk assessment
    # ------------------------------------------------------------------

    def assess_risk(
        self,
        review_id: str,
        triggers: list[RiskTrigger],
    ) -> ReviewRecord:
        """Run risk assessment and update the review record."""
        record = self.get(review_id)
        assessment = self._risk_assessor.assess(triggers)
        record.risk_assessment = assessment
        record.touch()
        logger.info(
            "risk_assessed id=%s level=%s l1=%s l2=%s",
            review_id,
            assessment.risk_level.value,
            assessment.l1_required,
            assessment.l2_required,
        )
        return record

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def _transition(self, record: ReviewRecord, to_state: SignoffState) -> None:
        """Apply a state transition, raising on invalid moves."""
        try:
            new_state = SignoffStateMachine.transition(record.state, to_state)
        except InvalidTransitionError as exc:
            raise ReviewStateError(str(exc)) from exc
        record.state = new_state
        record.touch()

    def mark_ready(self, review_id: str) -> ReviewRecord:
        """Move review from DRAFT to READY."""
        record = self.get(review_id)
        self._transition(record, SignoffState.READY)
        return record

    def assign_l1(self, review_id: str) -> ReviewRecord:
        """Assign an L1 reviewer and move to L1_REVIEW."""
        record = self.get(review_id)
        self._transition(record, SignoffState.L1_REVIEW)

        l1, _ = self._assigner.assign(record.risk_assessment.triggers_identified)
        record.l1_review.reviewer_id = l1.agent_id
        record.l1_review.reviewer_role = l1.reviewer_role
        record.l1_review.assigned_at = datetime.now(UTC)
        record.touch()
        logger.info(
            "l1_assigned id=%s reviewer=%s role=%s",
            review_id,
            l1.agent_id,
            l1.reviewer_role,
        )
        return record

    def submit_l1(
        self,
        review_id: str,
        decision: ReviewDecision,
        checklist: L1ChecklistResults | None = None,
        issues: list[str] | None = None,
        comments: str = "",
    ) -> ReviewRecord:
        """Submit L1 review decision."""
        record = self.get(review_id)

        if record.state != SignoffState.L1_REVIEW:
            raise ReviewStateError(
                f"Cannot submit L1 review in state {record.state.value}"
            )

        record.l1_review.decision = decision
        record.l1_review.completed_at = datetime.now(UTC)
        record.l1_review.comments = comments
        if issues:
            record.l1_review.issues_found = issues
        if checklist:
            record.l1_review.checklist_results = checklist.model_dump()

        if decision == ReviewDecision.APPROVED:
            if record.risk_assessment.l2_required:
                self._transition(record, SignoffState.L1_APPROVED)
            else:
                self._transition(record, SignoffState.L1_APPROVED)
                self._transition(record, SignoffState.APPROVED)
        elif decision == ReviewDecision.CHANGES_REQUESTED:
            self._transition(record, SignoffState.L1_CHANGES_REQUESTED)
        elif decision == ReviewDecision.ESCALATED:
            # Escalation triggers L2 requirement
            record.risk_assessment.l2_required = True
            self._transition(record, SignoffState.L1_APPROVED)

        logger.info(
            "l1_submitted id=%s decision=%s", review_id, decision.value
        )
        return record

    def assign_l2(self, review_id: str) -> ReviewRecord:
        """Assign an L2 reviewer and move to L2_REVIEW."""
        record = self.get(review_id)
        self._transition(record, SignoffState.L2_REVIEW)

        _, l2 = self._assigner.assign(record.risk_assessment.triggers_identified)
        record.l2_review.reviewer_id = l2.agent_id
        record.l2_review.reviewer_role = l2.reviewer_role
        record.l2_review.assigned_at = datetime.now(UTC)
        record.touch()
        logger.info(
            "l2_assigned id=%s reviewer=%s role=%s",
            review_id,
            l2.agent_id,
            l2.reviewer_role,
        )
        return record

    def submit_l2(
        self,
        review_id: str,
        decision: ReviewDecision,
        checklist: L2ChecklistResults | None = None,
        issues: list[str] | None = None,
        comments: str = "",
    ) -> ReviewRecord:
        """Submit L2 review decision."""
        record = self.get(review_id)

        if record.state != SignoffState.L2_REVIEW:
            raise ReviewStateError(
                f"Cannot submit L2 review in state {record.state.value}"
            )

        record.l2_review.decision = decision
        record.l2_review.completed_at = datetime.now(UTC)
        record.l2_review.comments = comments
        if issues:
            record.l2_review.issues_found = issues
        if checklist:
            record.l2_review.checklist_results = checklist.model_dump()

        if decision == ReviewDecision.APPROVED:
            self._transition(record, SignoffState.L2_APPROVED)
            self._transition(record, SignoffState.APPROVED)
        elif decision == ReviewDecision.CHANGES_REQUESTED:
            self._transition(record, SignoffState.L2_CHANGES_REQUESTED)
        elif decision == ReviewDecision.ESCALATED:
            # Escalation keeps it in L2 but flags for human
            self._transition(record, SignoffState.L2_CHANGES_REQUESTED)

        logger.info(
            "l2_submitted id=%s decision=%s", review_id, decision.value
        )
        return record

    def approve(
        self,
        review_id: str,
        approver_id: str,
        conditions: list[str] | None = None,
    ) -> ReviewRecord:
        """Record final signoff on an APPROVED review."""
        record = self.get(review_id)

        if record.state != SignoffState.APPROVED:
            raise ReviewStateError(
                f"Cannot approve review in state {record.state.value}"
            )

        # Determine approval type
        if record.l2_review.decision is not None:
            if record.l2_review.reviewer_id == "HUMAN":
                approval_type = "l1_l2_human"
            else:
                approval_type = "l1_l2_agent"
        else:
            approval_type = "l1_only"

        record.final_signoff = FinalSignoff(
            approved_by=approver_id,
            approved_at=datetime.now(UTC),
            approval_type=approval_type,
            conditions=conditions or [],
        )
        record.touch()
        logger.info(
            "review_approved id=%s by=%s type=%s",
            review_id,
            approver_id,
            approval_type,
        )
        return record

    def merge(self, review_id: str) -> ReviewRecord:
        """Mark a review as MERGED (final state)."""
        record = self.get(review_id)
        self._transition(record, SignoffState.MERGED)
        logger.info("review_merged id=%s", review_id)
        return record
