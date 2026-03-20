"""Health check endpoints."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from fastapi import APIRouter, Request, Response

from agent33.config import settings

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


def _get_adapters() -> dict[str, Any]:
    """Import the adapter registry lazily to avoid circular imports."""
    from agent33.api.routes.webhooks import _adapters

    return _adapters


async def _core_dependency_checks() -> dict[str, str]:
    """Probe the in-cluster dependencies required for normal API operation."""
    checks: dict[str, str] = {}

    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/version")
            checks["ollama"] = "ok" if response.status_code == 200 else "degraded"
    except Exception:
        checks["ollama"] = "unavailable"

    try:
        import redis.asyncio as aioredis

        redis_client = aioredis.from_url(settings.redis_url)  # type: ignore[no-untyped-call]
        await asyncio.wait_for(redis_client.ping(), timeout=3)
        await redis_client.aclose()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"

    try:
        import asyncpg

        connection = await asyncio.wait_for(
            asyncpg.connect(
                settings.database_url.replace("+asyncpg", "").replace("postgresql", "postgres")
            ),
            timeout=3,
        )
        await asyncio.wait_for(connection.execute("SELECT 1"), timeout=3)
        await connection.close()
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "unavailable"

    try:
        import nats

        nc = await asyncio.wait_for(nats.connect(settings.nats_url), timeout=3)
        await nc.close()
        checks["nats"] = "ok"
    except Exception:
        checks["nats"] = "unavailable"

    return checks


@router.get("/health")
async def health(request: Request = None) -> dict[str, Any]:  # type: ignore[assignment]
    """Aggregate health check for all services."""
    checks: dict[str, str] = {}
    include_external_checks = request is not None

    if include_external_checks:
        # Route requests get the full dependency probe set. Direct test calls
        # without a Request object only exercise channel aggregation.
        checks.update(await _core_dependency_checks())

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

    # Connector fleet (MCP proxy + boundary connectors)
    proxy_manager = getattr(app_state, "proxy_manager", None)
    if proxy_manager is not None:
        fleet = proxy_manager.health_summary()
        fleet_total = fleet.get("total", 0)
        fleet_healthy = fleet.get("healthy", 0)
        fleet_degraded = fleet.get("degraded", 0)
        if fleet_total == 0:
            checks["connectors"] = "idle"
        elif fleet_healthy == fleet_total:
            checks["connectors"] = "ok"
        elif fleet_degraded > 0 or fleet_healthy > 0:
            checks["connectors"] = "degraded"
        else:
            checks["connectors"] = "unavailable"
    else:
        checks["connectors"] = "unconfigured"

    all_ok = all(v == "ok" for v in checks.values())
    health_result: dict[str, Any] = {
        "status": "healthy" if all_ok else "degraded",
        "services": checks,
    }

    # Attach runtime version info if available
    runtime_info = getattr(app_state, "runtime_version_info", None)
    if runtime_info is not None:
        health_result["runtime_version"] = runtime_info.version
        health_result["git_short_hash"] = runtime_info.git_short_hash

    return health_result


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Lightweight process health for liveness probes."""
    return {"status": "healthy"}


@router.get("/readyz")
async def readyz(response: Response) -> dict[str, Any]:
    """Kubernetes readiness probe for core in-cluster dependencies."""
    checks = await _core_dependency_checks()
    healthy = all(status == "ok" for status in checks.values())
    response.status_code = 200 if healthy else 503
    return {
        "status": "healthy" if healthy else "degraded",
        "services": checks,
    }


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
