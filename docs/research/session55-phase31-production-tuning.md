# Phase 31 — Production Tuning Guide for Learning Signals

**Session:** 55
**Phase:** 31 — Continuous Learning & Signal Capture
**Date:** 2026-03-07

## Overview

Phase 31 introduces continuous learning-signal capture, trend analytics, threshold
calibration, and durable persistence for the improvement pipeline.  This document
covers default configuration values, recommended tuning for production
environments, and operator workflows for backup/restore.

---

## Default Configuration Values

| Setting | Default | Description |
|---|---|---|
| `improvement_learning_enabled` | `false` | Feature gate — must be `true` to expose learning signal endpoints. |
| `improvement_learning_persistence_backend` | `memory` | Persistence backend: `memory`, `file`, or `db` (SQLite). |
| `improvement_learning_persistence_path` | `var/improvement_learning_signals.json` | Path for file-based persistence. |
| `improvement_learning_persistence_db_path` | `var/improvement_learning_signals.sqlite3` | Path for SQLite persistence. |
| `improvement_learning_persistence_migrate_on_start` | `false` | Auto-migrate file state to SQLite on startup. |
| `improvement_learning_persistence_migration_backup_on_start` | `false` | Create a backup before migration. |
| `improvement_learning_persistence_migration_backup_path` | `var/improvement_learning_signals.backup.json` | Backup path for migration snapshots. |
| `improvement_learning_file_corruption_behavior` | `reset` | Behavior on corrupt file: `reset` (quarantine & continue) or `raise`. |
| `improvement_learning_db_corruption_behavior` | `reset` | Behavior on corrupt SQLite database: `reset` (quarantine & continue) or `raise`. |
| `improvement_learning_dedupe_window_minutes` | `30` | Time window (minutes) for deduplication of identical signals. |
| `improvement_learning_retention_days` | `180` | Maximum age (days) of retained signals before pruning. |
| `improvement_learning_max_signals` | `5000` | Maximum number of signals retained in the store. |
| `improvement_learning_max_generated_intakes` | `1000` | Maximum number of auto-generated intake records retained. |
| `improvement_learning_summary_default_limit` | `50` | Default `limit` for the summary endpoint when not specified. |
| `improvement_learning_auto_intake_enabled` | `false` | Enable automatic intake generation from high-severity signals. |
| `improvement_learning_auto_intake_min_severity` | `high` | Minimum severity for auto-intake generation. |
| `improvement_learning_auto_intake_max_items` | `3` | Maximum intakes generated per summary request. |
| `improvement_learning_auto_intake_min_quality` | `0.45` | Minimum quality score (0.0–1.0) for a signal to trigger auto-intake. |

---

## Production Tuning Recommendations

### 1. Choose the Right Persistence Backend

| Environment | Recommended Backend | Notes |
|---|---|---|
| Development / CI | `memory` | No disk I/O; state resets on restart. |
| Staging | `file` | Simple JSON file; easy to inspect. |
| Production | `db` (SQLite) | ACID writes, atomic commits, handles concurrent reads. |

When switching from `file` to `db`, enable the migration flag on first deploy:

```env
improvement_learning_persistence_backend=db
improvement_learning_persistence_migrate_on_start=true
improvement_learning_persistence_migration_backup_on_start=true
```

After the first successful start, set `migrate_on_start` back to `false` to avoid
unnecessary migration checks.

### 2. Tune Deduplication Window

The default 30-minute dedupe window merges signals with identical
`(tenant_id, signal_type, summary, source)` fingerprints.

- **High-noise environments** (frequent CI runs, automated monitors):
  increase to `60`–`120` minutes.
- **Low-volume, manual reporting**: decrease to `5`–`15` minutes or set to `0`
  to disable deduplication entirely.

```env
improvement_learning_dedupe_window_minutes=60
```

### 3. Set Retention and Capacity Limits

For production workloads, size limits prevent unbounded growth:

| Workload Size | `max_signals` | `max_generated_intakes` | `retention_days` |
|---|---|---|---|
| Small team (≤ 5 agents) | 2000 | 500 | 90 |
| Medium team (5–20 agents) | 5000 | 1000 | 180 |
| Large / multi-tenant | 10000 | 2000 | 365 |

Older signals are pruned on each write operation, newest-first.

### 4. Configure Auto-Intake Generation

Auto-intake converts high-severity learning signals into research intake records
for triage.  Start conservative and relax thresholds after observing the
calibration endpoint:

```env
improvement_learning_auto_intake_enabled=true
improvement_learning_auto_intake_min_severity=high
improvement_learning_auto_intake_max_items=3
improvement_learning_auto_intake_min_quality=0.6
```

Use the `GET /v1/improvements/learning/calibration` endpoint to get
data-driven threshold recommendations based on recent signal activity.
When the tuning loop is enabled, the active runtime policy becomes the source
of truth for `auto_intake_min_severity`, `auto_intake_max_items`, and
`auto_intake_min_quality`; calibration snapshots compare against that live
policy rather than only the boot-time environment values.

### 5. Corruption Handling

Both `file` and `db` backends support two corruption behaviors:

- **`reset`** (default, recommended for production): quarantines the corrupt
  file/payload into a `.corrupt` sidecar and resets to empty state.  Structured
  logs are emitted via `structlog` with event `learning_signal_corruption_detected`,
  including the quarantine path, original path, timestamp, and error details.
- **`raise`**: throws a `ValueError`, halting startup.  Useful in CI or staging
  where corruption should be a hard failure.

Monitor structured log events for `learning_signal_corruption_detected` to alert
on data integrity issues.

### 6. Operator Backup / Restore

Two operator-facing API endpoints support portable state backup and restore:

- **`POST /v1/improvements/learning/backup`** — creates a JSON snapshot of
  all signals and generated intakes.
- **`POST /v1/improvements/learning/restore`** — restores state from a
  previously created backup file.

#### Backup workflow

```bash
curl -X POST http://localhost:8000/v1/improvements/learning/backup \
  -H "Content-Type: application/json" \
  -d '{"backup_path": "/var/backups/learning_2026-03-07.json"}'
```

Response:
```json
{
  "status": "ok",
  "backup_path": "/var/backups/learning_2026-03-07.json",
  "signal_count": 142,
  "intake_count": 12
}
```

#### Restore workflow

```bash
curl -X POST http://localhost:8000/v1/improvements/learning/restore \
  -H "Content-Type: application/json" \
  -d '{"backup_path": "/var/backups/learning_2026-03-07.json"}'
```

The restore endpoint reloads the service after writing, so all subsequent API
calls reflect the restored state.

---

## Calibration Endpoint

The `GET /v1/improvements/learning/calibration` endpoint analyzes recent signal
activity and recommends production-appropriate thresholds:

```bash
curl "http://localhost:8000/v1/improvements/learning/calibration?window_days=14"
```

The response includes:

- `recommended_auto_intake_min_quality` — suggested quality floor
- `recommended_auto_intake_min_severity` — suggested minimum severity
- `recommended_auto_intake_max_items` — suggested cap per window
- `recommended_retention_days` — suggested retention period
- `rationale` — human-readable explanation of the recommendations

Run calibration periodically (e.g., weekly) and compare recommendations against
the active runtime policy.  Adjust environment variables when recommendations
diverge significantly from active configuration.
