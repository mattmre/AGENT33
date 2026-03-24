# P1.3 Connection Pooling and Resource Lifecycle Hardening

## Current Connection Setup

### SQLAlchemy Async Engine (PostgreSQL)

- **Module**: `engine/src/agent33/memory/long_term.py`
- **Call**: `create_async_engine(database_url, echo=False)`
- **Pool parameters**: None explicitly set. Uses SQLAlchemy defaults:
  - `pool_size=5`
  - `max_overflow=10`
  - `pool_pre_ping=False`
  - `pool_recycle=-1` (disabled)
- **Problem**: Under production load, 5 connections with 10 overflow is likely
  too low. Without `pool_pre_ping`, stale connections after PostgreSQL restarts
  cause intermittent errors. Without `pool_recycle`, long-lived connections can
  hit server-side timeouts or firewall idle-connection reaping.

### Redis (redis.asyncio)

- **Module**: `engine/src/agent33/main.py` lifespan
- **Call**: `aioredis.from_url(settings.redis_url, decode_responses=True)`
- **Pool parameters**: None explicitly set. `redis.asyncio.from_url` creates a
  `ConnectionPool` internally with `max_connections=2**31` (effectively
  unlimited). This is the standard and correct behavior for the redis-py async
  client.
- **Assessment**: Already pooled. Adding explicit `max_connections` from config
  provides operator control over connection pressure under load, but the
  current behavior is not broken. This slice adds a `redis_max_connections`
  config field and wires it in.

### NATS Client

- **Module**: `engine/src/agent33/messaging/bus.py`
- **Lifecycle**:
  - `connect()`: `await nats.connect(self._url)`
  - `close()`: `await self._nc.drain()` then `self._nc = None`
- **Shutdown path in main.py**: `if nats_bus.is_connected: await nats_bus.close()`
- **Assessment**: NATS drain/close lifecycle is already correct. Drain flushes
  pending messages before closing, which is the recommended shutdown pattern.
  No changes needed.

## What This Slice Adds

### Config Fields (config.py)

| Field | Type | Default | Purpose |
| --- | --- | --- | --- |
| `db_pool_size` | `int` | `10` | SQLAlchemy async pool core size |
| `db_max_overflow` | `int` | `20` | Extra connections above pool_size |
| `db_pool_pre_ping` | `bool` | `True` | Test connections before checkout |
| `db_pool_recycle` | `int` | `1800` | Recycle connections after 30 min |
| `redis_max_connections` | `int` | `50` | Max Redis connection pool size |

### LongTermMemory Constructor (memory/long_term.py)

Accept pool parameters in `__init__` and pass them to `create_async_engine`.

### Main Lifespan Wiring (main.py)

Pass settings pool values when constructing `LongTermMemory` and the Redis
client.

## Explicit Non-Goals

- Query optimization or SQL tuning
- Scaling runtime changes (P1.2 already merged)
- ORM schema changes or migrations
- NATS lifecycle changes (already correct)
- Replacing Redis with a different client library
- Multi-replica coordination (addressed by P1.2)
- Load testing (addressed by P1.5)

## Validation Plan

1. Config fields exist with correct types and defaults
2. `LongTermMemory` passes pool params to `create_async_engine` (verified by
   mocking `create_async_engine` and inspecting kwargs)
3. Redis `from_url` receives `max_connections` from config (verified by
   mocking `from_url` and inspecting kwargs)
4. NATS drain/close is called on shutdown (verified by mocking NATS client)
5. Ruff check, ruff format, and mypy all pass
