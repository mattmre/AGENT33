"""FastAPI middleware for multi-tenant request handling."""

from __future__ import annotations

import logging

from fastapi import Depends, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from agent33.db.session import get_session_factory
from agent33.security.auth import validate_api_key, validate_api_key_async, verify_token
from agent33.tenancy.models import PUBLIC_TENANT_ID, TenantContext
from agent33.tenancy.service import TenantService

logger = logging.getLogger(__name__)

# Paths that skip tenant resolution entirely
_SKIP_PATHS: set[str] = {"/health", "/docs", "/redoc", "/openapi.json"}


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware that resolves tenant context for each request.

    Authentication is extracted from:
    - X-API-Key header
    - Authorization: Bearer <token> header

    If no authentication is provided, the request is assigned to the
    default public tenant with limited permissions.

    The resolved TenantContext is attached to request.state.tenant.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and resolve tenant context."""
        path = request.url.path

        # Skip tenant resolution for public paths
        if path in _SKIP_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Extract authentication credentials
        api_key = request.headers.get("X-API-Key")
        auth_header = request.headers.get("Authorization", "")
        bearer_token = None
        if auth_header.startswith("Bearer "):
            bearer_token = auth_header[7:]

        tenant_context: TenantContext | None = None
        scopes: list[str] = []
        tenant_id: str | None = None

        # Try API key first
        if api_key:
            # Try in-memory cache first
            payload = validate_api_key(api_key)
            if payload is not None:
                tenant_id = payload.tenant_id
                scopes = payload.scopes
            else:
                # Fall back to database lookup
                session_factory = get_session_factory()
                async with session_factory() as session:
                    payload = await validate_api_key_async(session, api_key)
                    if payload is not None:
                        tenant_id = payload.tenant_id
                        scopes = payload.scopes
                        await session.commit()

        # Try Bearer token
        elif bearer_token:
            try:
                payload = verify_token(bearer_token)
                tenant_id = payload.tenant_id
                scopes = payload.scopes
            except Exception:
                # Invalid token - fall through to public tenant
                logger.debug("Invalid bearer token, using public tenant")

        # Resolve tenant from ID or fall back to public
        session_factory = get_session_factory()
        async with session_factory() as session:
            service = TenantService(session)

            if tenant_id:
                try:
                    from uuid import UUID
                    tenant = await service.get_tenant(UUID(tenant_id))
                    if tenant and tenant.is_active:
                        tenant_context = service.to_context(tenant, scopes)
                except (ValueError, TypeError):
                    logger.warning("Invalid tenant_id in token: %s", tenant_id)

            # Fall back to public tenant
            if tenant_context is None:
                default_tenant = await service.get_or_create_default_tenant()
                tenant_context = service.to_context(default_tenant, scopes=[])

            await session.commit()

        # Attach tenant context to request
        request.state.tenant = tenant_context

        return await call_next(request)


async def get_current_tenant(request: Request) -> TenantContext:
    """FastAPI dependency to get the current tenant context.

    Usage:
        @app.get("/items")
        async def list_items(tenant: TenantContext = Depends(get_current_tenant)):
            ...

    Returns:
        The TenantContext for the current request.

    Raises:
        HTTPException: If no tenant context is available (middleware not configured).
    """
    tenant: TenantContext | None = getattr(request.state, "tenant", None)
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant context not available. Is TenantMiddleware configured?",
        )
    return tenant


async def require_authenticated_tenant(
    tenant: TenantContext = Depends(get_current_tenant),
) -> TenantContext:
    """FastAPI dependency that requires a non-public tenant.

    Usage:
        @app.post("/admin/action")
        async def admin_action(tenant: TenantContext = Depends(require_authenticated_tenant)):
            ...

    Returns:
        The TenantContext for authenticated requests.

    Raises:
        HTTPException: If the request is using the public tenant.
    """
    if tenant.is_public or tenant.tenant_id == PUBLIC_TENANT_ID:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return tenant
