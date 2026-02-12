"""JWT authentication and API key management."""

from __future__ import annotations

import hashlib
import secrets
import time

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


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def create_access_token(subject: str, scopes: list[str] | None = None) -> str:
    """Create a signed JWT for *subject* with the given *scopes*."""
    now = int(time.time())
    payload = {
        "sub": subject,
        "scopes": scopes or [],
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
# API key management (in-memory)
# ---------------------------------------------------------------------------

# Mapping from key-hash -> {"key_id": str, "subject": str, "scopes": [...]}
_api_keys: dict[str, dict] = {}


def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key(subject: str, scopes: list[str] | None = None) -> dict:
    """Generate a new API key and return its metadata including the raw key.

    Returns ``{"key_id": ..., "key": ..., "subject": ..., "scopes": [...]}``.
    The raw ``key`` is only available at creation time.
    """
    raw_key = f"a33_{secrets.token_urlsafe(32)}"
    key_id = secrets.token_hex(8)
    hashed = _hash_key(raw_key)
    _api_keys[hashed] = {
        "key_id": key_id,
        "subject": subject,
        "scopes": scopes or [],
    }
    return {"key_id": key_id, "key": raw_key, "subject": subject, "scopes": scopes or []}


def validate_api_key(key: str) -> TokenPayload | None:
    """Validate an API key and return a :class:`TokenPayload`, or ``None``."""
    hashed = _hash_key(key)
    entry = _api_keys.get(hashed)
    if entry is None:
        return None
    return TokenPayload(
        sub=entry["subject"],
        scopes=entry["scopes"],
        exp=0,
    )


def revoke_api_key(key_id: str) -> bool:
    """Revoke an API key by its *key_id*.  Returns ``True`` if found."""
    for h, entry in list(_api_keys.items()):
        if entry["key_id"] == key_id:
            del _api_keys[h]
            return True
    return False
