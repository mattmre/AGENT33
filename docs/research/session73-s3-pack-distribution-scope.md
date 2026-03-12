# Session 73 S3 Pack Distribution Scope

## Date

2026-03-12

## Context

Phase 33 already landed the local marketplace baseline:

- filesystem-backed marketplace catalog
- marketplace installs by pack name/version
- pack provenance signing and trust evaluation primitives

OpenClaw Track 4 should not rebuild that baseline. The remaining gap is the operator-facing distribution layer above it.

## Included In This Slice

1. Remote marketplace source support with cached index/download handling.
2. Aggregated marketplace browsing across local and remote sources.
3. Trust-policy visibility and update surfaces.
4. Pack upgrade and rollback flows with preserved tenant enablement.
5. Tenant enablement matrix read/write endpoints.

## Explicit Non-Goals

1. Frontend pack-management UI work.
2. New signer infrastructure beyond the existing HMAC-based provenance model.
3. Per-pack health checks and audit trail UX.
4. Full conflict-resolution UI.
5. Replacing the existing local marketplace routes.

## Implementation Shape

### Marketplace

- Add `RemotePackMarketplace` for remote index fetch and pack archive download.
- Add `MarketplaceAggregator` so the runtime can expose one combined marketplace view.
- Keep `LocalPackMarketplace` intact and treat it as one source within the aggregator.

### Trust

- Add a persisted `TrustPolicyManager` backed by the orchestration state store.
- Expose current trust policy and pack-specific trust/provenance detail via API routes.

### Lifecycle

- Add a `PackRollbackManager` that archives current installed revisions before upgrade.
- Add pack upgrade and rollback routes.
- Preserve tenant enablement by keeping the registry enablement map intact across upgrade/rollback.

### Operations

- Add a pack enablement matrix endpoint for operator inspection and bulk updates.

## Validation Plan

- unit tests for remote marketplace fetch/cache/download behavior
- unit tests for marketplace aggregation
- unit tests for trust-policy persistence
- unit tests for rollback and enablement preservation
- route tests for marketplace refresh, trust, matrix, upgrade, and rollback
