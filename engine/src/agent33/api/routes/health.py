"""Health check endpoints."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter

from agent33.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, Any]:
    """Aggregate health check for all services."""
    checks: dict[str, str] = {}

    # Ollama
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/version")
            checks["ollama"] = "ok" if r.status_code == 200 else "degraded"
    except Exception:
        checks["ollama"] = "unavailable"

    # Redis
    try:
        import redis.asyncio as aioredis

        r_client = aioredis.from_url(settings.redis_url)
        await r_client.ping()
        await r_client.aclose()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    # PostgreSQL
    try:
        import asyncpg

        conn = await asyncpg.connect(
            settings.database_url.replace("+asyncpg", "").replace(
                "postgresql", "postgres"
            )
        )
        await conn.execute("SELECT 1")
        await conn.close()
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "unavailable"

    # NATS
    try:
        import nats

        nc = await nats.connect(settings.nats_url)
        await nc.close()
        checks["nats"] = "ok"
    except Exception:
        checks["nats"] = "unavailable"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "healthy" if all_ok else "degraded", "services": checks}
