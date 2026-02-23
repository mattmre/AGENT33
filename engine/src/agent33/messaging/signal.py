"""Signal adapter using signal-cli-rest-api."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from agent33.messaging.models import ChannelHealthResult, Message

logger = logging.getLogger(__name__)

class SignalAdapter:
    """MessagingAdapter implementation for Signal via signal-cli REST API."""

    def __init__(self, bridge_url: str, sender_number: str) -> None:
        self._bridge_url = bridge_url.rstrip("/")
        self._sender_number = sender_number
        self._client: httpx.AsyncClient | None = None
        self._queue: asyncio.Queue[Message] = asyncio.Queue()
        self._running = False

    @property
    def platform(self) -> str:
        return "signal"

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=30)
        self._running = True
        logger.info("SignalAdapter started")

    async def stop(self) -> None:
        self._running = False
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        logger.info("SignalAdapter stopped")

    async def send(self, channel_id: str, text: str) -> None:
        """Send a message via the Signal bridge."""
        client = self._ensure_client()
        resp = await client.post(
            f"{self._bridge_url}/v2/send",
            json={
                "message": text,
                "number": self._sender_number,
                "recipients": [channel_id],
            },
        )
        resp.raise_for_status()

    async def receive(self) -> Message:
        return await self._queue.get()

    def enqueue_message(self, payload: dict[str, Any]) -> None:
        """Parse incoming Signal webhook data."""
        # Typically wrapped in {"envelope": {"dataMessage": {"message": "..."}}}
        envelope = payload.get("envelope", {})
        data = envelope.get("dataMessage", {})
        text = data.get("message")
        source = envelope.get("source")

        if not text or not source:
            return

        self._queue.put_nowait(
            Message(
                platform="signal",
                channel_id=source,
                user_id=source,
                text=text,
                metadata={"raw": payload},
            )
        )

    async def health_check(self) -> ChannelHealthResult:
        if self._client is None:
            return ChannelHealthResult(
                platform="signal",
                status="unavailable",
                detail="Not started",
                queue_depth=self._queue.qsize(),
            )
        start = time.monotonic()
        try:
            resp = await self._client.get(f"{self._bridge_url}/v1/about")
            latency = (time.monotonic() - start) * 1000
            if resp.status_code == 200:
                return ChannelHealthResult(
                    platform="signal",
                    status="ok" if self._running else "degraded",
                    latency_ms=round(latency, 2),
                    detail="",
                    queue_depth=self._queue.qsize(),
                )
            return ChannelHealthResult(
                platform="signal",
                status="degraded",
                latency_ms=round(latency, 2),
                detail=f"Status {resp.status_code}",
                queue_depth=self._queue.qsize(),
            )
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            return ChannelHealthResult(
                platform="signal",
                status="unavailable",
                latency_ms=round(latency, 2),
                detail=str(exc),
                queue_depth=self._queue.qsize(),
            )

    def _ensure_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("SignalAdapter is not started")
        return self._client
