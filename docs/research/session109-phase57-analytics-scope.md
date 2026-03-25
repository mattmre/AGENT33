# Session 109 - Phase 57: Session Analytics & Insights Engine

## Included Work

1. **InsightsEngine** (`engine/src/agent33/observability/insights.py`)
   - Aggregates session/invocation data from MetricsCollector and CostTracker
   - Produces InsightsReport dataclass with total sessions, tokens, cost, tool
     usage, model usage breakdown, daily activity histogram, and period metadata
   - Supports configurable time-window filtering (default 30 days)
   - Supports optional tenant_id filtering for multi-tenant isolation

2. **API Route** (`engine/src/agent33/api/routes/insights.py`)
   - `GET /v1/insights` with query params `days` (int, default 30) and
     `tenant_id` (optional str)
   - Auth-required via `require_scope("agents:read")` (read-level access)
   - Returns JSON serialization of InsightsReport
   - Module-level setter pattern consistent with dashboard.py

3. **Tests** (`engine/tests/test_insights.py`)
   - InsightsEngine unit tests: correct aggregation math, time-window
     filtering, per-tenant isolation, empty-data edge case
   - API route integration tests: JSON shape validation, query param handling,
     auth enforcement

4. **Wiring** (`engine/src/agent33/main.py`)
   - Import insights route, register router
   - Wire MetricsCollector and CostTracker to insights module in lifespan

## Explicit Non-Goals

- Persistent storage of analytics (insights are computed live from in-memory data)
- Historical trend comparison across server restarts
- Frontend/UI components for insights visualization
- Export to external analytics services (Datadog, Mixpanel, etc.)
- Session replay or trace correlation from the insights endpoint

## Implementation Notes

- CostTracker is not currently wired into app.state on main. The InsightsEngine
  will accept an optional CostTracker; when not provided, cost fields will
  return zero. This avoids adding a new lifespan dependency that does not
  exist yet.
- MetricsCollector stores timestamped observations, which enables time-window
  filtering. Counters do not have timestamps, so counter-based metrics
  (e.g., total sessions) represent lifetime counts when no CostTracker is
  available.
- The PricingCatalog (Phase 49) provides per-model cost estimation but is
  invoked per-call, not stored in MetricsCollector. The InsightsEngine uses
  CostTracker records when available.
- The dashboard route (`/v1/dashboard/`) is public. The insights route requires
  auth because it may expose cost data.

## Validation Plan

1. `ruff check src/ tests/` -- 0 errors
2. `ruff format --check src/ tests/` -- 0 diff
3. `mypy src --config-file pyproject.toml` -- 0 errors
4. `pytest tests/test_insights.py -v` -- all pass
5. Manual: verify `/v1/insights` returns valid JSON with expected shape
