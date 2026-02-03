"""Multi-tenant support for AGENT-33.

This package provides:
- TenantContext: Runtime context attached to each request
- TenantMiddleware: Middleware that resolves tenant from auth headers
- TenantService: CRUD operations for tenant management
- Rate limiting: Per-tenant request rate limiting
"""

from agent33.tenancy.middleware import (
    TenantMiddleware,
    get_current_tenant,
    require_authenticated_tenant,
)
from agent33.tenancy.models import (
    PUBLIC_TENANT_ID,
    TenantContext,
    TenantCreate,
    TenantResponse,
    TenantSettings,
)
from agent33.tenancy.rate_limit import (
    RateLimiter,
    RedisRateLimiter,
    check_rate_limit,
    get_rate_limiter,
)
from agent33.tenancy.service import TenantService

__all__ = [
    # Models
    "PUBLIC_TENANT_ID",
    "TenantContext",
    "TenantCreate",
    "TenantResponse",
    "TenantSettings",
    # Service
    "TenantService",
    # Middleware
    "TenantMiddleware",
    "get_current_tenant",
    "require_authenticated_tenant",
    # Rate limiting
    "RateLimiter",
    "RedisRateLimiter",
    "check_rate_limit",
    "get_rate_limiter",
]
