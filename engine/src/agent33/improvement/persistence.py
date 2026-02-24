"""Persistence backends for learning-signal state."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from agent33.improvement.models import LearningSignal, ResearchIntake  # noqa: TC001


class LearningPersistenceState(BaseModel):
    """Durable state for learning signals and generated intakes."""

    signals: list[LearningSignal] = Field(default_factory=list)
    generated_intakes: list[ResearchIntake] = Field(default_factory=list)
    signal_intake_map: dict[str, str] = Field(default_factory=dict)


class LearningSignalStore(Protocol):
    """Persistence contract for learning-signal domain state."""

    def load(self) -> LearningPersistenceState:
        """Load persisted state."""

    def save(self, state: LearningPersistenceState) -> None:
        """Save state atomically."""


class InMemoryLearningSignalStore:
    """Non-durable in-memory store (test/default fallback)."""

    def __init__(self) -> None:
        self._state = LearningPersistenceState()

    def load(self) -> LearningPersistenceState:
        return self._state.model_copy(deep=True)

    def save(self, state: LearningPersistenceState) -> None:
        self._state = state.model_copy(deep=True)


class FileLearningSignalStore:
    """Deterministic JSON file-backed learning-signal store."""

    def __init__(self, path: str, *, on_corruption: str = "reset") -> None:
        self._path = Path(path)
        self._on_corruption = on_corruption.strip().lower()

    def load(self) -> LearningPersistenceState:
        if not self._path.exists():
            return LearningPersistenceState()
        try:
            payload = self._path.read_text(encoding="utf-8")
            if not payload.strip():
                return LearningPersistenceState()
            data = json.loads(payload)
            return LearningPersistenceState.model_validate(data)
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            return self._handle_corruption(exc)

    def save(self, state: LearningPersistenceState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        serialized = state.model_dump(mode="json")
        tmp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        tmp_path.write_text(
            json.dumps(serialized, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(self._path)

    def _handle_corruption(self, exc: Exception) -> LearningPersistenceState:
        if self._on_corruption == "raise":
            raise ValueError(
                f"Corrupted learning-signal persistence file: {self._path}"
            ) from exc
        self._quarantine_corrupted_file()
        return LearningPersistenceState()

    def _quarantine_corrupted_file(self) -> None:
        if not self._path.exists():
            return
        candidate = Path(f"{self._path}.corrupt")
        suffix = 1
        while candidate.exists():
            candidate = Path(f"{self._path}.corrupt.{suffix}")
            suffix += 1
        self._path.replace(candidate)


class SQLiteLearningSignalStore:
    """SQLite-backed durable store for learning-signal state."""

    def __init__(self, path: str, *, on_corruption: str = "reset") -> None:
        self._path = Path(path)
        self._on_corruption = on_corruption.strip().lower()

    def load(self) -> LearningPersistenceState:
        conn = self._connect()
        row: tuple[object] | None = None
        database_error: sqlite3.DatabaseError | None = None
        try:
            self._ensure_schema(conn)
            row = conn.execute(
                "SELECT payload FROM learning_signal_state WHERE state_key = 1"
            ).fetchone()
        except sqlite3.DatabaseError as exc:
            database_error = exc
        finally:
            conn.close()
        if database_error is not None:
            return self._handle_database_corruption(database_error)
        if row is None:
            return LearningPersistenceState()
        payload = row[0]
        if not isinstance(payload, str) or not payload.strip():
            return self._handle_corruption(payload, None)
        try:
            data = json.loads(payload)
            return LearningPersistenceState.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            return self._handle_corruption(payload, exc)

    def save(self, state: LearningPersistenceState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(state.model_dump(mode="json"), sort_keys=True)
        conn = self._connect()
        try:
            self._ensure_schema(conn)
            conn.execute(
                """
                INSERT INTO learning_signal_state(state_key, payload)
                VALUES (1, ?)
                ON CONFLICT(state_key) DO UPDATE SET payload = excluded.payload
                """,
                (payload,),
            )
            conn.commit()
        finally:
            conn.close()

    def _connect(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self._path)

    @staticmethod
    def _ensure_schema(conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learning_signal_state (
                state_key INTEGER PRIMARY KEY CHECK (state_key = 1),
                payload TEXT NOT NULL
            )
            """
        )

    def _handle_corruption(
        self, payload: object, exc: Exception | None
    ) -> LearningPersistenceState:
        message = (
            "Corrupted learning-signal persistence payload in SQLite: "
            f"{self._path}"
        )
        if self._on_corruption == "raise":
            raise ValueError(message) from exc
        self._write_corrupt_payload_sidecar(payload)
        conn = self._connect()
        database_error: sqlite3.DatabaseError | None = None
        try:
            try:
                self._ensure_schema(conn)
                conn.execute("DELETE FROM learning_signal_state WHERE state_key = 1")
                conn.commit()
            except sqlite3.DatabaseError as db_exc:
                database_error = db_exc
        finally:
            conn.close()
        if database_error is not None:
            return self._handle_database_corruption(database_error)
        return LearningPersistenceState()

    def _write_corrupt_payload_sidecar(self, payload: object) -> Path:
        sidecar_path = self._next_corrupt_payload_path()
        if isinstance(payload, str):
            sidecar_text = payload
        else:
            sidecar_text = json.dumps(
                {"payload": payload}, indent=2, sort_keys=True, default=str
            )
        sidecar_path.write_text(sidecar_text, encoding="utf-8")
        return sidecar_path

    def _next_corrupt_payload_path(self) -> Path:
        candidate = Path(f"{self._path}.corrupt.payload.json")
        suffix = 1
        while candidate.exists():
            candidate = Path(f"{self._path}.corrupt.payload.{suffix}.json")
            suffix += 1
        return candidate

    def _handle_database_corruption(self, exc: Exception) -> LearningPersistenceState:
        message = f"Corrupted learning-signal SQLite database: {self._path}"
        if self._on_corruption == "raise":
            raise ValueError(message) from exc
        self._quarantine_corrupted_database_file()
        return LearningPersistenceState()

    def _quarantine_corrupted_database_file(self) -> None:
        if not self._path.exists():
            return
        candidate = Path(f"{self._path}.corrupt")
        suffix = 1
        while candidate.exists():
            candidate = Path(f"{self._path}.corrupt.{suffix}")
            suffix += 1
        self._path.replace(candidate)


def _state_has_data(state: LearningPersistenceState) -> bool:
    return bool(state.signals or state.generated_intakes or state.signal_intake_map)


def should_migrate_file_learning_state_to_db(
    file_path: str,
    db_path: str,
    *,
    on_file_corruption: str = "reset",
    on_db_corruption: str = "reset",
) -> bool:
    """Return true when migration should run without overwriting existing DB state."""
    source_store = FileLearningSignalStore(
        file_path,
        on_corruption=on_file_corruption,
    )
    source_state = source_store.load()
    if not _state_has_data(source_state):
        return False

    destination_store = SQLiteLearningSignalStore(
        db_path,
        on_corruption=on_db_corruption,
    )
    destination_state = destination_store.load()
    return not _state_has_data(destination_state)


def migrate_learning_state(
    source_store: LearningSignalStore,
    destination_store: LearningSignalStore,
) -> LearningPersistenceState:
    """Copy persisted state between backends."""
    state = source_store.load()
    destination_store.save(state)
    return state


def migrate_file_learning_state_to_db(
    file_path: str,
    db_path: str,
    *,
    on_file_corruption: str = "reset",
    backup_path: str | None = None,
) -> LearningPersistenceState:
    """Migrate JSON file persistence state into SQLite persistence state."""
    source = FileLearningSignalStore(file_path, on_corruption=on_file_corruption)
    if backup_path is not None:
        backup_learning_state(source, backup_path)
    destination = SQLiteLearningSignalStore(db_path)
    return migrate_learning_state(source, destination)


def backup_learning_state(store: LearningSignalStore, backup_path: str) -> Path:
    """Persist a portable JSON backup of current learning state."""
    backup_file = Path(backup_path)
    backup_file.parent.mkdir(parents=True, exist_ok=True)
    payload = store.load().model_dump(mode="json")
    backup_file.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return backup_file


def restore_learning_state(
    store: LearningSignalStore, backup_path: str
) -> LearningPersistenceState:
    """Restore learning state from a portable JSON backup."""
    backup_file = Path(backup_path)
    payload = backup_file.read_text(encoding="utf-8")
    if not payload.strip():
        state = LearningPersistenceState()
    else:
        state = LearningPersistenceState.model_validate(json.loads(payload))
    store.save(state)
    return state
