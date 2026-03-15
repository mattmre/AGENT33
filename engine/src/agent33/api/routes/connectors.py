"""Connector monitoring API routes (Phase 32 UX)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from agent33.connectors.models import (
    CircuitBreakerSnapshot,
    CircuitEvent,
    ConnectorHealthSummary,
    ConnectorMetricsSummary,
    ConnectorStatus,
)

router = APIRouter(prefix="/v1/connectors", tags=["connectors"])


def _get_proxy_manager(request: Request) -> Any:
    """Return the proxy manager from app.state, or None."""
    return getattr(request.app.state, "proxy_manager", None)


def _get_connector_metrics(request: Request) -> Any:
    """Return the ConnectorMetricsCollector from app.state, or None."""
    return getattr(request.app.state, "connector_metrics", None)


def _build_proxy_statuses(proxy_manager: Any) -> list[ConnectorStatus]:
    """Build ConnectorStatus entries from the MCP proxy fleet."""
    statuses: list[ConnectorStatus] = []
    if proxy_manager is None:
        return statuses
    for summary in proxy_manager.list_servers():
        circuit_snap = None
        server_handle = proxy_manager.get_server(summary["id"])
        if server_handle is not None and hasattr(server_handle, "circuit_breaker"):
            cb = server_handle.circuit_breaker
            if hasattr(cb, "snapshot"):
                circuit_snap = CircuitBreakerSnapshot(**cb.snapshot())
            else:
                circuit_snap = CircuitBreakerSnapshot(
                    state=cb.state.value,
                    consecutive_failures=cb.consecutive_failures,
                    total_trips=getattr(cb, "total_trips", 0),
                    last_trip_at=getattr(cb, "last_trip_at", None),
                    failure_threshold=cb.failure_threshold,
                    recovery_timeout_seconds=cb.recovery_timeout_seconds,
                    half_open_success_threshold=cb.half_open_success_threshold,
                )
        statuses.append(
            ConnectorStatus(
                connector_id=summary["id"],
                name=summary.get("name", summary["id"]),
                connector_type="mcp_proxy",
                state=summary.get("state", "unknown"),
                circuit=circuit_snap,
            )
        )
    return statuses


def _build_boundary_statuses(connector_metrics: Any, proxy_ids: set[str]) -> list[ConnectorStatus]:
    """Build ConnectorStatus entries from boundary-level metrics."""
    statuses: list[ConnectorStatus] = []
    if connector_metrics is None:
        return statuses
    for cid in connector_metrics.list_known_connectors():
        if cid in proxy_ids:
            continue
        raw = connector_metrics.get_connector_metrics(cid)
        statuses.append(
            ConnectorStatus(
                connector_id=cid,
                name=cid,
                connector_type="boundary",
                state="active" if raw["total_calls"] > 0 else "idle",
                metrics=ConnectorMetricsSummary(**raw),
            )
        )
    return statuses


def _compute_health_summary(
    statuses: list[ConnectorStatus],
) -> ConnectorHealthSummary:
    """Derive fleet-level counts from connector statuses."""
    total = len(statuses)
    healthy = 0
    degraded = 0
    open_circuit = 0
    stopped = 0
    for s in statuses:
        if s.state in {"healthy", "active", "closed"}:
            healthy += 1
        elif s.state == "degraded":
            degraded += 1
        elif s.state == "stopped":
            stopped += 1
        elif s.state in {"open", "unhealthy", "cooldown"} or (
            s.circuit is not None and s.circuit.state == "open"
        ):
            open_circuit += 1
        else:
            # idle or unknown -- count as healthy
            healthy += 1
    return ConnectorHealthSummary(
        total=total,
        healthy=healthy,
        degraded=degraded,
        open_circuit=open_circuit,
        stopped=stopped,
    )


@router.get("")
async def list_connectors(
    request: Request,
) -> dict[str, Any]:
    """List all known connectors with current state, circuit snapshot, and metrics."""
    proxy_manager = _get_proxy_manager(request)
    connector_metrics = _get_connector_metrics(request)

    proxy_statuses = _build_proxy_statuses(proxy_manager)
    proxy_ids = {s.connector_id for s in proxy_statuses}

    # Attach metrics to proxy statuses when available
    if connector_metrics is not None:
        for ps in proxy_statuses:
            raw = connector_metrics.get_connector_metrics(ps.connector_id)
            if raw["total_calls"] > 0:
                ps.metrics = ConnectorMetricsSummary(**raw)

    boundary_statuses = _build_boundary_statuses(connector_metrics, proxy_ids)
    all_statuses = proxy_statuses + boundary_statuses
    summary = _compute_health_summary(all_statuses)

    return {
        "connectors": [s.model_dump() for s in all_statuses],
        "health": summary.model_dump(),
    }


@router.get("/health")
async def connector_health(request: Request) -> dict[str, Any]:
    """Return just the fleet-level ConnectorHealthSummary."""
    proxy_manager = _get_proxy_manager(request)
    connector_metrics = _get_connector_metrics(request)

    proxy_statuses = _build_proxy_statuses(proxy_manager)
    proxy_ids = {s.connector_id for s in proxy_statuses}
    boundary_statuses = _build_boundary_statuses(connector_metrics, proxy_ids)
    all_statuses = proxy_statuses + boundary_statuses
    summary = _compute_health_summary(all_statuses)

    return summary.model_dump()


@router.get("/{connector_id}")
async def get_connector(request: Request, connector_id: str) -> dict[str, Any]:
    """Return a single connector's detail with full metrics."""
    proxy_manager = _get_proxy_manager(request)
    connector_metrics = _get_connector_metrics(request)

    # Check proxy fleet first
    if proxy_manager is not None:
        handle = proxy_manager.get_server(connector_id)
        if handle is not None:
            summary = handle.status_summary()
            circuit_snap = None
            if hasattr(handle, "circuit_breaker"):
                cb = handle.circuit_breaker
                if hasattr(cb, "snapshot"):
                    circuit_snap = CircuitBreakerSnapshot(**cb.snapshot())
            metrics = None
            if connector_metrics is not None:
                raw = connector_metrics.get_connector_metrics(connector_id)
                if raw["total_calls"] > 0:
                    metrics = ConnectorMetricsSummary(**raw)
            status = ConnectorStatus(
                connector_id=connector_id,
                name=summary.get("name", connector_id),
                connector_type="mcp_proxy",
                state=summary.get("state", "unknown"),
                circuit=circuit_snap,
                metrics=metrics,
            )
            return status.model_dump()

    # Check boundary metrics
    if connector_metrics is not None:
        known = connector_metrics.list_known_connectors()
        if connector_id in known:
            raw = connector_metrics.get_connector_metrics(connector_id)
            status = ConnectorStatus(
                connector_id=connector_id,
                name=connector_id,
                connector_type="boundary",
                state="active" if raw["total_calls"] > 0 else "idle",
                metrics=ConnectorMetricsSummary(**raw),
            )
            return status.model_dump()

    raise HTTPException(status_code=404, detail=f"Connector '{connector_id}' not found")


@router.get("/{connector_id}/events")
async def get_connector_events(
    request: Request,
    connector_id: str,
    limit: int = 20,
) -> dict[str, Any]:
    """Return circuit breaker event history for a connector."""
    connector_metrics = _get_connector_metrics(request)
    if connector_metrics is None:
        return {"connector_id": connector_id, "events": []}

    raw_events = connector_metrics.get_circuit_events(connector_id, limit=limit)
    events = [
        CircuitEvent(
            connector_id=e["connector_id"],
            old_state=e["old_state"],
            new_state=e["new_state"],
            timestamp=e["timestamp"],
        ).model_dump()
        for e in raw_events
    ]
    return {"connector_id": connector_id, "events": events}
