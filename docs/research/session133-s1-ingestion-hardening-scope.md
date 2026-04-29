# Session 133 S1 - Ingestion Hardening Scope Lock

## Why this note exists

The active authority docs already describe this slice as part of the closed
Sessions 131-132 ingestion wave, but `docs/research/` did not contain a
dedicated scope memo for the mailbox persistence plus retention/metrics
hardening pass. This note locks the exact implementation shape and points back
to the authoritative handoff sources.

## Authority

- `docs/next-session.md`
- `docs/phases/PHASE-PLAN-POST-P72-2026.md`
- `task_plan.md`
- `progress.md`

## Slice goal

Harden ingestion durability without reopening the broader ingestion
architecture:

1. persist non-candidate mailbox inbox events across restarts
2. add journal retention/expiry with configurable cleanup
3. persist task metrics with summary/history queries and configurable expiry

## Scope lock

### In scope

- Keep `candidate_asset` mailbox events on the existing fast path into
  `IntakePipeline.submit()`
- Persist only non-candidate mailbox inbox events in a dedicated SQLite store
- Add additive retention settings for ingestion journal and task metrics
- Run startup cleanup for expired journal and metrics rows
- Keep tenant-scoped reads and destructive drain behavior unchanged
- Reuse existing ingestion API endpoints for mailbox, heartbeat, metrics,
  metrics history, journal, and candidate history
- Reuse the existing SQLite persistence patterns already used by
  `ingestion.persistence` and `ingestion.notifications`

### Non-goals

- No lifecycle-state redesign
- No new event transport or worker system
- No new operator UX beyond existing mailbox/metrics/journal surfaces
- No cross-module observability redesign outside ingestion

## Implementation shape

- `engine/src/agent33/ingestion/mailbox.py`
  - continue routing `candidate_asset` directly to the intake pipeline
  - enqueue all other stamped events into a persistence backend when configured
  - keep `drain()` oldest-first and tenant-scoped
  - keep `heartbeat()` driven by inbox depth
- `engine/src/agent33/ingestion/mailbox_persistence.py`
  - dedicated SQLite table for mailbox inbox events
  - store full stamped event payload JSON plus tenant/event metadata
  - delete rows during drain after successful tenant readout
- `engine/src/agent33/ingestion/journal.py`
  - retain append-only journal semantics
  - add configurable expiry by `occurred_at`
  - cleanup must prune both SQLite rows and hydrated in-memory entries
- `engine/src/agent33/ingestion/metrics.py`
  - persist per-event task metrics in SQLite
  - expose tenant-scoped `summary()` and `history()`
  - add configurable expiry by `recorded_at`
  - cleanup must prune both SQLite rows and hydrated in-memory records
- `engine/src/agent33/main.py`
  - resolve approved state paths
  - construct mailbox/journal/metrics stores during lifespan startup
  - run one cleanup pass at startup
  - attach stores to `app.state`
  - close stores on shutdown
- `engine/src/agent33/config.py`
  - hold mailbox DB path, journal DB path, metrics DB path, and retention-day
    settings
- `engine/src/agent33/api/routes/ingestion.py`
  - keep the existing mailbox endpoints additive
  - record task metrics on mailbox post success/failure
  - expose tenant-scoped metrics summary/history reads

## Data model changes

- mailbox inbox table: `ingestion_mailbox_events`
- journal table: `ingestion_journal` with expiry driven by `occurred_at`
- task metrics table: `ingestion_task_metrics` with expiry driven by
  `recorded_at`
- all persistence remains additive and SQLite-backed; no migration away from the
  current ingestion stores

## API and behavior notes

- `POST /v1/ingestion/mailbox`
  - unchanged request contract
  - `candidate_asset` still bypasses the inbox
  - non-candidate events become durable
  - success/failure should be recorded in task metrics
- `GET /v1/ingestion/mailbox/drain`
  - returns tenant events oldest-first
  - deletes drained persisted rows
- `GET /v1/ingestion/heartbeat`
  - inbox depth should reflect persisted mailbox state
- `GET /v1/ingestion/metrics`
  - returns tenant-scoped aggregate counts and average latency
- `GET /v1/ingestion/metrics/history`
  - returns recent tenant-scoped records
- journal and candidate history reads remain additive; expiry should remove only
  stale entries, not alter current transition semantics

## Likely implementation files

- `engine/src/agent33/api/routes/ingestion.py`
- `engine/src/agent33/config.py`
- `engine/src/agent33/ingestion/mailbox.py`
- `engine/src/agent33/ingestion/mailbox_persistence.py`
- `engine/src/agent33/ingestion/journal.py`
- `engine/src/agent33/ingestion/metrics.py`
- `engine/src/agent33/main.py`

## Likely test files

- `engine/tests/test_ingestion_api.py`
- `engine/tests/test_ingestion_journal.py`
- `engine/tests/test_ingestion_mailbox.py`
- `engine/tests/test_ingestion_service.py`

## Main risks and dependencies

- Retention cleanup must update both persisted rows and in-memory hydrated
  caches, or reads will serve stale data after cleanup.
- Mailbox drain must stay tenant-scoped and oldest-first after persistence is
  introduced.
- Startup wiring must resolve approved state paths and close every SQLite handle
  cleanly to avoid Windows file-lock issues.
- On this host, validation should pin `PYTHONPATH` to the active worktree's
  `engine\src` so tests do not import the stale root checkout.

## Validation plan

- `Set-Location 'C:\GitHub\repos\AGENT33\worktrees\session133-s1-ingestion-hardening\engine'; $env:PYTHONPATH='C:\GitHub\repos\AGENT33\worktrees\session133-s1-ingestion-hardening\engine\src'; python -m pytest tests/test_ingestion_mailbox.py tests/test_ingestion_journal.py tests/test_ingestion_service.py tests/test_ingestion_api.py -q --no-cov`
- If implementation touches startup wiring beyond the focused ingestion modules,
  extend validation to the broader ingestion verification set already recorded in
  `progress.md`.
