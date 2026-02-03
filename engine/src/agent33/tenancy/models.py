"""Tenancy Pydantic models for multi-tenant support."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# Default public tenant UUID
PUBLIC_TENANT_ID = UUID("00000000-0000-0000-0000-000000000000")


class TenantSettings(BaseModel):
    """Tenant-specific settings and limits."""

    is_public: bool = False
    rate_limit: int = Field(default=100, description="Requests per minute")
    max_sources: int = Field(default=50, description="Maximum number of sources")
    max_facts: int = Field(default=10000, description="Maximum number of facts")
    features: list[str] = Field(
        default_factory=list,
        description="Enabled feature flags",
    )


class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=63, pattern=r"^[a-z0-9-]+$")
    settings: TenantSettings = Field(default_factory=TenantSettings)


class TenantResponse(BaseModel):
    """Schema for tenant API responses."""

    id: UUID
    name: str
    slug: str
    is_active: bool
    settings: TenantSettings
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TenantContext(BaseModel):
    """Runtime context for the current tenant.

    Attached to request.state.tenant by TenantMiddleware.
    """

    tenant_id: UUID
    tenant_slug: str
    is_public: bool = False
    scopes: list[str] = Field(default_factory=list)
    rate_limit: int = Field(default=100, description="Requests per minute")

    @property
    def is_default_tenant(self) -> bool:
        """Check if this is the default public tenant."""
        return self.tenant_id == PUBLIC_TENANT_ID
