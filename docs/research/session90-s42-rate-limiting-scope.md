# S42: Per-Tenant Rate Limiting and Quotas

## Scope

Add a per-tenant rate limiting system to AGENT-33 using the token bucket
algorithm with configurable tier-based limits.

## Architecture Decisions

### Token Bucket Algorithm

The token bucket algorithm provides:
- **Burst handling**: Allows short bursts up to `burst_size` without throttling
- **Steady-state enforcement**: Tokens refill at a rate of `requests_per_minute / 60` per second
- **Simplicity**: Well-understood, easy to reason about, deterministic

### In-Memory Storage

For the initial implementation, all rate limit state is held in memory using a
`dict[str, RateLimitState]` protected by `threading.Lock`. This avoids adding
a Redis dependency for rate limiting specifically (Redis is optional for the
overall application).

Future work: Redis-backed state for multi-instance deployments.

### Tier System

Four tiers with distinct limits:

| Tier      | RPM | RPH    | Daily  | Burst |
|-----------|-----|--------|--------|-------|
| free      | 10  | 200    | 1,000  | 5     |
| standard  | 60  | 2,000  | 10,000 | 15    |
| premium   | 200 | 10,000 | 50,000 | 50    |
| unlimited | -   | -      | -      | -     |

### Middleware Integration

`RateLimitMiddleware` (Starlette `BaseHTTPMiddleware`) runs after
`AuthMiddleware` so it can read `request.state.user.tenant_id`. If
`tenant_id` is empty, falls back to `request.state.user.sub`.

Bypass paths match the auth middleware's public paths (health, docs,
dashboard) so rate limiting only applies to authenticated API calls.

## Files Modified

| File | Change |
|------|--------|
| `engine/src/agent33/security/rate_limiter.py` | New: core rate limiter, models, middleware |
| `engine/src/agent33/api/routes/rate_limits.py` | New: admin endpoints |
| `engine/src/agent33/config.py` | Add `rate_limit_enabled`, `rate_limit_default_tier` |
| `engine/src/agent33/main.py` | Wire rate limiter into lifespan and middleware stack |
| `engine/tests/test_rate_limiter.py` | Comprehensive test suite |

## Config Fields

- `RATE_LIMIT_ENABLED` (bool, default: `True`) -- enable/disable rate limiting
- `RATE_LIMIT_DEFAULT_TIER` (str, default: `"standard"`) -- default tier for new tenants

## Admin Endpoints

- `GET /v1/admin/rate-limits` -- list all tenant quotas
- `GET /v1/admin/rate-limits/tiers` -- list available tiers and configs
- `GET /v1/admin/rate-limits/{tenant_id}` -- get tenant quota snapshot
- `PUT /v1/admin/rate-limits/{tenant_id}/tier` -- set tenant tier
- `POST /v1/admin/rate-limits/{tenant_id}/reset` -- reset tenant counters

All endpoints require `admin` scope.

## HTTP Headers

On every authenticated response:
- `X-RateLimit-Limit` -- per-minute limit
- `X-RateLimit-Remaining` -- remaining requests in current window
- `X-RateLimit-Reset` -- monotonic timestamp of next window reset

On 429 responses:
- `Retry-After` -- seconds until the client should retry

## Test Coverage

- Token bucket: refill, depletion, burst
- Per-tenant isolation
- Tier enforcement and tier changes
- Header values (X-RateLimit-*, Retry-After)
- Admin endpoints (list, get, set tier, reset)
- Health endpoint bypass
- Quota tracking accuracy
- Concurrent access thread safety
- Missing tenant_id fallback
