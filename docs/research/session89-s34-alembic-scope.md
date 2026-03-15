# S34: Alembic CI Migration Automation

**Session**: 89
**Date**: 2026-03-15
**Status**: Implemented

## Scope

Add offline Alembic migration chain validation to AGENT-33. The system
inspects migration script files directly (AST parsing) to validate chain
integrity, detect multiple heads, and list revisions -- all without requiring
a database connection or running Alembic environment.

## Deliverables

### New files

| File | Purpose |
|------|---------|
| `engine/src/agent33/migrations/__init__.py` | Package init with exports |
| `engine/src/agent33/migrations/checker.py` | `MigrationChecker` + `MigrationStatus` model |
| `engine/src/agent33/api/routes/migrations.py` | `GET /v1/migrations/status`, `GET /v1/migrations/revisions` |
| `engine/tests/test_migration_checker.py` | Full test suite |
| `docs/research/session89-s34-alembic-scope.md` | This scope doc |

### Modified files

| File | Change |
|------|--------|
| `engine/src/agent33/config.py` | Added `alembic_config_path`, `alembic_auto_check_on_startup` |
| `engine/src/agent33/main.py` | Imports migrations routes, registers router, initializes checker in lifespan |

## Architecture

### Offline mode (default)

The `MigrationChecker` parses Alembic migration `.py` files using Python's
`ast` module.  It extracts `revision`, `down_revision`, `branch_labels`, and
`depends_on` from module-level assignments (both plain and annotated styles).

Offline operations:
- `list_revisions()` -- enumerate all discovered scripts with metadata
- `validate_chain()` -- check for orphans, duplicates, multiple roots
- `detect_conflicts()` -- detect multiple heads (merge needed)
- `get_status()` -- composite snapshot combining all checks

### Online mode (optional)

`check_pending(db_url=...)` uses Alembic's `MigrationContext` with a
synchronous SQLAlchemy engine to compare the database revision against the
chain head.  Requires a live database.

### API endpoints

Both endpoints are admin-scoped (`require_scope("admin")`):

- `GET /v1/migrations/status` -- returns `MigrationStatus` JSON
- `GET /v1/migrations/revisions` -- returns list of revision metadata dicts

### Startup integration

When `alembic_auto_check_on_startup=True`, the lifespan logs the chain
status at startup.  Chain errors and multiple heads are logged as warnings.

## Design decisions

1. **AST parsing over subprocess**: Avoids spawning `alembic` CLI processes.
   More reliable in CI, no PATH requirements, handles both annotated and plain
   assignment styles.

2. **Alembic is a direct dependency**: Already in `pyproject.toml`
   (`alembic>=1.14,<2`), so we can import it directly for online checks.
   Offline checks do not import alembic at all.

3. **Admin scope for API**: Migration status is infrastructure metadata; only
   admins should see it.

4. **Caching**: Revisions are lazily loaded and cached on the checker instance.
   The checker is instantiated once during lifespan and reused.
