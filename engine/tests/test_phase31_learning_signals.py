"""Phase 31 — Continuous learning signals tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from agent33.config import settings
from agent33.improvement.models import (
    LearningSignal,
    LearningSignalSeverity,
    LearningSignalType,
)
from agent33.improvement.persistence import FileLearningSignalStore
from agent33.improvement.service import ImprovementService

if TYPE_CHECKING:
    from pathlib import Path

    from starlette.testclient import TestClient


@pytest.fixture()
def service() -> ImprovementService:
    return ImprovementService()


@pytest.fixture(autouse=True)
def _reset_learning_route_state(monkeypatch: pytest.MonkeyPatch):
    from agent33.api.routes.improvements import _reset_service

    monkeypatch.setattr(
        settings, "improvement_learning_persistence_backend", "memory"
    )
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_path", "unused.json"
    )
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


def test_learning_signal_quality_enrichment_applied(service: ImprovementService):
    signal = service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="CI failure when integration tests run with production-like fixtures",
            details="Nightly build fails after db migration and retries are exhausted.",
            source="ci",
            context={"pipeline": "nightly", "job": "integration"},
        )
    )
    assert signal.quality_score > 0.7
    assert signal.quality_label == "high"
    assert signal.enrichment["has_source"] == "true"
    assert signal.quality_reasons == ["well_formed_signal"]


def test_file_store_persists_signals_and_generated_intakes(tmp_path: Path):
    store_path = tmp_path / "learning_state.json"
    first = ImprovementService(
        learning_store=FileLearningSignalStore(str(store_path))
    )
    first.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.INCIDENT,
            severity=LearningSignalSeverity.CRITICAL,
            summary="Tenant outage",
            tenant_id="tenant-a",
        )
    )
    created = first.generate_intakes_from_learning_signals(max_items=1)
    assert len(created) == 1

    second = ImprovementService(
        learning_store=FileLearningSignalStore(str(store_path))
    )
    signals = second.list_learning_signals(tenant_id="tenant-a", limit=10)
    assert len(signals) == 1
    assert signals[0].related_intake_id is not None
    intakes = second.list_intakes(tenant_id="tenant-a")
    assert len(intakes) == 1
    assert intakes[0].generated_from_signal_id == signals[0].signal_id


def test_summary_supports_tenant_and_window_trends(service: ImprovementService):
    now = datetime.now(UTC)
    service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            tenant_id="tenant-a",
            summary="fresh-a",
            recorded_at=now - timedelta(days=1),
        )
    )
    service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.FEEDBACK,
            severity=LearningSignalSeverity.MEDIUM,
            tenant_id="tenant-a",
            summary="older-a",
            recorded_at=now - timedelta(days=8),
        )
    )
    service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            tenant_id="tenant-b",
            summary="fresh-b",
            recorded_at=now - timedelta(days=1),
        )
    )

    summary = service.summarize_learning_signals(
        limit=10, tenant_id="tenant-a", window_days=7
    )
    assert summary.total_signals == 1
    assert summary.counts_by_tenant == {"tenant-a": 1}
    assert summary.previous_window_total == 1
    assert summary.trend_delta == 0
    assert summary.trend_direction == "stable"


def test_auto_intake_priority_uses_quality_score(service: ImprovementService):
    service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="Short",
        )
    )
    service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="Detailed recurring bug in release pipeline after dependency bump",
            details="Observed in two regions with canary and stable lanes.",
            source="ci",
            context={"region": "us-east", "release": "2026.02"},
        )
    )
    created = service.generate_intakes_from_learning_signals(
        min_severity=LearningSignalSeverity.HIGH,
        max_items=2,
    )
    assert len(created) == 2
    scores = [intake.relevance.priority_score for intake in created]
    assert scores[0] >= scores[1]
    assert created[0].automated_quality_score is not None


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
        params={
            "signal_type": "bug",
            "severity": "high",
            "tenant_id": "default",
            "limit": 10,
        },
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
    monkeypatch.setattr(
        settings, "improvement_learning_auto_intake_min_severity", "high"
    )
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


def test_summary_is_tenant_scoped_in_route(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(settings, "improvement_learning_enabled", True)
    client.post(
        "/v1/improvements/learning/signals",
        json={
            "signal_type": "incident",
            "severity": "high",
            "summary": "tenant one signal",
            "tenant_id": "tenant-1",
        },
    )
    client.post(
        "/v1/improvements/learning/signals",
        json={
            "signal_type": "bug",
            "severity": "high",
            "summary": "tenant two signal",
            "tenant_id": "tenant-2",
        },
    )

    response = client.get(
        "/v1/improvements/learning/summary",
        params={"tenant_id": "tenant-1", "window_days": 30},
    )
    assert response.status_code == 200
    payload = response.json()["summary"]
    assert payload["tenant_id"] == "tenant-1"
    assert payload["total_signals"] == 1
    assert payload["counts_by_tenant"] == {"tenant-1": 1}
