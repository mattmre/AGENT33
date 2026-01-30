"""Messaging data models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class Message(BaseModel):
    """An inbound message from any platform."""

    platform: str
    channel_id: str
    user_id: str
    text: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class OutgoingMessage(BaseModel):
    """A message to be sent to a platform channel."""

    channel_id: str
    text: str
    reply_to: str | None = None


class PairingRequest(BaseModel):
    """A pairing request linking a platform user to an AGENT-33 account."""

    platform: str
    user_id: str
    code: str
    expires_at: datetime
