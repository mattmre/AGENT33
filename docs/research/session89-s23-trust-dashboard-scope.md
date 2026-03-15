# S23: Phase 33 Trust Dashboard -- Scope

**Session**: 89
**Slice**: S23
**Date**: 2026-03-15
**Status**: Complete

## Objective

Add backend analytics for pack trust/provenance, exposing aggregate
trust metrics, trust chain inspection, audit trail, and batch signature
verification through a unified dashboard API.

## Deliverables

### 1. `engine/src/agent33/packs/trust_analytics.py`

New module containing:

- **TrustOverview** -- aggregate metrics (total/signed/unsigned counts,
  by-trust-level breakdown, signature rate, policy compliance counts).
- **TrustChainEntry** -- per-pack trust status (trust level, signer,
  signature validity, policy decision).
- **TrustAuditRecord** -- trust-relevant audit events from provenance
  collector.
- **TrustDashboardSummary** -- composite model combining overview,
  trust chain, audit trail, current policy, and optional curation stats.
- **TrustAnalyticsService** -- service class wiring PackRegistry,
  TrustPolicyManager, ProvenanceCollector, and CurationService.

### 2. API endpoints in `engine/src/agent33/api/routes/packs.py`

Five new endpoints under `/v1/packs/trust/`:

| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| GET | `/trust/dashboard` | agents:read | Full composite summary |
| GET | `/trust/overview` | agents:read | Aggregate trust metrics |
| GET | `/trust/chain` | agents:read | Per-pack trust chain entries |
| GET | `/trust/audit` | agents:read | Recent audit trail (limit param) |
| POST | `/trust/verify-all` | admin | Batch signature verification |

### 3. Lifespan wiring in `engine/src/agent33/main.py`

- TrustAnalyticsService created after pack registry and trust manager.
- Provenance collector back-wired after provenance subsystem init.
- Stored on `app.state.trust_analytics`.

### 4. Config addition in `engine/src/agent33/config.py`

- `pack_signing_key: str = ""` -- verification key for HMAC signature
  checks in batch verification.

### 5. Tests in `engine/tests/test_trust_dashboard.py`

Coverage:
- TrustOverview: mixed, all unsigned, all signed, empty, strict policy
- Trust chain: signed/unsigned, policy deny, signature verification
- Batch verification: valid, wrong key, no key, unsigned skipped, empty
- Audit trail: from collector, limit, no collector
- Dashboard composite: sections present, curation stats, JSON serialization
- API routes: all 5 endpoints, 503 when uninitialized
- Edge cases: model defaults, generated_at recency

## Dependencies

Existing infrastructure consumed (not modified beyond new imports):

- `packs/provenance_models.py` -- TrustLevel, PackProvenance, PackTrustPolicy
- `packs/provenance.py` -- sign_pack, verify_pack, evaluate_trust
- `packs/trust_manager.py` -- TrustPolicyManager
- `packs/registry.py` -- PackRegistry
- `packs/curation_service.py` -- CurationService
- `provenance/collector.py` -- ProvenanceCollector
- `provenance/models.py` -- ProvenanceReceipt, ProvenanceSource

## Design Decisions

1. **Lazy provenance wiring**: TrustAnalyticsService is created early
   (after pack registry) with `provenance_collector=None`, then the
   collector is back-wired after provenance subsystem init. This avoids
   reordering the lifespan init sequence.

2. **Optional verification key**: Signature verification in chain and
   batch endpoints is skipped when no key is configured, returning None
   instead of False.

3. **CurationService stats via duck-typing**: The service accepts any
   object with `list_curated()` method, making it testable with a
   simple fake without importing the full CurationService dependency
   chain.
