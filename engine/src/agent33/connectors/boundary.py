"""Shared connector-boundary construction and error mapping."""

from __future__ import annotations

import httpx

from agent33.config import settings
from agent33.connectors.circuit_breaker import CircuitBreaker, CircuitOpenError
from agent33.connectors.executor import ConnectorExecutor
from agent33.connectors.governance import BlocklistConnectorPolicy
from agent33.connectors.middleware import (
    CircuitBreakerMiddleware,
    ConnectorMiddleware,
    GovernanceMiddleware,
    MetricsMiddleware,
    RetryMiddleware,
    TimeoutMiddleware,
)


def _parse_csv(value: str) -> frozenset[str]:
    return frozenset(item.strip() for item in value.split(",") if item.strip())


_POLICY_PACKS: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "default": (frozenset(), frozenset()),
    "strict-web": (
        frozenset({"tool:web_fetch", "workflow:http_request"}),
        frozenset(),
    ),
    "mcp-readonly": (
        frozenset(),
        frozenset({"tools/call"}),
    ),
}


def get_policy_pack(
    pack_name: str | None,
) -> tuple[frozenset[str], frozenset[str]]:
    """Return blocked connector/operation sets for the configured policy pack."""
    if not pack_name:
        return _POLICY_PACKS["default"]
    return _POLICY_PACKS.get(pack_name, _POLICY_PACKS["default"])


def build_connector_boundary_executor(
    *,
    default_timeout_seconds: float | None = None,
    retry_attempts: int = 1,
    policy_pack: str | None = None,
) -> ConnectorExecutor | None:
    """Build the default connector boundary middleware chain."""
    if not settings.connector_boundary_enabled:
        return None

    middlewares: list[ConnectorMiddleware] = []
    pack_blocked_connectors, pack_blocked_operations = get_policy_pack(
        policy_pack or getattr(settings, "connector_policy_pack", "default")
    )
    policy = BlocklistConnectorPolicy(
        blocked_connectors=pack_blocked_connectors.union(
            _parse_csv(settings.connector_governance_blocked_connectors)
        ),
        blocked_operations=pack_blocked_operations.union(
            _parse_csv(settings.connector_governance_blocked_operations)
        ),
    )
    middlewares.append(GovernanceMiddleware(policy))
    if default_timeout_seconds is not None:
        middlewares.append(TimeoutMiddleware(default_timeout_seconds))
    if retry_attempts > 1:
        middlewares.append(RetryMiddleware(max_attempts=retry_attempts))
    if settings.connector_circuit_breaker_enabled:
        middlewares.append(
            CircuitBreakerMiddleware(
                CircuitBreaker(
                    failure_threshold=settings.connector_circuit_failure_threshold,
                    recovery_timeout_seconds=settings.connector_circuit_recovery_seconds,
                    half_open_success_threshold=settings.connector_circuit_half_open_successes,
                )
            )
        )
    middlewares.append(MetricsMiddleware())
    return ConnectorExecutor(middlewares=middlewares)


def map_connector_exception(exc: Exception, connector: str, operation: str) -> RuntimeError:
    """Normalize connector errors for consistent caller-facing failures."""
    if isinstance(exc, PermissionError):
        return RuntimeError(f"Connector governance blocked {connector}/{operation}: {exc}")
    if isinstance(exc, (TimeoutError, httpx.TimeoutException)):
        return RuntimeError(f"Connector timeout for {connector}/{operation}: {exc}")
    if isinstance(exc, CircuitOpenError):
        return RuntimeError(f"Connector circuit open for {connector}/{operation}: {exc}")
    if isinstance(exc, httpx.HTTPError):
        return RuntimeError(f"Connector HTTP error for {connector}/{operation}: {exc}")
    return RuntimeError(f"Connector failure for {connector}/{operation}: {exc}")
