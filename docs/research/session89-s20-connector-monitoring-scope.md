# S20: Phase 32 Connector Monitoring UX

Session 89 / Slice 20

## Summary

Adds runtime visibility into the connector boundary and MCP proxy fleet through
dedicated API endpoints, metrics collection, and enhanced diagnostics.

## Deliverables

### 1. CircuitBreaker Extensions (`circuit_breaker.py`)

- `total_trips` counter: incremented each time state transitions to OPEN
- `last_trip_at` timestamp: monotonic timestamp of last trip
- `on_state_change` callback: optional `(old_state, new_state) -> None`
- `snapshot()` method: serializable dict for API consumption

### 2. ConnectorMetricsCollector (`monitoring.py`)

New class tracking per-connector call metrics and circuit state-change events
in ring buffers. Provides:

- `record_call()` / `record_circuit_event()` for ingestion
- `get_connector_metrics()` / `get_all_metrics()` for query
- `get_circuit_events()` with configurable limit
- `list_known_connectors()`

### 3. Pydantic Response Models (`models.py`)

- `CircuitBreakerSnapshot`
- `ConnectorMetricsSummary`
- `ConnectorStatus`
- `ConnectorHealthSummary`
- `CircuitEvent`

### 4. Connector API Routes (`/v1/connectors`)

- `GET /v1/connectors` -- list all with state, circuit, metrics, health summary
- `GET /v1/connectors/health` -- fleet-level health counts only
- `GET /v1/connectors/{connector_id}` -- single connector detail
- `GET /v1/connectors/{connector_id}/events` -- circuit breaker event history

### 5. Health Endpoint Extension

`GET /health` now includes a `connectors` key reporting MCP proxy fleet status
(ok / degraded / unavailable / idle / unconfigured).

### 6. Operator Service Extension

`GET /v1/operator/status` inventories now include `proxy_servers` with count
and active (healthy + degraded) server count.

### 7. DOC-14 Diagnostics Enhancement

The MCP diagnostic check now probes individual server health states and circuit
breaker states. Reports WARNING for any server with circuit OPEN or state
UNHEALTHY/COOLDOWN.

### 8. Main Lifespan Wiring

`ConnectorMetricsCollector` created during lifespan, stored on
`app.state.connector_metrics`. Connectors router registered on app.

## Files Modified

- `engine/src/agent33/connectors/circuit_breaker.py`
- `engine/src/agent33/connectors/models.py`
- `engine/src/agent33/connectors/__init__.py`
- `engine/src/agent33/api/routes/health.py`
- `engine/src/agent33/operator/service.py`
- `engine/src/agent33/operator/diagnostics.py`
- `engine/src/agent33/main.py`

## Files Created

- `engine/src/agent33/connectors/monitoring.py`
- `engine/src/agent33/api/routes/connectors.py`
- `engine/tests/test_connector_monitoring.py`
- `docs/research/session89-s20-connector-monitoring-scope.md`
