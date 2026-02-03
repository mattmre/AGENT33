"""Tenant service for CRUD operations."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from agent33.db.models import Tenant
from agent33.tenancy.models import (
    PUBLIC_TENANT_ID,
    TenantContext,
    TenantCreate,
    TenantResponse,
    TenantSettings,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class TenantService:
    """Service for tenant management operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with a database session.

        Args:
            session: SQLAlchemy async session for database operations.
        """
        self.session = session

    async def get_tenant(self, tenant_id: UUID) -> TenantResponse | None:
        """Retrieve a tenant by ID.

        Args:
            tenant_id: The UUID of the tenant to retrieve.

        Returns:
            TenantResponse if found, None otherwise.
        """
        stmt = select(Tenant).where(Tenant.id == str(tenant_id))
        result = await self.session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            return None

        return self._to_response(tenant)

    async def get_tenant_by_slug(self, slug: str) -> TenantResponse | None:
        """Retrieve a tenant by its slug.

        Args:
            slug: The unique slug of the tenant.

        Returns:
            TenantResponse if found, None otherwise.
        """
        stmt = select(Tenant).where(Tenant.slug == slug)
        result = await self.session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is None:
            return None

        return self._to_response(tenant)

    async def create_tenant(self, tenant: TenantCreate) -> TenantResponse:
        """Create a new tenant.

        Args:
            tenant: The tenant creation data.

        Returns:
            The created TenantResponse.
        """
        db_tenant = Tenant(
            name=tenant.name,
            slug=tenant.slug,
            is_active=True,
            settings=tenant.settings.model_dump(),
        )
        self.session.add(db_tenant)
        await self.session.flush()
        await self.session.refresh(db_tenant)

        logger.info("Created tenant: %s (slug=%s)", db_tenant.id, db_tenant.slug)
        return self._to_response(db_tenant)

    async def get_or_create_default_tenant(self) -> TenantResponse:
        """Get the default public tenant, creating it if it does not exist.

        The default tenant is used for unauthenticated requests and has
        the well-known ID 00000000-0000-0000-0000-000000000000.

        Returns:
            The default public TenantResponse.
        """
        # Check if default tenant exists
        stmt = select(Tenant).where(Tenant.id == str(PUBLIC_TENANT_ID))
        result = await self.session.execute(stmt)
        tenant = result.scalar_one_or_none()

        if tenant is not None:
            return self._to_response(tenant)

        # Create the default public tenant
        default_settings = TenantSettings(
            is_public=True,
            rate_limit=60,  # Lower rate limit for public
            max_sources=10,
            max_facts=1000,
            features=[],
        )

        db_tenant = Tenant(
            id=str(PUBLIC_TENANT_ID),
            name="Public",
            slug="public",
            is_active=True,
            settings=default_settings.model_dump(),
        )
        self.session.add(db_tenant)
        await self.session.flush()
        await self.session.refresh(db_tenant)

        logger.info("Created default public tenant: %s", db_tenant.id)
        return self._to_response(db_tenant)

    def _to_response(self, tenant: Tenant) -> TenantResponse:
        """Convert a database Tenant to a TenantResponse.

        Args:
            tenant: The SQLAlchemy Tenant model.

        Returns:
            The corresponding TenantResponse.
        """
        settings_data = tenant.settings or {}
        return TenantResponse(
            id=UUID(tenant.id),
            name=tenant.name,
            slug=tenant.slug,
            is_active=tenant.is_active,
            settings=TenantSettings(**settings_data),
            created_at=tenant.created_at,
            updated_at=tenant.updated_at,
        )

    def to_context(self, tenant: TenantResponse, scopes: list[str] | None = None) -> TenantContext:
        """Convert a TenantResponse to a TenantContext.

        Args:
            tenant: The tenant response.
            scopes: Optional list of authorized scopes.

        Returns:
            A TenantContext suitable for attaching to request state.
        """
        return TenantContext(
            tenant_id=tenant.id,
            tenant_slug=tenant.slug,
            is_public=tenant.settings.is_public,
            scopes=scopes or [],
            rate_limit=tenant.settings.rate_limit,
        )
