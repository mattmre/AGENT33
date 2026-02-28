"""API response and request Pydantic models for plugin endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PluginSummary(BaseModel):
    """Compact plugin info for list responses."""

    name: str
    version: str
    description: str
    state: str
    author: str
    tags: list[str]
    contributions_summary: dict[str, int] = Field(
        default_factory=dict,
        description='Counts per contribution type, e.g. {"skills": 2, "tools": 1}.',
    )


class PluginDetail(BaseModel):
    """Full plugin info for detail responses."""

    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: str
    repository: str
    state: str
    status: str
    permissions: list[str]
    granted_permissions: list[str]
    denied_permissions: list[str]
    contributions: dict[str, list[str]]
    dependencies: list[dict[str, Any]]
    tags: list[str]
    tenant_config: dict[str, Any] | None = None
    error: str | None = None


class PluginConfigUpdate(BaseModel):
    """Request body for plugin config updates."""

    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool | None = None
    permission_overrides: dict[str, bool] | None = None


class PluginHealthResponse(BaseModel):
    """Health check result for a plugin."""

    plugin_name: str
    healthy: bool
    details: dict[str, Any] = Field(default_factory=dict)


class PluginSearchResponse(BaseModel):
    """Search results wrapper."""

    query: str
    count: int
    plugins: list[PluginSummary]


class PluginDiscoverResponse(BaseModel):
    """Response from discovery scan."""

    discovered: int
    total: int
