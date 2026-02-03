"""Rate limiting for multi-tenant requests."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from agent33.tenancy.middleware import get_current_tenant
from agent33.tenancy.models import TenantContext

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter using sliding window.

    For production use with multiple workers, consider using Redis
    via the RedisRateLimiter class.
    """

    def __init__(self, window_seconds: int = 60) -> None:
        """Initialize the rate limiter.

        Args:
            window_seconds: The sliding window size in seconds.
        """
        self.window_seconds = window_seconds
        # tenant_id -> list of request timestamps
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check(self, tenant_id: UUID, limit: int) -> bool:
        """Check if a request is allowed under the rate limit.

        Args:
            tenant_id: The tenant making the request.
            limit: Maximum requests allowed in the window.

        Returns:
            True if the request is allowed, False if rate limited.
        """
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            key = str(tenant_id)

            # Remove expired entries
            self._requests[key] = [
                ts for ts in self._requests[key] if ts > cutoff
            ]

            # Check limit
            if len(self._requests[key]) >= limit:
                return False

            # Record this request
            self._requests[key].append(now)
            return True

    async def get_remaining(self, tenant_id: UUID, limit: int) -> int:
        """Get the number of remaining requests in the current window.

        Args:
            tenant_id: The tenant to check.
            limit: The tenant's rate limit.

        Returns:
            Number of remaining requests allowed.
        """
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds
            key = str(tenant_id)

            # Count active requests
            active = len([ts for ts in self._requests[key] if ts > cutoff])
            return max(0, limit - active)

    def clear(self) -> None:
        """Clear all rate limit data. Useful for testing."""
        self._requests.clear()


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


class RedisRateLimiter:
    """Redis-backed rate limiter for distributed deployments.

    Uses a sliding window algorithm with sorted sets.
    """

    def __init__(self, redis_url: str, window_seconds: int = 60) -> None:
        """Initialize the Redis rate limiter.

        Args:
            redis_url: Redis connection URL.
            window_seconds: The sliding window size in seconds.
        """
        self.redis_url = redis_url
        self.window_seconds = window_seconds
        self._redis = None

    async def _get_redis(self):
        """Lazily initialize Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self.redis_url)
            except ImportError:
                logger.warning("redis package not installed, rate limiting disabled")
                return None
        return self._redis

    async def check(self, tenant_id: UUID, limit: int) -> bool:
        """Check if a request is allowed under the rate limit.

        Args:
            tenant_id: The tenant making the request.
            limit: Maximum requests allowed in the window.

        Returns:
            True if the request is allowed, False if rate limited.
        """
        redis = await self._get_redis()
        if redis is None:
            return True  # Allow if Redis unavailable

        now = time.time()
        key = f"ratelimit:{tenant_id}"

        # Lua script for atomic sliding window
        script = """
        local key = KEYS[1]
        local now = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local limit = tonumber(ARGV[3])
        local cutoff = now - window

        -- Remove old entries
        redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)

        -- Count current requests
        local count = redis.call('ZCARD', key)

        if count < limit then
            -- Add new request
            redis.call('ZADD', key, now, now .. math.random())
            redis.call('EXPIRE', key, window)
            return 1
        else
            return 0
        end
        """

        try:
            result = await redis.eval(
                script, 1, key, now, self.window_seconds, limit
            )
            return result == 1
        except Exception as e:
            logger.error("Redis rate limit check failed: %s", e)
            return True  # Allow on error

    async def get_remaining(self, tenant_id: UUID, limit: int) -> int:
        """Get the number of remaining requests in the current window.

        Args:
            tenant_id: The tenant to check.
            limit: The tenant's rate limit.

        Returns:
            Number of remaining requests allowed.
        """
        redis = await self._get_redis()
        if redis is None:
            return limit

        now = time.time()
        cutoff = now - self.window_seconds
        key = f"ratelimit:{tenant_id}"

        try:
            # Count requests in window
            count = await redis.zcount(key, cutoff, now)
            return max(0, limit - count)
        except Exception as e:
            logger.error("Redis rate limit check failed: %s", e)
            return limit

    async def close(self) -> None:
        """Close the Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


async def check_rate_limit(
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> TenantContext:
    """FastAPI dependency that enforces rate limiting.

    Usage:
        @app.get("/api/data")
        async def get_data(tenant: TenantContext = Depends(check_rate_limit)):
            ...

    Returns:
        The TenantContext if the request is allowed.

    Raises:
        HTTPException: If the tenant has exceeded their rate limit.
    """
    limiter = get_rate_limiter()
    allowed = await limiter.check(tenant.tenant_id, tenant.rate_limit)

    if not allowed:
        remaining = await limiter.get_remaining(tenant.tenant_id, tenant.rate_limit)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Limit: {tenant.rate_limit}/min, remaining: {remaining}",
            headers={
                "X-RateLimit-Limit": str(tenant.rate_limit),
                "X-RateLimit-Remaining": str(remaining),
                "Retry-After": "60",
            },
        )

    return tenant
