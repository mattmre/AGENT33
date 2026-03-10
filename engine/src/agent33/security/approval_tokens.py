"""Stateless HITL approval tokens backed by short-lived JWTs."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

import jwt
from pydantic import BaseModel

from agent33.security.arg_hash import canonical_arg_hash

if TYPE_CHECKING:
    from agent33.tools.approvals import ToolApprovalRequest

logger = logging.getLogger(__name__)


class ApprovalTokenError(Exception):
    """Raised when an approval token fails validation."""


class ApprovalTokenPayload(BaseModel):
    """Decoded approval-token claims."""

    typ: str = "a33_approval"
    sub: str = ""
    jti: str = ""
    tool: str = ""
    op: str = ""
    arg_hash: str = ""
    tenant_id: str = ""
    scope: str = "tools:execute"
    one_time: bool = True
    exp: int = 0
    iat: int = 0


class ApprovalTokenManager:
    """Issue and validate stateless HITL approval tokens.

    Tokens are JWTs signed with a shared secret.  A ``typ`` claim of
    ``a33_approval`` prevents cross-use with regular auth JWTs.
    """

    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        default_ttl_seconds: int = 300,
        clock: Any | None = None,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._default_ttl_seconds = default_ttl_seconds
        self._clock = clock or time.time
        # Track consumed one-time tokens (jti -> consumed_at)
        self._consumed: dict[str, float] = {}
        # Emergency revocation set (jti -> revoked_at)
        self._revoked: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Issuance
    # ------------------------------------------------------------------

    def issue(
        self,
        approval: ToolApprovalRequest,
        arguments: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
        one_time: bool = True,
    ) -> str:
        """Issue a signed approval token for an already-approved request.

        Raises ``ApprovalTokenError`` if the approval is not in ``approved``
        status.
        """
        from agent33.tools.approvals import ApprovalStatus

        if approval.status != ApprovalStatus.APPROVED:
            raise ApprovalTokenError(
                f"Cannot issue token for approval in status={approval.status}"
            )

        now = int(self._clock())
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl_seconds
        arg_hash = canonical_arg_hash(approval.tool_name, arguments or {})

        claims: dict[str, Any] = {
            "typ": "a33_approval",
            "sub": approval.reviewed_by or approval.requested_by,
            "iss": "agent33",
            "iat": now,
            "exp": now + ttl,
            "jti": approval.approval_id,
            "tool": approval.tool_name,
            "op": approval.operation,
            "arg_hash": arg_hash,
            "tenant_id": approval.tenant_id,
            "scope": "tools:execute",
            "one_time": one_time,
        }
        return jwt.encode(claims, self._secret, algorithm=self._algorithm)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(
        self,
        token: str,
        tool_name: str,
        arguments: dict[str, Any],
        tenant_id: str = "",
    ) -> ApprovalTokenPayload:
        """Validate and optionally consume an approval token.

        Raises ``ApprovalTokenError`` on any validation failure.
        """
        self._prune_consumed()
        self._prune_revoked()

        try:
            data = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                options={"require": ["exp", "iat", "typ", "tool", "jti"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise ApprovalTokenError("Approval token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise ApprovalTokenError(f"Invalid approval token: {exc}") from exc

        # Validate type claim
        if data.get("typ") != "a33_approval":
            raise ApprovalTokenError("Token is not an approval token (wrong typ)")

        # Validate tool scope
        if data.get("tool") != tool_name:
            raise ApprovalTokenError(
                f"Token tool mismatch: expected={tool_name}, got={data.get('tool')}"
            )

        # Validate argument hash
        expected_hash = canonical_arg_hash(tool_name, arguments)
        if data.get("arg_hash") != expected_hash:
            raise ApprovalTokenError("Token argument hash mismatch (arguments were tampered)")

        # Validate tenant scope
        token_tenant = data.get("tenant_id", "")
        if tenant_id and token_tenant and token_tenant != tenant_id:
            raise ApprovalTokenError(
                f"Token tenant mismatch: expected={tenant_id}, got={token_tenant}"
            )

        jti = data.get("jti", "")

        # Check revocation
        if jti in self._revoked:
            raise ApprovalTokenError("Token has been revoked")

        # Check one-time consumption
        if data.get("one_time", True):
            if jti in self._consumed:
                raise ApprovalTokenError("One-time token has already been consumed")
            self._consumed[jti] = self._clock()

        return ApprovalTokenPayload(**data)

    # ------------------------------------------------------------------
    # Revocation
    # ------------------------------------------------------------------

    def revoke(self, jti: str) -> bool:
        """Add a token JTI to the revocation set."""
        if jti in self._revoked:
            return False
        self._revoked[jti] = self._clock()
        return True

    def is_revoked(self, jti: str) -> bool:
        """Check if a JTI has been revoked."""
        return jti in self._revoked

    # ------------------------------------------------------------------
    # Pruning
    # ------------------------------------------------------------------

    def _prune_consumed(self) -> None:
        """Remove consumed entries older than 2x default TTL."""
        cutoff = self._clock() - (2 * self._default_ttl_seconds)
        self._consumed = {jti: ts for jti, ts in self._consumed.items() if ts > cutoff}

    def _prune_revoked(self) -> None:
        """Remove revoked entries older than 2x default TTL."""
        cutoff = self._clock() - (2 * self._default_ttl_seconds)
        self._revoked = {jti: ts for jti, ts in self._revoked.items() if ts > cutoff}
