"""Slack Web API adapter using plain httpx."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import logging
import time
from typing import Any

import httpx

from agent33.messaging.models import Message

logger = logging.getLogger(__name__)

_API_BASE = "https://slack.com/api"


class SlackAdapter:
    """MessagingAdapter implementation for Slack."""

    def __init__(self, bot_token: str, signing_secret: str) -> None:
        self._bot_token = bot_token
        self._signing_secret = signing_secret
        self._client: httpx.AsyncClient | None = None
        self._queue: asyncio.Queue[Message] = asyncio.Queue()

    @property
    def platform(self) -> str:
        return "slack"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=_API_BASE,
            headers={
                "Authorization": f"Bearer {self._bot_token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            timeout=30,
        )
        logger.info("SlackAdapter started")

    async def stop(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        logger.info("SlackAdapter stopped")

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    async def send(self, channel_id: str, text: str) -> None:
        client = self._ensure_client()
        resp = await client.post(
            "/chat.postMessage",
            json={"channel": channel_id, "text": text},
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Slack API error: {data.get('error', 'unknown')}")

    # ------------------------------------------------------------------
    # Receiving
    # ------------------------------------------------------------------

    async def receive(self) -> Message:
        return await self._queue.get()

    def enqueue_event(self, payload: dict[str, Any]) -> None:
        """Parse a Slack Events API payload and enqueue it."""
        event = payload.get("event", {})
        event_type = event.get("type")
        if event_type != "message":
            return
        # Ignore bot messages to avoid loops
        if event.get("bot_id"):
            return
        self._queue.put_nowait(
            Message(
                platform="slack",
                channel_id=str(event.get("channel", "")),
                user_id=str(event.get("user", "")),
                text=event.get("text", ""),
                metadata={"raw": payload},
            )
        )

    def verify_signature(self, timestamp: str, body: bytes, signature: str) -> bool:
        """Verify Slack request signature using the signing secret."""
        # Reject requests older than 5 minutes
        if abs(time.time() - float(timestamp)) > 300:
            return False
        sig_basestring = f"v0:{timestamp}:{body.decode()}"
        computed = "v0=" + hmac.new(
            self._signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(computed, signature)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("SlackAdapter is not started")
        return self._client
