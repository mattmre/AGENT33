"""Circuit-breaker primitives for external connector boundaries."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


class CircuitState(StrEnum):
    """Current state of a circuit breaker."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised when a call is blocked by an open circuit breaker."""


@dataclass(slots=True)
class CircuitBreaker:
    """Simple consecutive-failure circuit breaker."""

    failure_threshold: int = 3
    recovery_timeout_seconds: float = 30.0
    half_open_success_threshold: int = 1
    clock: Callable[[], float] = time.monotonic
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    opened_at: float | None = None
    half_open_successes: int = 0
    total_trips: int = 0
    last_trip_at: float | None = None
    on_state_change: Callable[[CircuitState, CircuitState], None] | None = field(
        default=None, repr=False
    )

    def _transition(self, new_state: CircuitState) -> None:
        """Apply a state transition and fire the callback if set."""
        old_state = self.state
        if old_state == new_state:
            return
        self.state = new_state
        if self.on_state_change is not None:
            self.on_state_change(old_state, new_state)

    def before_call(self) -> None:
        """Check whether the next call is allowed."""
        if self.state != CircuitState.OPEN:
            return
        if self.opened_at is None:
            raise CircuitOpenError("Circuit is open")
        elapsed = self.clock() - self.opened_at
        if elapsed < self.recovery_timeout_seconds:
            raise CircuitOpenError("Circuit is open")
        self._transition(CircuitState.HALF_OPEN)
        self.half_open_successes = 0

    def record_success(self) -> None:
        """Record a successful downstream call."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_success_threshold:
                self._transition(CircuitState.CLOSED)
                self.consecutive_failures = 0
                self.opened_at = None
                self.half_open_successes = 0
            return

        self._transition(CircuitState.CLOSED)
        self.consecutive_failures = 0

    def record_failure(self) -> None:
        """Record a failed downstream call."""
        if self.state == CircuitState.HALF_OPEN:
            self._open()
            return

        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self._open()

    def _open(self) -> None:
        self._transition(CircuitState.OPEN)
        self.opened_at = self.clock()
        self.total_trips += 1
        self.last_trip_at = self.opened_at
        self.consecutive_failures = 0
        self.half_open_successes = 0

    def snapshot(self) -> dict[str, Any]:
        """Return a serializable dict of the breaker's current state."""
        return {
            "state": self.state.value,
            "consecutive_failures": self.consecutive_failures,
            "total_trips": self.total_trips,
            "last_trip_at": self.last_trip_at,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout_seconds": self.recovery_timeout_seconds,
            "half_open_success_threshold": self.half_open_success_threshold,
        }
