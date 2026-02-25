"""Phase 31 — Continuous learning signals tests."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from agent33.config import settings
from agent33.improvement.models import (
    LearningSignal,
    LearningSignalSeverity,
    LearningSignalType,
)
from agent33.improvement.persistence import (
    FileLearningSignalStore,
    SQLiteLearningSignalStore,
    backup_learning_state,
    migrate_file_learning_state_to_db,
    restore_learning_state,
)
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
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_db_path", "unused.sqlite3"
    )
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_migrate_on_start", False
    )
    monkeypatch.setattr(
        settings,
        "improvement_learning_persistence_migration_backup_on_start",
        False,
    )
    monkeypatch.setattr(
        settings,
        "improvement_learning_persistence_migration_backup_path",
        "var/improvement_learning_signals.backup.json",
    )
    monkeypatch.setattr(
        settings, "improvement_learning_file_corruption_behavior", "reset"
    )
    monkeypatch.setattr(
        settings, "improvement_learning_db_corruption_behavior", "reset"
    )
    _reset_service()
    monkeypatch.setattr(settings, "improvement_learning_enabled", False)
    monkeypatch.setattr(settings, "improvement_learning_summary_default_limit", 50)
    monkeypatch.setattr(settings, "improvement_learning_auto_intake_enabled", False)
    monkeypatch.setattr(
        settings, "improvement_learning_auto_intake_min_severity", "high"
    )
    monkeypatch.setattr(settings, "improvement_learning_auto_intake_max_items", 3)
    yield
    _reset_service()


def test_settings_reject_invalid_learning_corruption_behavior() -> None:
    from agent33.config import Settings

    with pytest.raises(ValidationError, match="corruption behavior must be one of"):
        Settings(improvement_learning_file_corruption_behavior="invalid")
    with pytest.raises(ValidationError, match="corruption behavior must be one of"):
        Settings(improvement_learning_db_corruption_behavior="invalid")


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


def test_file_to_db_migration_path(tmp_path: Path):
    file_path = tmp_path / "learning_state.json"
    db_path = tmp_path / "learning_state.sqlite3"

    seed = ImprovementService(learning_store=FileLearningSignalStore(str(file_path)))
    seed.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="Persisted in file backend",
            tenant_id="tenant-a",
        )
    )
    seed.generate_intakes_from_learning_signals(max_items=1)

    migrated = migrate_file_learning_state_to_db(str(file_path), str(db_path))
    assert len(migrated.signals) == 1
    assert len(migrated.generated_intakes) == 1

    db_service = ImprovementService(
        learning_store=SQLiteLearningSignalStore(str(db_path))
    )
    loaded_signals = db_service.list_learning_signals(tenant_id="tenant-a", limit=10)
    assert len(loaded_signals) == 1
    assert loaded_signals[0].summary == "Persisted in file backend"
    assert len(db_service.list_intakes(tenant_id="tenant-a")) == 1


def test_file_to_db_migration_path_creates_backup_when_requested(tmp_path: Path):
    file_path = tmp_path / "learning_state.json"
    db_path = tmp_path / "learning_state.sqlite3"
    backup_path = tmp_path / "learning_state.backup.json"

    seed = ImprovementService(learning_store=FileLearningSignalStore(str(file_path)))
    seed.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="Persisted in file backend",
            tenant_id="tenant-a",
        )
    )

    migrated = migrate_file_learning_state_to_db(
        str(file_path), str(db_path), backup_path=str(backup_path)
    )

    assert len(migrated.signals) == 1
    assert backup_path.exists()
    backup_payload = json.loads(backup_path.read_text(encoding="utf-8"))
    assert len(backup_payload["signals"]) == 1


def test_backup_and_restore_persisted_learning_state(tmp_path: Path):
    source_path = tmp_path / "source_learning.json"
    backup_path = tmp_path / "backup_learning.json"
    target_path = tmp_path / "target_learning.sqlite3"

    source_store = FileLearningSignalStore(str(source_path))
    source_service = ImprovementService(learning_store=source_store)
    source_service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.INCIDENT,
            severity=LearningSignalSeverity.CRITICAL,
            summary="Needs backup",
            tenant_id="tenant-backup",
        )
    )

    backup_file = backup_learning_state(source_store, str(backup_path))
    assert backup_file.exists()

    target_store = SQLiteLearningSignalStore(str(target_path))
    restored = restore_learning_state(target_store, str(backup_path))
    assert len(restored.signals) == 1

    restored_service = ImprovementService(learning_store=target_store)
    restored_signals = restored_service.list_learning_signals(
        tenant_id="tenant-backup", limit=10
    )
    assert len(restored_signals) == 1
    assert restored_signals[0].summary == "Needs backup"


def test_file_store_corruption_recovery_is_deterministic(tmp_path: Path):
    corrupt_path = tmp_path / "corrupt_learning.json"
    corrupt_path.write_text("{not-json", encoding="utf-8")

    store = FileLearningSignalStore(str(corrupt_path), on_corruption="reset")
    state = store.load()

    assert state.signals == []
    assert not corrupt_path.exists()
    assert (tmp_path / "corrupt_learning.json.corrupt").exists()


def test_sqlite_store_corruption_reset_writes_sidecar_and_clears_row(tmp_path: Path):
    db_path = tmp_path / "corrupt_learning.sqlite3"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_signal_state (
                state_key INTEGER PRIMARY KEY CHECK (state_key = 1),
                payload TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO learning_signal_state(state_key, payload) VALUES (1, ?)",
            ("{not-json",),
        )
        conn.commit()

    store = SQLiteLearningSignalStore(str(db_path), on_corruption="reset")
    loaded = store.load()

    assert loaded.signals == []
    sidecars = sorted(
        tmp_path.glob("corrupt_learning.sqlite3.corrupt.payload*.json")
    )
    assert len(sidecars) == 1
    assert sidecars[0].read_text(encoding="utf-8") == "{not-json"
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT payload FROM learning_signal_state WHERE state_key = 1"
        ).fetchone()
    assert row is None


def test_sqlite_store_corruption_raise_throws_value_error(tmp_path: Path):
    db_path = tmp_path / "corrupt_learning.sqlite3"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_signal_state (
                state_key INTEGER PRIMARY KEY CHECK (state_key = 1),
                payload TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO learning_signal_state(state_key, payload) VALUES (1, ?)",
            ("{not-json",),
        )
        conn.commit()

    store = SQLiteLearningSignalStore(str(db_path), on_corruption="raise")
    with pytest.raises(
        ValueError,
        match=(
            "^Corrupted learning-signal persistence payload in SQLite: "
            f"{re.escape(str(db_path))}$"
        ),
    ):
        store.load()


def test_sqlite_database_corruption_reset_quarantines_db_file(tmp_path: Path):
    db_path = tmp_path / "corrupt_db.sqlite3"
    db_path.write_bytes(b"not-a-sqlite-database")

    store = SQLiteLearningSignalStore(str(db_path), on_corruption="reset")
    loaded = store.load()

    assert loaded.signals == []
    assert not db_path.exists()
    sidecars = sorted(tmp_path.glob("corrupt_db.sqlite3.corrupt*"))
    assert len(sidecars) == 1


def test_sqlite_database_corruption_raise_throws_value_error(tmp_path: Path):
    db_path = tmp_path / "corrupt_db.sqlite3"
    db_path.write_bytes(b"not-a-sqlite-database")

    store = SQLiteLearningSignalStore(str(db_path), on_corruption="raise")
    with pytest.raises(
        ValueError,
        match=(
            "^Corrupted learning-signal SQLite database: "
            f"{re.escape(str(db_path))}$"
        ),
    ):
        store.load()


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


def test_routes_support_sqlite_backend_with_file_migration(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from agent33.api.routes.improvements import _reset_service

    file_path = tmp_path / "learning_state.json"
    db_path = tmp_path / "learning_state.sqlite3"

    file_seed_service = ImprovementService(
        learning_store=FileLearningSignalStore(str(file_path))
    )
    file_seed_service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="Migrate me",
            tenant_id="tenant-db",
        )
    )

    monkeypatch.setattr(settings, "improvement_learning_enabled", True)
    monkeypatch.setattr(settings, "improvement_learning_persistence_backend", "db")
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_path", str(file_path)
    )
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_db_path", str(db_path)
    )
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_migrate_on_start", True
    )
    _reset_service()

    listed = client.get(
        "/v1/improvements/learning/signals",
        params={"tenant_id": "tenant-db", "limit": 10},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_routes_sqlite_startup_migration_creates_backup_when_enabled(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from agent33.api.routes.improvements import _reset_service

    file_path = tmp_path / "learning_state.json"
    db_path = tmp_path / "learning_state.sqlite3"
    backup_path = tmp_path / "learning_state.backup.json"

    file_seed_service = ImprovementService(
        learning_store=FileLearningSignalStore(str(file_path))
    )
    file_seed_service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="Migrate and backup me",
            tenant_id="tenant-db",
        )
    )

    monkeypatch.setattr(settings, "improvement_learning_enabled", True)
    monkeypatch.setattr(settings, "improvement_learning_persistence_backend", "db")
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_path", str(file_path)
    )
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_db_path", str(db_path)
    )
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_migrate_on_start", True
    )
    monkeypatch.setattr(
        settings,
        "improvement_learning_persistence_migration_backup_on_start",
        True,
    )
    monkeypatch.setattr(
        settings,
        "improvement_learning_persistence_migration_backup_path",
        str(backup_path),
    )
    _reset_service()

    listed = client.get(
        "/v1/improvements/learning/signals",
        params={"tenant_id": "tenant-db", "limit": 10},
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert backup_path.exists()


def test_routes_sqlite_startup_migration_does_not_overwrite_existing_db(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    from agent33.api.routes.improvements import _reset_service

    file_path = tmp_path / "learning_state.json"
    db_path = tmp_path / "learning_state.sqlite3"

    db_seed_service = ImprovementService(
        learning_store=SQLiteLearningSignalStore(str(db_path))
    )
    db_seed_service.record_learning_signal(
        LearningSignal(
            signal_type=LearningSignalType.BUG,
            severity=LearningSignalSeverity.HIGH,
            summary="Keep DB state",
            tenant_id="tenant-db",
        )
    )

    monkeypatch.setattr(settings, "improvement_learning_enabled", True)
    monkeypatch.setattr(settings, "improvement_learning_persistence_backend", "db")
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_path", str(file_path)
    )
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_db_path", str(db_path)
    )
    monkeypatch.setattr(
        settings, "improvement_learning_persistence_migrate_on_start", True
    )
    _reset_service()

    listed = client.get(
        "/v1/improvements/learning/signals",
        params={"tenant_id": "tenant-db", "limit": 10},
    )
    assert listed.status_code == 200
    payload = listed.json()
    assert len(payload) == 1
    assert payload[0]["summary"] == "Keep DB state"
