# P4.15: Alembic Rolling Deploy Migration Testing

## Scope

Add a comprehensive test suite that validates Alembic migration safety for
rolling deploys. In a rolling deploy, two application versions coexist
momentarily: the new code (version N) runs alongside old code (version N-1)
while the database schema transitions forward.

## Included Work

1. **Migration chain structural validation** -- verify that every migration
   file declares revision/down\_revision correctly and that the chain is
   linear (single root, single head, no orphans). Extends existing
   `test_alembic_migration_chain.py`.

2. **Upgrade/downgrade symmetry** -- verify that each migration script
   declares both `upgrade()` and `downgrade()` with real bodies (not empty
   `pass` stubs for migrations that change schema).

3. **N-1 schema compatibility analysis** -- for each migration step, verify
   that the ORM model columns used by application code at version N remain
   compatible with the schema at version N-1. This catches rolling-deploy
   failures where new code queries a column that doesn't yet exist.

4. **Migration metadata consistency** -- verify that migration filenames
   follow the sequential numbering convention, that revision IDs match
   filename prefixes, and that `down_revision` links form a strict chain.

5. **Data preservation analysis** -- for each migration, classify whether it
   is additive-only (safe for rolling deploy) or destructive (requires
   downtime). Flag destructive migrations with appropriate markers.

## Explicit Non-Goals

- **Running actual Alembic against a live PostgreSQL database** -- these tests
  parse migration files and ORM models statically. PostgreSQL-dependent
  execution tests are marked `@pytest.mark.integration` and skipped in CI
  unless a database is available.
- **Rewriting existing migrations** -- we test what exists; we do not modify
  001 or 002.
- **ORM model changes** -- no production code changes.
- **Modifying `alembic/env.py`** -- the environment configuration is not
  touched.

## Implementation Notes

- Both existing migrations use PostgreSQL-specific features (pgvector, JSONB,
  UUID). Pure SQLite execution of the migration SQL is not possible.
- Migration 002 is explicitly destructive (drops and re-creates embedding
  column). The test suite must detect and flag this.
- The ORM model in `checkpoint.py` uses `String(36)` for `id` and
  `String(128)` for workflow/step IDs, while migration 001 uses `UUID` and
  `Text()`. This mismatch is tolerable at runtime because PostgreSQL
  handles the type coercion, but the test should document it.
- The test file is `engine/tests/test_alembic_rolling_deploy.py`.

## Validation Plan

1. `python -m pytest tests/test_alembic_rolling_deploy.py -q` -- all
   non-integration tests pass.
2. `python -m ruff check tests/test_alembic_rolling_deploy.py` -- no lint
   errors.
3. `python -m ruff format --check tests/test_alembic_rolling_deploy.py` --
   properly formatted.
4. `python -m mypy tests/test_alembic_rolling_deploy.py --config-file
   pyproject.toml` -- no type errors.
