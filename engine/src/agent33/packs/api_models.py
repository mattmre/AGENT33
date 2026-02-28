"""Pydantic models for pack API request/response payloads."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 - Pydantic needs this at runtime

from pydantic import BaseModel, Field


class PackSummary(BaseModel):
    """Compact pack representation for list endpoints."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    category: str = ""
    skills_count: int = 0
    status: str = "installed"


class PackDetail(BaseModel):
    """Full pack details for get endpoints."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = ""
    tags: list[str] = Field(default_factory=list)
    category: str = ""
    skills: list[PackSkillInfo] = Field(default_factory=list)
    loaded_skill_names: list[str] = Field(default_factory=list)
    engine_min_version: str = ""
    installed_at: datetime | None = None
    source: str = "local"
    checksum: str = ""
    status: str = "installed"


class PackSkillInfo(BaseModel):
    """Skill info within a pack detail response."""

    name: str
    path: str = ""
    description: str = ""
    required: bool = True


# Fix forward reference
PackDetail.model_rebuild()


class InstallRequest(BaseModel):
    """Request body for pack installation."""

    source_type: str = Field(
        default="local",
        description="Source type: 'local'",
    )
    path: str = Field(
        default="",
        description="Local filesystem path to pack directory",
    )
    name: str = Field(
        default="",
        description="Pack name (for marketplace, not yet supported)",
    )
    version: str = Field(
        default="",
        description="Target version (empty = latest)",
    )


class InstallResponse(BaseModel):
    """Response for install/upgrade operations."""

    success: bool
    pack_name: str
    version: str = ""
    skills_loaded: int = 0
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class EnableDisableResponse(BaseModel):
    """Response for enable/disable operations."""

    success: bool
    pack_name: str
    tenant_id: str
    action: str  # "enabled" or "disabled"


class SearchRequest(BaseModel):
    """Request parameters for pack search."""

    query: str = Field(..., min_length=1, description="Search query string")


class PackSearchResult(BaseModel):
    """Search result item."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    tags: list[str] = Field(default_factory=list)
    match_score: float = 0.0
