"""Health check endpoints."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Request

from agent33.config import settings

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


def _get_adapters() -> dict[str, Any]:
    """Import the adapter registry lazily to avoid circular imports."""
    from agent33.api.routes.webhooks import _adapters

    return _adapters


@router.get("/health")
async def health(request: Request = None) -> dict[str, Any]:  # type: ignore[assignment]
    """Aggregate health check for all services."""
    checks: dict[str, str] = {}
    include_external_checks = request is not None

    if include_external_checks:
        # Route requests get the full dependency probe set. Direct test calls
        # without a Request object only exercise channel aggregation.
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{settings.ollama_base_url}/api/version")
                checks["ollama"] = "ok" if r.status_code == 200 else "degraded"
        except Exception:
            checks["ollama"] = "unavailable"

        # Redis
        try:
            import redis.asyncio as aioredis

            r_client = aioredis.from_url(settings.redis_url)  # type: ignore[no-untyped-call]
            await r_client.ping()
            await r_client.aclose()
            checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "unavailable"

        # PostgreSQL
        try:
            import asyncpg

            conn = await asyncpg.connect(
                settings.database_url.replace("+asyncpg", "").replace("postgresql", "postgres")
            )
            await conn.execute("SELECT 1")
            await conn.close()
            checks["postgres"] = "ok"
        except Exception:
            checks["postgres"] = "unavailable"

        # External Integrations
        if settings.openai_api_key.get_secret_value():
            try:
                async with httpx.AsyncClient(timeout=3) as client:
                    r = await client.get(
                        "https://api.openai.com/v1/models",
                        headers={
                            "Authorization": f"Bearer {settings.openai_api_key.get_secret_value()}"
                        },
                    )
                    checks["openai"] = "ok" if r.status_code == 200 else "degraded"
            except Exception:
                checks["openai"] = "unavailable"
        else:
            checks["openai"] = "unconfigured"

        if settings.elevenlabs_api_key.get_secret_value():
            try:
                async with httpx.AsyncClient(timeout=3) as client:
                    r = await client.get(
                        "https://api.elevenlabs.io/v1/models",
                        headers={"xi-api-key": settings.elevenlabs_api_key.get_secret_value()},
                    )
                    checks["elevenlabs"] = "ok" if r.status_code == 200 else "degraded"
            except Exception:
                checks["elevenlabs"] = "unavailable"
        else:
            checks["elevenlabs"] = "unconfigured"

        if settings.jina_api_key.get_secret_value():
            # Jina reader uses a simple ping since /models isn't universally standard
            checks["jina"] = "configured"
        else:
            checks["jina"] = "unconfigured"

        # NATS
        try:
            import nats

            nc = await nats.connect(settings.nats_url)
            await nc.close()
            checks["nats"] = "ok"
        except Exception:
            checks["nats"] = "unavailable"

    # Messaging channels
    adapters = _get_adapters()
    for platform, adapter in adapters.items():
        try:
            result = await adapter.health_check()
            checks[f"channel:{platform}"] = result.status
        except Exception:
            checks[f"channel:{platform}"] = "unavailable"

    app_state = request.app.state if request is not None else None

    voice_probe = getattr(app_state, "voice_sidecar_probe", None)
    if voice_probe is not None:
        voice_snapshot = await voice_probe.health_snapshot()
        checks["voice_sidecar"] = str(voice_snapshot.get("status", "unavailable"))
    else:
        checks["voice_sidecar"] = "unconfigured"

    status_line_service = getattr(app_state, "status_line_service", None)
    if status_line_service is not None:
        status_line_snapshot = await status_line_service.health_snapshot()
        checks["status_line"] = str(status_line_snapshot.get("status", "unavailable"))
    else:
        checks["status_line"] = "unconfigured"

    all_ok = all(v == "ok" for v in checks.values())
    result: dict[str, Any] = {"status": "healthy" if all_ok else "degraded", "services": checks}

    # Attach runtime version info if available
    runtime_info = getattr(app_state, "runtime_version_info", None)
    if runtime_info is not None:
        result["runtime_version"] = runtime_info.version
        result["git_short_hash"] = runtime_info.git_short_hash

    return result


@router.get("/health/channels")
async def channel_health() -> dict[str, Any]:
    """Detailed health check for all registered messaging channels."""
    adapters = _get_adapters()
    results: dict[str, Any] = {}
    for platform, adapter in adapters.items():
        try:
            result = await adapter.health_check()
            results[platform] = result.model_dump()
        except Exception as exc:
            results[platform] = {
                "platform": platform,
                "status": "unavailable",
                "detail": str(exc),
            }
    return {"channels": results}
