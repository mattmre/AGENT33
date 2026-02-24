"""Middleware contracts and built-in connector boundary middleware."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any, Protocol

from agent33.connectors.models import ConnectorRequest

if TYPE_CHECKING:
    from agent33.connectors.circuit_breaker import CircuitBreaker
    from agent33.connectors.governance import ConnectorGovernancePolicy

ConnectorHandler = Callable[[ConnectorRequest], Awaitable[Any]]


class ConnectorMiddleware(Protocol):
    """Callable connector middleware contract."""

    async def __call__(
        self,
        request: ConnectorRequest,
        call_next: ConnectorHandler,
    ) -> Any:
        ...


class GovernanceMiddleware:
    """Enforce a governance policy before executing a connector call."""

    def __init__(self, policy: ConnectorGovernancePolicy) -> None:
        self._policy = policy

    async def __call__(
        self,
        request: ConnectorRequest,
        call_next: ConnectorHandler,
    ) -> Any:
        decision = self._policy.evaluate(request)
        if not decision.allowed:
            reason = decision.reason or "connector call blocked by governance policy"
            raise PermissionError(reason)
        return await call_next(request)


class CircuitBreakerMiddleware:
    """Protect connector calls with a circuit breaker."""

    def __init__(self, breaker: CircuitBreaker) -> None:
        self._breaker = breaker

    async def __call__(
        self,
        request: ConnectorRequest,
        call_next: ConnectorHandler,
    ) -> Any:
        self._breaker.before_call()
        try:
            result = await call_next(request)
        except Exception:
            self._breaker.record_failure()
            raise
        self._breaker.record_success()
        return result
