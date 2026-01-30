"""Scope-based permission system."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status

# ---------------------------------------------------------------------------
# Defined scopes
# ---------------------------------------------------------------------------

SCOPES: set[str] = {
    "admin",
    "agents:read",
    "agents:write",
    "agents:invoke",
    "workflows:read",
    "workflows:write",
    "workflows:execute",
    "tools:execute",
}


def check_permission(required_scope: str, token_scopes: list[str]) -> bool:
    """Return ``True`` if *token_scopes* satisfy *required_scope*.

    The ``admin`` scope implicitly grants all permissions.
    """
    if "admin" in token_scopes:
        return True
    return required_scope in token_scopes


def _get_token_payload(request: Request):
    """Extract token payload previously set by auth middleware."""
    payload = getattr(request.state, "user", None)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return payload


def require_scope(scope: str):
    """FastAPI dependency that enforces *scope* on the current request.

    Usage::

        @router.get("/agents", dependencies=[Depends(require_scope("agents:read"))])
        async def list_agents(): ...
    """

    async def _checker(request: Request):
        payload = _get_token_payload(request)
        if not check_permission(scope, payload.scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
            )
        return payload

    return Depends(_checker)
