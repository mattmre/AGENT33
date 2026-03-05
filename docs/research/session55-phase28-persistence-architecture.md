# Session 55 — Phase 28: Security Scan Persistence Architecture

**Date:** 2026-03-09  
**Phase:** 28 — Security Hardening (remaining gaps)  
**Author:** Implementer Agent  

---

## Problem Statement

The `SecurityScanService` stores scan runs and findings exclusively in
in-memory Python dictionaries (`self._runs`, `self._findings`). Any process
restart or deployment loses all historical scan data, breaking auditability,
trend analysis, and the ability to enforce retention policies.

Three gaps were identified:

| # | Gap | Priority |
|---|-----|----------|
| 1 | SQLite persistence for scan runs + findings | HIGH |
| 2 | Finding deduplication across tools | MEDIUM |
| 3 | 90-day retention cleanup | MEDIUM |

---

## Architecture Decisions

### AD-1: SQLite as the persistence backend

**Decision:** Use SQLite via the stdlib `sqlite3` module with WAL journal mode.

**Rationale:**
- Zero-dependency — already in CPython stdlib.
- Follows the precedent set by `SQLiteLearningSignalStore` in
  `engine/src/agent33/improvement/persistence.py`.
- Configurable path allows `:memory:` for tests and a durable file in
  production (`/data/security_scans.db`).
- WAL mode provides concurrent-read safety for the API layer.

**Alternatives considered:**
- PostgreSQL — too heavy for a single-service embedded store; no external DB
  dependency is required at this stage.
- JSON file — already proven fragile for concurrent writes in the learning
  signal domain; migrated away from in Session 51.

### AD-2: Two normalised tables rather than a single JSON blob

**Decision:** Create `scan_runs` and `scan_findings` tables with typed columns.

**Rationale:**
- Enables indexed queries (`WHERE tenant_id = ?`, `WHERE created_at < ?`)
  without deserializing blobs.
- JSON columns (`tools_used`, `summary`) are used only for aggregate data
  that is never queried independently.
- Foreign-key cascade (`ON DELETE CASCADE`) ensures findings are removed
  automatically when a run is deleted or cleaned up.

### AD-3: SHA-256 fingerprint deduplication

**Decision:** Compute a deterministic fingerprint from five identity fields:
`tool + file_path + line_number + category + cwe_id`.

**Rationale:**
- Multiple scanners can report the same underlying issue (e.g. Bandit and
  Semgrep both flag a subprocess call). The fingerprint collapses true
  duplicates while preserving distinct findings from the same tool at
  different locations.
- SHA-256 is collision-resistant and produces a fixed-length hex string
  suitable for storage and indexing.
- First-occurrence-wins policy keeps the richest metadata (the first scanner
  that reported the issue).

### AD-4: Opt-in store injection (backward compatible)

**Decision:** `SecurityScanService.__init__` accepts an optional
`store: SecurityScanStore | None` parameter. When `None`, behaviour is
unchanged (pure in-memory).

**Rationale:**
- No existing callers are broken.
- Unit tests for the service that don't need persistence continue to work
  without change.
- The wiring layer (DI / app factory) can decide whether to inject a store
  based on configuration.

### AD-5: 90-day retention via `cleanup_expired_runs()`

**Decision:** A simple `DELETE WHERE created_at < cutoff` query with a
configurable `retention_days` parameter (default 90).

**Rationale:**
- Matches industry-standard compliance windows (SOC 2, ISO 27001 typically
  require ≥ 90 days of security logs).
- The method returns the count of deleted rows so callers can log / alert on
  bulk cleanups.
- Intended to be called from a periodic task (cron / scheduler), not
  automatically on every scan.

---

## Module Layout

```
engine/src/agent33/component_security/
├── __init__.py          # existing re-exports
├── models.py            # existing Pydantic domain models
├── dedup.py             # NEW — fingerprint + dedup helpers
├── persistence.py       # NEW — SecurityScanStore (SQLite)
├── llm_security.py      # existing
├── mcp_scanner.py       # existing
├── sarif.py             # existing
└── claude_security.py   # existing

engine/src/agent33/services/
└── security_scan.py     # MODIFIED — optional store injection

engine/tests/
└── test_security_persistence.py  # NEW — 22 tests
```

---

## Schema

```sql
CREATE TABLE scan_runs (
    id          TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL DEFAULT '',
    profile     TEXT NOT NULL,
    status      TEXT NOT NULL,
    started_at  TEXT,
    completed_at TEXT,
    target_path TEXT NOT NULL DEFAULT '',
    tools_used  TEXT NOT NULL DEFAULT '[]',   -- JSON array
    summary     TEXT NOT NULL DEFAULT '{}',   -- JSON object
    created_at  TEXT NOT NULL
);

CREATE TABLE scan_findings (
    id              TEXT PRIMARY KEY,
    run_id          TEXT NOT NULL,
    tool            TEXT NOT NULL DEFAULT '',
    file_path       TEXT NOT NULL DEFAULT '',
    line_number     INTEGER,
    severity        TEXT NOT NULL,
    category        TEXT NOT NULL,
    cwe_id          TEXT NOT NULL DEFAULT '',
    title           TEXT NOT NULL DEFAULT '',
    description     TEXT NOT NULL DEFAULT '',
    recommendation  TEXT NOT NULL DEFAULT '',
    fingerprint     TEXT NOT NULL DEFAULT '',
    created_at      TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES scan_runs(id) ON DELETE CASCADE
);
```

---

## Testing Strategy

- All store tests use `:memory:` SQLite — no filesystem side-effects.
- One explicit file-backed test validates durability across connections.
- Service integration tests use fake command runners that return canned
  Bandit / gitleaks JSON, avoiding any real subprocess execution.
- Deduplication tested independently with unit-level assertions.
- Cleanup tested by backdating `created_at` with `timedelta`.

---

## Future Work

- Add a periodic cleanup scheduler (cron-like) that calls
  `cleanup_expired_runs()` on a configurable interval.
- Expose persisted historical runs through the REST API for the dashboard.
- Add full-text search index on `scan_findings.title` + `description` for
  the security findings explorer UI.
- Consider migrating to PostgreSQL when multi-instance horizontal scaling
  is required.
