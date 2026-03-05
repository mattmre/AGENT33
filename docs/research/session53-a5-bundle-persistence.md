# Session 53: A5 Synthetic Bundle Durable Persistence

Date: 2026-03-04
Scope: Priority 6 from `docs/next-session.md`

## Problem

The current synthetic environment service stores generated bundles only in memory. Process restart drops all generated bundles, which blocks downstream A5/A6 comparative workflows that need reproducible bundle IDs across sessions.

## Baseline reviewed

- `engine/src/agent33/evaluation/synthetic_envs/service.py`
- `engine/src/agent33/main.py`
- `engine/src/agent33/config.py`
- `engine/tests/test_synthetic_environment_service.py`
- `engine/tests/test_synthetic_environment_api.py`

## Design

Add optional file-backed persistence to `SyntheticEnvironmentService`:

- new constructor arg: `persistence_path: str | Path | None`
- on startup:
  - load persisted bundle order + bundle payloads if file exists
  - validate and retain only up to `max_saved_bundles`
- on new bundle generation:
  - store in memory (existing behavior)
  - persist updated state atomically to disk

Persisted format:

```json
{
  "bundle_order": ["BND-..."],
  "bundles": [{...SyntheticEnvironmentBundle...}]
}
```

## Runtime wiring

- add config key `synthetic_env_bundle_persistence_path` (default file under `var/`)
- pass path from app startup into `SyntheticEnvironmentService`

## Non-goals

- no database schema migration
- no cross-node/distributed lock coordination
- no bundle indexing/query expansion beyond current APIs
