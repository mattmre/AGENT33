"""Circuit-breaker primitives for external connector boundaries."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


class CircuitState(str, Enum):
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

    def before_call(self) -> None:
        """Check whether the next call is allowed."""
        if self.state != CircuitState.OPEN:
            return
        if self.opened_at is None:
            raise CircuitOpenError("Circuit is open")
        elapsed = self.clock() - self.opened_at
        if elapsed < self.recovery_timeout_seconds:
            raise CircuitOpenError("Circuit is open")
        self.state = CircuitState.HALF_OPEN
        self.half_open_successes = 0

    def record_success(self) -> None:
        """Record a successful downstream call."""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_success_threshold:
                self.state = CircuitState.CLOSED
                self.consecutive_failures = 0
                self.opened_at = None
                self.half_open_successes = 0
            return

        self.state = CircuitState.CLOSED
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
        self.state = CircuitState.OPEN
        self.opened_at = self.clock()
        self.consecutive_failures = 0
        self.half_open_successes = 0
