"""Scope-based permission system with deny-first evaluation."""

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


def check_permission(
    required_scope: str,
    token_scopes: list[str],
    deny_scopes: list[str] | None = None,
) -> bool:
    """Return ``True`` if *token_scopes* satisfy *required_scope*.

    Evaluation order (deny-first):
    1. If the required scope is in *deny_scopes*, **deny** immediately.
    2. The ``admin`` scope implicitly grants all permissions (unless denied).
    3. Otherwise, check if *required_scope* is in *token_scopes*.
    """
    if deny_scopes and required_scope in deny_scopes:
        return False
    if "admin" in token_scopes:
        return not (deny_scopes and "admin" in deny_scopes)
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
