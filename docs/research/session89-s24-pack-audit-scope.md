# S24: Phase 33 Pack Audit Surfaces

**Session**: 89
**Slice**: S24
**Status**: Implemented
**Date**: 2026-03-15

## Scope

Add pack health monitoring and audit log browsing for operators. Builds on:
- S22 curation system (CurationService, QualityAssessment)
- S23 trust dashboard (TrustAnalyticsService, TrustOverview)
- Existing pack registry, provenance collector, conflicts detection

## Deliverables

### 1. Pack Audit Service (`engine/src/agent33/packs/audit.py`)

**Models**:
- `PackHealthStatus` (StrEnum): HEALTHY, DEGRADED, UNHEALTHY, UNKNOWN
- `PackHealthCheck`: per-pack health result with issues, skill counts, provenance, quality
- `PackHealthSummary`: aggregate health metrics (counts, health rate, top issues)
- `PackAuditEvent`: recorded lifecycle event with actor, versions, details
- `PackComplianceReport`: pass/fail checks against compliance rules

**Service** (`PackAuditService`):
- `check_pack_health(name)` -- single pack health (missing skills, provenance, quality, status)
- `check_all_health()` -- aggregate summary
- `get_health_details()` -- per-pack details for all packs
- `record_event(...)` -- bounded in-memory ring buffer (max 500)
- `get_audit_log(pack_name, event_type, limit)` -- filtered retrieval, newest first
- `compliance_check(name)` -- 5-point compliance check (manifest, provenance, quality, license, conflicts)

### 2. API Endpoints (added to `engine/src/agent33/api/routes/packs.py`)

| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| GET | `/v1/packs/health` | agents:read | Aggregate health summary |
| GET | `/v1/packs/health/details` | agents:read | Per-pack health details |
| GET | `/v1/packs/health/{name}` | agents:read | Single pack health |
| GET | `/v1/packs/audit` | agents:read | Audit log (filterable) |
| GET | `/v1/packs/audit/{name}` | agents:read | Pack-specific audit log |
| GET | `/v1/packs/compliance/{name}` | agents:read | Single pack compliance |
| POST | `/v1/packs/compliance/check-all` | admin | Batch compliance check |

### 3. Wiring (`engine/src/agent33/main.py`)

PackAuditService created after trust_analytics and curation_service. Stored on
`app.state.pack_audit`. Provenance collector back-wired later in initialization.

### 4. Tests (`engine/tests/test_pack_audit.py`)

Comprehensive tests covering:
- Health check states (healthy, degraded, unhealthy, unknown)
- Health summary with mixed states
- Curation quality integration
- Audit event recording and retrieval
- Filtering by pack_name, event_type, and limit
- Ring buffer eviction at capacity
- Compliance checks (all 5 rules)
- API endpoint behavior (success, 404, 503)

## Design Decisions

1. **In-memory ring buffer** for audit events (500 max). Persistent storage can be
   added later via the orchestration state store pattern used by CurationService.

2. **Health classification logic**: ERROR state = UNHEALTHY, missing skills = DEGRADED,
   disabled = DEGRADED, no provenance alone = HEALTHY (informational issue only).

3. **Compliance checks are synchronous** and run against in-memory state. No async
   I/O is required since all data comes from the pack registry and curation service.

## Dependencies

- `agent33.packs.registry.PackRegistry`
- `agent33.packs.trust_analytics.TrustAnalyticsService` (optional)
- `agent33.packs.curation_service.CurationService` (optional)
- `agent33.provenance.collector.ProvenanceCollector` (optional, back-wired)
