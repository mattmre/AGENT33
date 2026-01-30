"""Authentication API routes."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from agent33.security.auth import (
    create_access_token,
    generate_api_key,
    revoke_api_key,
    verify_token,
)

router = APIRouter(prefix="/v1/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# In-memory user store (replace with a real DB in production)
# ---------------------------------------------------------------------------

_users: dict[str, dict[str, Any]] = {
    "admin": {
        "password_hash": hashlib.sha256(b"admin").hexdigest(),
        "scopes": ["admin"],
    },
}

# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ApiKeyRequest(BaseModel):
    subject: str
    scopes: list[str] = []


class ApiKeyResponse(BaseModel):
    key_id: str
    key: str
    subject: str
    scopes: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/token", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Authenticate with username/password and receive a JWT."""
    user = _users.get(body.username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    password_hash = hashlib.sha256(body.password.encode()).hexdigest()
    if password_hash != user["password_hash"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=body.username, scopes=user["scopes"])
    return TokenResponse(access_token=token)


@router.post("/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(body: ApiKeyRequest) -> ApiKeyResponse:
    """Generate a new API key."""
    result = generate_api_key(subject=body.subject, scopes=body.scopes)
    return ApiKeyResponse(**result)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(key_id: str) -> None:
    """Revoke an API key by its identifier."""
    found = revoke_api_key(key_id)
    if not found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
