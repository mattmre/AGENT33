"""Phase 31 — Continuous learning signals tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from agent33.config import settings
from agent33.improvement.models import (
    LearningSignal,
    LearningSignalSeverity,
    LearningSignalType,
)
from agent33.improvement.service import ImprovementService

if TYPE_CHECKING:
    from starlette.testclient import TestClient


@pytest.fixture()
def service() -> ImprovementService:
    return ImprovementService()


@pytest.fixture(autouse=True)
def _reset_learning_route_state(monkeypatch: pytest.MonkeyPatch):
    from agent33.api.routes.improvements import _reset_service

    _reset_service()
    monkeypatch.setattr(settings, "improvement_learning_enabled", False)
    monkeypatch.setattr(settings, "improvement_learning_summary_default_limit", 50)
    monkeypatch.setattr(settings, "improvement_learning_auto_intake_enabled", False)
    monkeypatch.setattr(settings, "improvement_learning_auto_intake_min_severity", "high")
    monkeypatch.setattr(settings, "improvement_learning_auto_intake_max_items", 3)
    yield
    _reset_service()


def test_service_roundtrip_and_summary_counts(service: ImprovementService):
    service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="Build flake in CI",
        )
    )
    service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.FEEDBACK,
            severity=LearningSignalSeverity.LOW,
            summary="User requests better docs",
        )
    )
    service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="Regression after deploy",
        )
    )

    only_bugs = service.list_learning_signals(
        signal_type=LearningSignalType.BUG, limit=10
    )
    assert len(only_bugs) == 2

    summary = service.summarize_learning_signals(limit=10)
    assert summary.total_signals == 3
    assert summary.counts_by_type["bug"] == 2
    assert summary.counts_by_type["feedback"] == 1
    assert summary.counts_by_severity["high"] == 2
    assert summary.counts_by_severity["low"] == 1


def test_idempotent_intake_generation(service: ImprovementService):
    signal = service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.INCIDENT,
            severity=LearningSignalSeverity.HIGH,
            summary="Production timeout spike",
        )
    )

    first = service.generate_intakes_from_learning_signals(
        min_severity=LearningSignalSeverity.HIGH, max_items=3
    )
    second = service.generate_intakes_from_learning_signals(
        min_severity=LearningSignalSeverity.HIGH, max_items=3
    )

    assert len(first) == 1
    assert len(second) == 0
    assert signal.intake_generated is True
    assert signal.related_intake_id == first[0].intake_id


def test_routes_404_when_feature_disabled(client: TestClient):
    assert client.post(
        "/v1/improvements/learning/signals",
        json={"signal_type": "bug", "severity": "high", "summary": "x"},
    ).status_code == 404
    assert client.get("/v1/improvements/learning/signals").status_code == 404
    assert client.get("/v1/improvements/learning/summary").status_code == 404


def test_routes_record_and_list_when_enabled(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(settings, "improvement_learning_enabled", True)

    created = client.post(
        "/v1/improvements/learning/signals",
        json={
            "signal_type": "bug",
            "severity": "high",
            "summary": "New flaky test discovered",
            "details": "Observed in nightly run",
            "source": "ci",
        },
    )
    assert created.status_code == 200
    body = created.json()
    assert body["signal_id"].startswith("LS-")
    assert body["signal_type"] == "bug"
    assert body["severity"] == "high"

    listed = client.get(
        "/v1/improvements/learning/signals",
        params={"signal_type": "bug", "severity": "high", "limit": 10},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_summary_generate_intakes_respects_auto_intake_flag(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(settings, "improvement_learning_enabled", True)

    client.post(
        "/v1/improvements/learning/signals",
        json={
            "signal_type": "incident",
            "severity": "high",
            "summary": "Retry storm after deploy",
        },
    )

    monkeypatch.setattr(settings, "improvement_learning_auto_intake_enabled", False)
    no_intakes = client.get(
        "/v1/improvements/learning/summary",
        params={"generate_intakes": "true"},
    )
    assert no_intakes.status_code == 200
    assert no_intakes.json()["generated_intakes"] == []

    monkeypatch.setattr(settings, "improvement_learning_auto_intake_enabled", True)
    monkeypatch.setattr(settings, "improvement_learning_auto_intake_min_severity", "high")
    monkeypatch.setattr(settings, "improvement_learning_auto_intake_max_items", 3)

    with_intakes = client.get(
        "/v1/improvements/learning/summary",
        params={"generate_intakes": "true"},
    )
    assert with_intakes.status_code == 200
    assert len(with_intakes.json()["generated_intakes"]) == 1

    second = client.get(
        "/v1/improvements/learning/summary",
        params={"generate_intakes": "true"},
    )
    assert second.status_code == 200
    assert second.json()["generated_intakes"] == []
