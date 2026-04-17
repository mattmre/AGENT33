from __future__ import annotations

from datetime import UTC, datetime, timedelta

from agent33.evaluation.ppack_ab_persistence import PPackABPersistence
from agent33.evaluation.ppack_ab_service import PPackABService
from agent33.outcomes.models import OutcomeEventCreate, OutcomeMetricType
from agent33.outcomes.service import OutcomesService


def test_assign_variant_is_deterministic() -> None:
    service = PPackABService(
        outcomes_service=OutcomesService(),
        persistence=PPackABPersistence(":memory:"),
    )
    first = service.assign_variant(tenant_id="tenant-a", session_id="session-123")
    second = service.assign_variant(tenant_id="tenant-a", session_id="session-123")
    assert first.variant == second.variant
    assert first.assignment_hash == second.assignment_hash


def test_generate_report_detects_significant_regression() -> None:
    outcomes = OutcomesService()
    service = PPackABService(
        outcomes_service=outcomes,
        persistence=PPackABPersistence(":memory:"),
        minimum_sample_size=4,
        regression_threshold=-0.05,
    )
    base = datetime.now(UTC) - timedelta(days=1)
    assignments = []
    candidate = 0
    while len([item for item in assignments if item.variant.value == "control"]) < 4:
        assignment = service.assign_variant(
            tenant_id="tenant-a",
            session_id=f"session-candidate-{candidate}",
        )
        if assignment.variant.value == "control":
            assignments.append(assignment)
        candidate += 1
    while len([item for item in assignments if item.variant.value == "treatment"]) < 4:
        assignment = service.assign_variant(
            tenant_id="tenant-a",
            session_id=f"session-candidate-{candidate}",
        )
        if assignment.variant.value == "treatment":
            assignments.append(assignment)
        candidate += 1
    for assignment in assignments:
        value = 1.0 if assignment.variant.value == "control" else 0.0
        for offset in range(4):
            outcomes.record_event(
                tenant_id="tenant-a",
                event=OutcomeEventCreate(
                    domain="support",
                    event_type="invoke",
                    metric_type=OutcomeMetricType.SUCCESS_RATE,
                    value=value,
                    occurred_at=base + timedelta(minutes=offset),
                    metadata={
                        "session_id": assignment.session_id,
                        "ppack_variant": assignment.variant.value,
                    },
                ),
            )
    report = service.generate_report(
        tenant_id="tenant-a",
        domain="support",
        since=base - timedelta(minutes=1),
        until=base + timedelta(hours=1),
        metric_types=[OutcomeMetricType.SUCCESS_RATE],
    )
    assert report.total_assignments >= 8
    assert report.total_events_considered == 32
    assert report.overall_regression is True
    comparison = report.comparisons[0]
    assert comparison.metric_type == OutcomeMetricType.SUCCESS_RATE
    assert comparison.regression_detected is True
    assert comparison.statistically_significant is True
    assert comparison.directional_delta_pct <= -0.05
