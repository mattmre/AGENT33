"""JWT authentication and API key management."""

from __future__ import annotations

import hashlib
import secrets
import time
from typing import Any

import jwt
from pydantic import BaseModel

from agent33.config import settings

# ---------------------------------------------------------------------------
# Token payload model
# ---------------------------------------------------------------------------


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str
    scopes: list[str] = []
    exp: int = 0
    tenant_id: str = ""


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(
    subject: str,
    scopes: list[str] | None = None,
    tenant_id: str = "",
) -> str:
    """Create a signed JWT for *subject* with the given *scopes*."""
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": subject,
        "scopes": scopes or [],
        "iat": now,
        "exp": now + settings.jwt_expire_minutes * 60,
    }
    if tenant_id:
        payload["tenant_id"] = tenant_id
    return jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )


def verify_token(token: str) -> TokenPayload:
    """Decode and validate a JWT, returning a :class:`TokenPayload`.

    Raises ``jwt.InvalidTokenError`` on failure.
    """
    data = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
    )
    return TokenPayload(**data)


# ---------------------------------------------------------------------------
# API key management (in-memory)
# ---------------------------------------------------------------------------

# Mapping from key-hash -> {"key_id": str, "subject": str, "scopes": [...], ...}
_api_keys: dict[str, dict[str, Any]] = {}


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key(
    subject: str,
    scopes: list[str] | None = None,
    tenant_id: str = "",
    expires_in_seconds: int | None = None,
) -> dict[str, Any]:
    """Generate a new API key and return its metadata including the raw key.

    Returns ``{"key_id": ..., "key": ..., "subject": ..., "scopes": [...], ...}``.
    The raw ``key`` is only available at creation time.

    If *expires_in_seconds* is provided, the key will be rejected after that
    duration.  ``None`` means the key never expires.
    """
    raw_key = f"a33_{secrets.token_urlsafe(32)}"
    key_id = secrets.token_hex(8)
    hashed = _hash_key(raw_key)
    created_at = int(time.time())
    expires_at = (created_at + expires_in_seconds) if expires_in_seconds else 0
    _api_keys[hashed] = {
        "key_id": key_id,
        "subject": subject,
        "scopes": scopes or [],
        "tenant_id": tenant_id,
        "created_at": created_at,
        "expires_at": expires_at,
    }
    return {
        "key_id": key_id,
        "key": raw_key,
        "subject": subject,
        "scopes": scopes or [],
        "tenant_id": tenant_id,
        "expires_at": expires_at,
    }


def validate_api_key(key: str) -> TokenPayload | None:
    """Validate an API key and return a :class:`TokenPayload`, or ``None``."""
    hashed = _hash_key(key)
    entry = _api_keys.get(hashed)
    if entry is None:
        return None
    # Check expiration
    expires_at = entry.get("expires_at", 0)
    if expires_at and int(time.time()) > expires_at:
        # Key has expired — remove it and reject
        del _api_keys[hashed]
        return None
    return TokenPayload(
        sub=entry["subject"],
        scopes=entry["scopes"],
        exp=expires_at,
        tenant_id=entry.get("tenant_id", ""),
    )


def revoke_api_key(key_id: str, requesting_subject: str | None = None) -> bool:
    """Revoke an API key by its *key_id*.  Returns ``True`` if found.

    If *requesting_subject* is provided, only allow revocation if the key
    belongs to that subject or if requesting_subject is None (admin bypass).
    """
    for h, entry in list(_api_keys.items()):
        if entry["key_id"] == key_id:
            if requesting_subject is not None and entry["subject"] != requesting_subject:
                return False  # not owned by requester
            del _api_keys[h]
            return True
    return False
