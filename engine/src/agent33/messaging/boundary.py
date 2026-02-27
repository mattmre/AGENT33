"""Connector boundary helpers for messaging adapters."""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import TYPE_CHECKING, Any, TypeVar

from agent33.config import settings
from agent33.connectors.boundary import (
    build_connector_boundary_executor,
    map_connector_exception,
)
from agent33.connectors.models import ConnectorRequest

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from agent33.connectors.executor import ConnectorExecutor

_T = TypeVar("_T")
_DEFAULT_TIMEOUT_SECONDS = 30.0
_RETRY_ATTEMPTS = 1


def _boundary_executor_cache_key() -> tuple[Any, ...]:
    return (
        settings.connector_boundary_enabled,
        settings.connector_policy_pack,
        settings.connector_governance_blocked_connectors,
        settings.connector_governance_blocked_operations,
        settings.connector_circuit_breaker_enabled,
        settings.connector_circuit_failure_threshold,
        settings.connector_circuit_recovery_seconds,
        settings.connector_circuit_half_open_successes,
    )


@lru_cache(maxsize=8)
def _get_boundary_executor(cache_key: tuple[Any, ...]) -> ConnectorExecutor | None:
    if not cache_key[0]:
        return None
    return build_connector_boundary_executor(
        default_timeout_seconds=_DEFAULT_TIMEOUT_SECONDS,
        retry_attempts=_RETRY_ATTEMPTS,
        policy_pack=cache_key[1],
    )


async def execute_messaging_boundary_call(
    *,
    connector: str,
    operation: str,
    payload: dict[str, Any],
    metadata: dict[str, Any],
    call: Callable[[ConnectorRequest], Awaitable[_T]],
    timeout_seconds: float = 30.0,
) -> _T:
    """Execute a messaging connector call through the boundary middleware."""
    request_metadata = dict(metadata)
    request_metadata["timeout_seconds"] = timeout_seconds
    request = ConnectorRequest(
        connector=connector,
        operation=operation,
        payload=dict(payload),
        metadata=request_metadata,
    )
    boundary_executor = _get_boundary_executor(_boundary_executor_cache_key())

    if boundary_executor is None:
        return await call(request)

    try:
        result: _T = await boundary_executor.execute(request, call)
        return result
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        raise map_connector_exception(exc, connector, operation) from exc
