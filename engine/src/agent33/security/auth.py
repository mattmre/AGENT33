"""JWT authentication and API key management.

Supports both in-memory (for testing) and database-backed API key storage.
"""

from __future__ import annotations

import hashlib
import secrets
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import jwt
from pydantic import BaseModel

from agent33.config import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# ---------------------------------------------------------------------------
# Token payload model
# ---------------------------------------------------------------------------


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    tenant_id: str | None = None
    scopes: list[str] = []
    exp: int = 0


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(
    subject: str,
    scopes: list[str] | None = None,
    tenant_id: str | None = None,
) -> str:
    """Create a signed JWT for *subject* with the given *scopes*."""
    now = int(time.time())
    payload = {
        "sub": subject,
        "scopes": scopes or [],
        "tenant_id": tenant_id,
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> TokenPayload:
    """Decode and validate a JWT, returning a :class:`TokenPayload`.

    Raises ``jwt.InvalidTokenError`` on failure.
    """
    data = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return TokenPayload(**data)


# ---------------------------------------------------------------------------
# API key management (hybrid: in-memory cache + database persistence)
# ---------------------------------------------------------------------------

# In-memory cache for fast lookups
# Mapping from key-hash -> {"key_id": str, "subject": str, "scopes": [...], "tenant_id": str}
_api_keys_cache: dict[str, dict] = {}


def _hash_key(key: str) -> str:
    """Hash an API key using SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key(
    subject: str,
    scopes: list[str] | None = None,
    tenant_id: str | None = None,
    name: str | None = None,
) -> dict:
    """Generate a new API key and return its metadata including the raw key.

    Returns ``{"key_id": ..., "key": ..., "subject": ..., "scopes": [...], "tenant_id": ...}``.
    The raw ``key`` is only available at creation time.

    Note: This adds to the in-memory cache. For persistence, use
    :func:`generate_api_key_async` which stores to the database.
    """
    raw_key = f"a33_{secrets.token_urlsafe(32)}"
    key_id = secrets.token_hex(8)
    hashed = _hash_key(raw_key)

    entry = {
        "key_id": key_id,
        "subject": subject,
        "scopes": scopes or [],
        "tenant_id": tenant_id,
        "name": name or f"api_key_{key_id}",
    }
    _api_keys_cache[hashed] = entry

    return {
        "key_id": key_id,
        "key": raw_key,
        "subject": subject,
        "scopes": scopes or [],
        "tenant_id": tenant_id,
    }


async def generate_api_key_async(
    session: AsyncSession,
    tenant_id: str,
    subject: str,
    name: str,
    scopes: list[str] | None = None,
) -> dict:
    """Generate and persist a new API key to the database.

    Returns ``{"key_id": ..., "key": ..., "subject": ..., "scopes": [...], "tenant_id": ...}``.
    The raw ``key`` is only available at creation time.
    """
    from agent33.db.models import ApiKey

    raw_key = f"a33_{secrets.token_urlsafe(32)}"
    key_id = secrets.token_hex(8)
    key_hash = _hash_key(raw_key)

    api_key = ApiKey(
        tenant_id=tenant_id,
        key_id=key_id,
        key_hash=key_hash,
        name=name,
        scopes=scopes or [],
        is_active=True,
    )
    session.add(api_key)
    await session.flush()

    # Add to cache
    _api_keys_cache[key_hash] = {
        "key_id": key_id,
        "subject": subject,
        "scopes": scopes or [],
        "tenant_id": tenant_id,
        "name": name,
        "db_id": api_key.id,
    }

    return {
        "key_id": key_id,
        "key": raw_key,
        "subject": subject,
        "scopes": scopes or [],
        "tenant_id": tenant_id,
    }


def validate_api_key(key: str) -> TokenPayload | None:
    """Validate an API key from cache and return a :class:`TokenPayload`, or ``None``.

    For database validation, use :func:`validate_api_key_async`.
    """
    hashed = _hash_key(key)
    entry = _api_keys_cache.get(hashed)
    if entry is None:
        return None
    return TokenPayload(
        sub=entry["subject"],
        scopes=entry["scopes"],
        tenant_id=entry.get("tenant_id"),
        exp=0,
    )


async def validate_api_key_async(
    session: AsyncSession,
    key: str,
) -> TokenPayload | None:
    """Validate an API key against the database.

    Checks cache first, then falls back to database lookup.
    Updates cache on successful database lookup.
    """
    from sqlalchemy import select

    from agent33.db.models import ApiKey

    key_hash = _hash_key(key)

    # Check cache first
    if key_hash in _api_keys_cache:
        entry = _api_keys_cache[key_hash]
        return TokenPayload(
            sub=entry.get("subject", "api_user"),
            scopes=entry["scopes"],
            tenant_id=entry.get("tenant_id"),
            exp=0,
        )

    # Fall back to database
    stmt = select(ApiKey).where(
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True,  # noqa: E712
    )
    result = await session.execute(stmt)
    api_key = result.scalar_one_or_none()

    if api_key is None:
        return None

    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
        return None

    # Update last used timestamp
    api_key.last_used_at = datetime.now(UTC)

    # Cache the result
    _api_keys_cache[key_hash] = {
        "key_id": api_key.key_id,
        "subject": "api_user",
        "scopes": api_key.scopes or [],
        "tenant_id": api_key.tenant_id,
        "name": api_key.name,
        "db_id": api_key.id,
    }

    return TokenPayload(
        sub="api_user",
        scopes=api_key.scopes or [],
        tenant_id=api_key.tenant_id,
        exp=0,
    )


def revoke_api_key(key_id: str) -> bool:
    """Revoke an API key by its *key_id* from cache. Returns ``True`` if found.

    For database revocation, use :func:`revoke_api_key_async`.
    """
    for h, entry in list(_api_keys_cache.items()):
        if entry["key_id"] == key_id:
            del _api_keys_cache[h]
            return True
    return False


async def revoke_api_key_async(
    session: AsyncSession,
    key_id: str,
    tenant_id: str,
) -> bool:
    """Revoke an API key by its *key_id* in the database.

    Returns ``True`` if the key was found and revoked.
    """
    from sqlalchemy import select

    from agent33.db.models import ApiKey

    stmt = select(ApiKey).where(
        ApiKey.key_id == key_id,
        ApiKey.tenant_id == tenant_id,
    )
    result = await session.execute(stmt)
    api_key = result.scalar_one_or_none()

    if api_key is None:
        return False

    # Deactivate the key
    api_key.is_active = False

    # Remove from cache
    for h, entry in list(_api_keys_cache.items()):
        if entry["key_id"] == key_id:
            del _api_keys_cache[h]
            break

    return True


async def load_api_keys_to_cache(session: AsyncSession) -> int:
    """Load all active API keys from database into cache.

    Call this on startup to warm the cache.
    Returns the number of keys loaded.
    """
    from sqlalchemy import select

    from agent33.db.models import ApiKey

    stmt = select(ApiKey).where(ApiKey.is_active == True)  # noqa: E712
    result = await session.execute(stmt)
    api_keys = result.scalars().all()

    for api_key in api_keys:
        # Skip expired keys
        if api_key.expires_at and api_key.expires_at < datetime.now(UTC):
            continue

        _api_keys_cache[api_key.key_hash] = {
            "key_id": api_key.key_id,
            "subject": "api_user",
            "scopes": api_key.scopes or [],
            "tenant_id": api_key.tenant_id,
            "name": api_key.name,
            "db_id": api_key.id,
        }

    return len(api_keys)


def clear_api_key_cache() -> None:
    """Clear the API key cache. Useful for testing."""
    _api_keys_cache.clear()
