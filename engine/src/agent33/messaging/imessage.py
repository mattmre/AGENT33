"""iMessage adapter using BlueBubbles or AppleScript wrapper."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from agent33.messaging.models import ChannelHealthResult, Message

logger = logging.getLogger(__name__)

class IMessageAdapter:
    """MessagingAdapter implementation for iMessage via Mac Bridge."""

    def __init__(self, bridge_url: str) -> None:
        self._bridge_url = bridge_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None
        self._queue: asyncio.Queue[Message] = asyncio.Queue()
        self._running = False

    @property
    def platform(self) -> str:
        return "imessage"

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=30)
        self._running = True
        logger.info("IMessageAdapter started")

    async def stop(self) -> None:
        self._running = False
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        logger.info("IMessageAdapter stopped")

    async def send(self, channel_id: str, text: str) -> None:
        client = self._ensure_client()
        resp = await client.post(
            f"{self._bridge_url}/api/v1/message/text",
            json={"chatGuid": channel_id, "text": text},
        )
        resp.raise_for_status()

    async def receive(self) -> Message:
        return await self._queue.get()

    def enqueue_message(self, payload: dict[str, Any]) -> None:
        """Parse incoming BlueBubbles webhook data."""
        handle = payload.get("data", {}).get("handle", {}).get("address")
        text = payload.get("data", {}).get("text")
        guid = payload.get("data", {}).get("chats", [{}])[0].get("guid")

        if not text or not guid:
            return

        self._queue.put_nowait(
            Message(
                platform="imessage",
                channel_id=guid,
                user_id=handle or "unknown",
                text=text,
                metadata={"raw": payload},
            )
        )

    async def health_check(self) -> ChannelHealthResult:
        if self._client is None:
            return ChannelHealthResult(
                platform="imessage",
                status="unavailable",
                detail="Not started",
                queue_depth=self._queue.qsize(),
            )
        start = time.monotonic()
        try:
            resp = await self._client.get(f"{self._bridge_url}/api/v1/ping")
            latency = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                return ChannelHealthResult(
                    platform="imessage",
                    status="ok" if self._running else "degraded",
                    latency_ms=round(latency, 2),
                    detail="",
                    queue_depth=self._queue.qsize(),
                )
            return ChannelHealthResult(
                platform="imessage",
                status="degraded",
                latency_ms=round(latency, 2),
                detail=f"Status {resp.status_code}",
                queue_depth=self._queue.qsize(),
            )
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            return ChannelHealthResult(
                platform="imessage",
                status="unavailable",
                latency_ms=round(latency, 2),
                detail=str(exc),
                queue_depth=self._queue.qsize(),
            )

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("IMessageAdapter is not started")
        return self._client
