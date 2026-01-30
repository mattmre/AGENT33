"""Pairing code manager for linking platform users to AGENT-33 accounts."""

from __future__ import annotations

import asyncio
import logging
import secrets
from datetime import datetime, timedelta, timezone

from agent33.messaging.models import PairingRequest

logger = logging.getLogger(__name__)

_TTL_MINUTES = 15


class PairingManager:
    """Generate and verify six-digit pairing codes with automatic expiry."""

    def __init__(self) -> None:
        self._codes: dict[str, PairingRequest] = {}
        self._cleanup_task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        """Begin periodic cleanup of expired codes."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    def generate_code(self, platform: str, user_id: str) -> str:
        """Create a six-digit pairing code with a 15-minute TTL.

        If the user already has an active code it is replaced.
        """
        code = f"{secrets.randbelow(1_000_000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=_TTL_MINUTES)
        self._codes[code] = PairingRequest(
            platform=platform,
            user_id=user_id,
            code=code,
            expires_at=expires_at,
        )
        logger.info(
            "Pairing code generated for %s/%s (expires %s)",
            platform,
            user_id,
            expires_at.isoformat(),
        )
        return code

    def verify_code(self, code: str, user_id: str) -> bool:
        """Verify and consume a pairing code.

        Returns ``True`` if the code is valid, not expired, and matches the
        user.  A consumed code is removed immediately.
        """
        request = self._codes.get(code)
        if request is None:
            return False
        if datetime.now(timezone.utc) > request.expires_at:
            del self._codes[code]
            return False
        if request.user_id != user_id:
            return False
        del self._codes[code]
        return True

    def _purge_expired(self) -> int:
        now = datetime.now(timezone.utc)
        expired = [k for k, v in self._codes.items() if now > v.expires_at]
        for k in expired:
            del self._codes[k]
        return len(expired)

    async def _cleanup_loop(self) -> None:
        """Periodically remove expired codes."""
        while True:
            await asyncio.sleep(60)
            n = self._purge_expired()
            if n:
                logger.debug("Purged %d expired pairing codes", n)
