"""Telegram Bot API adapter using plain httpx."""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any

import httpx

from agent33.messaging.models import Message

logger = logging.getLogger(__name__)

_API_BASE = "https://api.telegram.org"


class TelegramAdapter:
    """MessagingAdapter implementation for Telegram."""

    def __init__(self, token: str) -> None:
        self._token = token
        self._base = f"{_API_BASE}/bot{token}"
        self._client: httpx.AsyncClient | None = None
        self._queue: asyncio.Queue[Message] = asyncio.Queue()
        self._running = False
        self._poll_task: asyncio.Task[None] | None = None

    @property
    def platform(self) -> str:
        return "telegram"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start long-polling for updates."""
        self._client = httpx.AsyncClient(timeout=60)
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("TelegramAdapter started (long-poll)")

    async def stop(self) -> None:
        """Cancel polling and close the HTTP client."""
        self._running = False
        if self._poll_task is not None:
            self._poll_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._poll_task
            self._poll_task = None
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        logger.info("TelegramAdapter stopped")

    # ------------------------------------------------------------------
    # Sending
    # ------------------------------------------------------------------

    async def send(self, channel_id: str, text: str) -> None:
        """Send a text message to a Telegram chat."""
        client = self._ensure_client()
        resp = await client.post(
            f"{self._base}/sendMessage",
            json={"chat_id": channel_id, "text": text, "parse_mode": "Markdown"},
        )
        resp.raise_for_status()

    # ------------------------------------------------------------------
    # Receiving
    # ------------------------------------------------------------------

    async def receive(self) -> Message:
        """Return the next queued inbound message."""
        return await self._queue.get()

    def enqueue_webhook_update(self, payload: dict[str, Any]) -> None:
        """Parse a Telegram webhook update and place it on the queue."""
        msg_data = payload.get("message") or payload.get("edited_message")
        if msg_data is None:
            return
        text = msg_data.get("text", "")
        chat = msg_data.get("chat", {})
        user = msg_data.get("from", {})
        self._queue.put_nowait(
            Message(
                platform="telegram",
                channel_id=str(chat.get("id", "")),
                user_id=str(user.get("id", "")),
                text=text,
                metadata={"raw": payload},
            )
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        """Long-poll getUpdates in a background task."""
        offset = 0
        client = self._ensure_client()
        while self._running:
            try:
                resp = await client.get(
                    f"{self._base}/getUpdates",
                    params={"offset": offset, "timeout": 30},
                )
                resp.raise_for_status()
                updates = resp.json().get("result", [])
                for update in updates:
                    self.enqueue_webhook_update(update)
                    offset = update["update_id"] + 1
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Telegram poll error")
                await asyncio.sleep(5)

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("TelegramAdapter is not started")
        return self._client
