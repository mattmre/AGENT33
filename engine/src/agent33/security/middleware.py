"""FastAPI authentication middleware."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from agent33.security.auth import validate_api_key, verify_token

if TYPE_CHECKING:
    from starlette.requests import Request

logger = logging.getLogger(__name__)

_PUBLIC_PATHS: set[str] = {"/health", "/docs", "/redoc", "/openapi.json"}


class AuthMiddleware(BaseHTTPMiddleware):
    """Enforce authentication on every request except public paths.

    Supports two schemes:

    * ``Authorization: Bearer <jwt>``
    * ``X-API-Key: <key>``

    On success the decoded :class:`~agent33.security.auth.TokenPayload` is
    attached to ``request.state.user``.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Allow public endpoints through without auth
        if (
            path in _PUBLIC_PATHS
            or path == "/docs"
            or path.startswith("/docs/")
            or path == "/redoc"
            or path.startswith("/redoc/")
        ):
            return await call_next(request)

        # Try Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = verify_token(token)
            except Exception:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"},
                )
            request.state.user = payload
            return await call_next(request)

        # Try API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            api_payload = validate_api_key(api_key)
            if api_payload is not None:
                request.state.user = api_payload
                return await call_next(request)
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})

        return JSONResponse(
            status_code=401,
            content={"detail": "Missing authentication credentials"},
        )
