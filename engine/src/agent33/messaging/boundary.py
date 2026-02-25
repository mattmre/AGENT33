"""Connector boundary helpers for messaging adapters."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, TypeVar

from agent33.connectors.boundary import (
    build_connector_boundary_executor,
    map_connector_exception,
)
from agent33.connectors.models import ConnectorRequest

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

_T = TypeVar("_T")


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
    request = ConnectorRequest(
        connector=connector,
        operation=operation,
        payload=payload,
        metadata=metadata,
    )
    boundary_executor = build_connector_boundary_executor(
        default_timeout_seconds=timeout_seconds,
        retry_attempts=1,
    )

    if boundary_executor is None:
        return await call(request)

    try:
        return await boundary_executor.execute(request, call)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        raise map_connector_exception(exc, connector, operation) from exc
