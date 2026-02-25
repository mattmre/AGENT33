"""Persistence backends for learning-signal state."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field

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

    def __init__(self, path: str) -> None:
        self._path = Path(path)

    def load(self) -> LearningPersistenceState:
        if not self._path.exists():
            return LearningPersistenceState()
        payload = self._path.read_text(encoding="utf-8")
        if not payload.strip():
            return LearningPersistenceState()
        data = json.loads(payload)
        return LearningPersistenceState.model_validate(data)

    def save(self, state: LearningPersistenceState) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        serialized = state.model_dump(mode="json")
        tmp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        tmp_path.write_text(
            json.dumps(serialized, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        tmp_path.replace(self._path)
