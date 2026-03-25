# P4.9: Multi-Replica E2E Testing Infrastructure -- Scope

## Included Work

1. **Docker Compose override** (`engine/docker-compose.multi.yml`): 2 API
   instances behind an nginx round-robin load balancer for local multi-replica
   testing.
2. **Nginx config** (`engine/nginx-multi.conf`): minimal upstream pointing at
   api-1 and api-2, round-robin distribution.
3. **Cross-instance E2E test suite** (`engine/tests/test_multi_replica_e2e.py`):
   unit-level tests that exercise multi-instance behavior without Docker (run in
   CI), plus integration-marked tests for the full Docker setup.
4. **Multi-replica smoke script** (`scripts/multi-replica-smoke.sh`): starts
   multi-instance compose, health-checks both instances, validates load
   balancing, tears down.
5. **This scope document.**

## Explicit Non-Goals

- Changing `maxReplicas` in the Kubernetes HPA or removing the single-instance
  guardrail. The architecture doc is clear: those changes require all blocking
  surfaces to be migrated first.
- Migrating any control-plane state from in-memory to shared storage. This
  slice is testing infrastructure only.
- Adding new Redis or PostgreSQL dependencies to the test suite. Lock tests
  use mock Redis via the existing `InProcessLock` pattern and manual Redis
  mock objects.
- Changing the existing `scaling/` package or any production code.

## Implementation Notes

### SQLite Repository Sharing

The three SQLite repositories (`SqliteSchedulerJobRepository`,
`SqliteJobHistoryRepository`, `SqliteWebhookRepository`) all use:
- `sqlite3.connect(db_path, check_same_thread=False)` -- allows cross-thread
  access
- `PRAGMA journal_mode=WAL` -- allows concurrent reads with a single writer

For cross-instance testing, two repository instances pointing at the same
on-disk temp file can demonstrate that writes from one instance are visible to
reads from the other. This validates the basic file-sharing model that would
apply when multiple pods mount a ReadWriteMany volume.

**Limitation**: SQLite WAL mode does not support concurrent writers from
separate processes at the filesystem level in all configurations. The tests
verify in-process cross-connection consistency, which is the right unit-test
boundary. True cross-process SQLite sharing would need the integration-tier
Docker tests.

### Distributed Lock Infrastructure

The `scaling/` package already provides:
- `RedisDistributedLock` -- SETNX-based lock with TTL and Lua release
- `InProcessLock` -- asyncio.Lock fallback for single-node
- `InstanceRegistry` -- Redis-based heartbeat registration
- `SingleInstanceGuard` -- raises `InstanceConflictError` if count > 1
- `SchedulerOwnershipGuard` -- wraps jobs with lock acquisition

The E2E tests validate these primitives' behavioral contracts (lock mutual
exclusion, TTL auto-release, release-then-acquire sequencing) using mock Redis
objects, since the tests must run in CI without a real Redis instance.

### Session Affinity

The `OperatorSessionService` maintains an in-memory `_active` cache. When two
instances share the same `FileSessionStorage` base directory, the on-disk
`session.json` is the durable handoff point, but the in-memory cache is
per-process. The test validates that one service instance can load a session
persisted by a different service instance via the shared storage layer.

## Validation Plan

1. `ruff check src/ tests/` -- zero errors
2. `ruff format --check src/ tests/` -- zero diffs
3. `mypy src --config-file pyproject.toml` -- zero errors
4. `pytest tests/ -x -q` -- all tests pass including new suite
5. New tests marked `@pytest.mark.integration` are skipped in CI but present
   for local Docker testing
