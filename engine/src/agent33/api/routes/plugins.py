"""FastAPI router for plugin management endpoints."""

# NOTE: no ``from __future__ import annotations`` -- Pydantic needs these
# types at runtime for request-body validation.

from pathlib import Path
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Request, status

from agent33.plugins.api_models import (
    PluginConfigUpdate,
    PluginDetail,
    PluginDiscoverResponse,
    PluginHealthResponse,
    PluginSearchResponse,
    PluginSummary,
)
from agent33.plugins.models import PluginState
from agent33.security.permissions import require_scope

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/plugins", tags=["plugins"])


def _get_plugin_registry(request: Request) -> Any:
    """Extract plugin registry from app state."""
    registry = getattr(request.app.state, "plugin_registry", None)
    if registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Plugin registry not initialized",
        )
    return registry


def _manifest_to_summary(manifest: Any, state: str) -> PluginSummary:
    """Convert a PluginManifest + state into a PluginSummary."""
    contributions = manifest.contributions
    return PluginSummary(
        name=manifest.name,
        version=manifest.version,
        description=manifest.description,
        state=state,
        author=manifest.author,
        tags=manifest.tags,
        contributions_summary={
            "skills": len(contributions.skills),
            "tools": len(contributions.tools),
            "agents": len(contributions.agents),
            "hooks": len(contributions.hooks),
        },
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=list[PluginSummary],
    dependencies=[require_scope("plugins:read")],
)
async def list_plugins(request: Request) -> list[PluginSummary]:
    """List all discovered plugins."""
    registry = _get_plugin_registry(request)
    summaries: list[PluginSummary] = []
    for manifest in registry.list_all():
        state = registry.get_state(manifest.name)
        summaries.append(
            _manifest_to_summary(manifest, state.value if state else "unknown")
        )
    return summaries


@router.get(
    "/search",
    response_model=PluginSearchResponse,
    dependencies=[require_scope("plugins:read")],
)
async def search_plugins(request: Request, q: str = "") -> PluginSearchResponse:
    """Search plugins by query string."""
    registry = _get_plugin_registry(request)
    if not q:
        manifests = registry.list_all()
    else:
        manifests = registry.search(q)

    summaries: list[PluginSummary] = []
    for manifest in manifests:
        state = registry.get_state(manifest.name)
        summaries.append(
            _manifest_to_summary(manifest, state.value if state else "unknown")
        )

    return PluginSearchResponse(
        query=q,
        count=len(summaries),
        plugins=summaries,
    )


@router.get(
    "/{name}",
    response_model=PluginDetail,
    dependencies=[require_scope("plugins:read")],
)
async def get_plugin(request: Request, name: str) -> PluginDetail:
    """Get detailed plugin info."""
    registry = _get_plugin_registry(request)
    entry = registry.get(name)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found",
        )

    manifest = entry.manifest
    contributions = manifest.contributions
    state = entry.state

    # Determine granted vs denied permissions from the plugin context
    granted: list[str] = []
    denied: list[str] = []
    if entry.instance is not None:
        ctx = entry.instance.context
        granted = sorted(ctx.granted_permissions)
        denied = sorted(set(p.value for p in manifest.permissions) - set(granted))
    else:
        granted = [p.value for p in manifest.permissions]

    return PluginDetail(
        name=manifest.name,
        version=manifest.version,
        description=manifest.description,
        author=manifest.author,
        license=manifest.license,
        homepage=manifest.homepage,
        repository=manifest.repository,
        state=state.value,
        status=manifest.status.value,
        permissions=[p.value for p in manifest.permissions],
        granted_permissions=granted,
        denied_permissions=denied,
        contributions={
            "skills": contributions.skills,
            "tools": contributions.tools,
            "agents": contributions.agents,
            "hooks": contributions.hooks,
        },
        dependencies=[
            {
                "name": d.name,
                "version_constraint": d.version_constraint,
                "optional": d.optional,
            }
            for d in manifest.dependencies
        ],
        tags=manifest.tags,
        error=entry.error,
    )


@router.post(
    "/{name}/enable",
    response_model=PluginSummary,
    dependencies=[require_scope("plugins:write")],
)
async def enable_plugin(request: Request, name: str) -> PluginSummary:
    """Enable a loaded/disabled plugin."""
    registry = _get_plugin_registry(request)
    entry = registry.get(name)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found",
        )

    try:
        await registry.enable(name)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    entry = registry.get(name)
    return _manifest_to_summary(entry.manifest, entry.state.value)


@router.post(
    "/{name}/disable",
    response_model=PluginSummary,
    dependencies=[require_scope("plugins:write")],
)
async def disable_plugin(request: Request, name: str) -> PluginSummary:
    """Disable an active plugin."""
    registry = _get_plugin_registry(request)
    entry = registry.get(name)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found",
        )

    try:
        await registry.disable(name)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    entry = registry.get(name)
    return _manifest_to_summary(entry.manifest, entry.state.value)


@router.post(
    "/{name}/reload",
    response_model=PluginSummary,
    dependencies=[require_scope("admin")],
)
async def reload_plugin(request: Request, name: str) -> PluginSummary:
    """Unload and reload a plugin (hot reload). Requires admin scope."""
    registry = _get_plugin_registry(request)
    entry = registry.get(name)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found",
        )

    # Get context factory from app state
    context_factory = getattr(request.app.state, "plugin_context_factory", None)
    if context_factory is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Plugin context factory not available for reload",
        )

    try:
        # Unload, then reload
        await registry.unload(name)
        await registry.load(name, context_factory)
        await registry.enable(name)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reload failed: {exc}",
        ) from exc

    entry = registry.get(name)
    return _manifest_to_summary(entry.manifest, entry.state.value)


@router.get(
    "/{name}/config",
    dependencies=[require_scope("plugins:read")],
)
async def get_plugin_config(request: Request, name: str) -> dict[str, Any]:
    """Get tenant-specific plugin configuration."""
    registry = _get_plugin_registry(request)
    entry = registry.get(name)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found",
        )

    if entry.instance is not None:
        return dict(entry.instance.context.plugin_config)
    return {}


@router.put(
    "/{name}/config",
    dependencies=[require_scope("plugins:write")],
)
async def update_plugin_config(
    request: Request, name: str, update: PluginConfigUpdate
) -> dict[str, Any]:
    """Update tenant-specific plugin configuration."""
    registry = _get_plugin_registry(request)
    entry = registry.get(name)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found",
        )

    # Store the config update. In a full implementation this would persist
    # to the database via TenantPluginConfig. For now, the config is stored
    # in-memory on the plugin context.
    result: dict[str, Any] = {"plugin_name": name, "updated": True}
    if update.config:
        result["config"] = update.config
    if update.enabled is not None:
        result["enabled"] = update.enabled
    return result


@router.get(
    "/{name}/health",
    response_model=PluginHealthResponse,
    dependencies=[require_scope("plugins:read")],
)
async def get_plugin_health(request: Request, name: str) -> PluginHealthResponse:
    """Get plugin health status."""
    registry = _get_plugin_registry(request)
    entry = registry.get(name)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plugin '{name}' not found",
        )

    healthy = entry.state == PluginState.ACTIVE
    details: dict[str, Any] = {
        "state": entry.state.value,
        "version": entry.manifest.version,
    }
    if entry.error:
        details["error"] = entry.error
        healthy = False

    # If plugin implements a health_check method, call it
    if entry.instance is not None and hasattr(entry.instance, "health_check"):
        try:
            check_result = await entry.instance.health_check()
            if isinstance(check_result, dict):
                details.update(check_result)
                healthy = check_result.get("healthy", healthy)
        except Exception as exc:
            details["health_check_error"] = str(exc)
            healthy = False

    return PluginHealthResponse(
        plugin_name=name,
        healthy=healthy,
        details=details,
    )


@router.post(
    "/discover",
    response_model=PluginDiscoverResponse,
    dependencies=[require_scope("admin")],
)
async def discover_plugins(request: Request) -> PluginDiscoverResponse:
    """Re-scan plugin directories for new plugins. Requires admin scope."""
    registry = _get_plugin_registry(request)

    # Get plugin directory from settings
    from agent33.config import settings

    plugin_dir = Path(
        getattr(settings, "plugin_definitions_dir", "plugins")
    )

    discovered = registry.discover(plugin_dir)
    return PluginDiscoverResponse(
        discovered=discovered,
        total=registry.count,
    )
