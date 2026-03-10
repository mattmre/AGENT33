# Session 64 Phase 33 Marketplace Integration

## Objective

Activate the dormant pack marketplace contract with a concrete MVP that supports:

- browsing available marketplace packs
- searching marketplace packs
- viewing pack detail and version history
- installing marketplace packs through the existing pack registry

## Problem

Phase 33 pack models already exposed `source_type="marketplace"` on `PackSource`, but
the runtime rejected every marketplace install attempt as unsupported. That left the
distribution layer partially modeled but non-functional.

## Delivered Slice

This session implements a local-registry-backed marketplace MVP instead of inventing a
remote service that the repo does not yet contain.

### Catalog model

- Added `LocalPackMarketplace` under `engine/src/agent33/packs/marketplace.py`
- Scans a configured filesystem root for `PACK.yaml` or `pack.yaml`
- Groups entries by manifest `name`
- Sorts available versions with the existing semantic version parser
- Resolves latest or explicit versions to concrete pack directories

### Registry integration

- Added `pack_marketplace_dir` configuration
- Wired `LocalPackMarketplace` into FastAPI lifespan initialization
- Extended `PackRegistry.install()` to support `source_type="marketplace"`
- Preserved local install behavior unchanged
- Marks installed marketplace packs with `source="marketplace"`

### API surface

- Added `/v1/marketplace/packs`
- Added `/v1/marketplace/packs/{name}`
- Added `/v1/marketplace/packs/{name}/versions`
- Added `/v1/marketplace/search`
- Added `/v1/marketplace/install`
- Updated `/v1/packs/install` so the existing install route now honors marketplace sources

## Why This Shape

This is the smallest complete slice that fulfills the Phase 33 intent without
shipping a fake network marketplace. The catalog is real, installable, testable,
and compatible with future promotion to a remote-backed registry.

## Verification

- registry tests cover latest-version marketplace install, explicit-version install,
  and missing-pack failure
- pack route tests cover marketplace install through `/v1/packs/install`
- dedicated marketplace route tests cover browse, detail, versions, search, and install
- pack integration and version suites were rerun to verify no regression in adjacent logic
