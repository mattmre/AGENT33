"""Connector boundary governance coverage for messaging adapters."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from agent33.messaging.discord import DiscordAdapter
from agent33.messaging.imessage import IMessageAdapter
from agent33.messaging.matrix import MatrixAdapter
from agent33.messaging.signal import SignalAdapter
from agent33.messaging.slack import SlackAdapter
from agent33.messaging.telegram import TelegramAdapter
from agent33.messaging.whatsapp import WhatsAppAdapter


class _NeverCalledClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def post(self, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG002
        self.calls.append("post")
        raise AssertionError("HTTP client should not be called when governance denies")

    async def get(self, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG002
        self.calls.append("get")
        raise AssertionError("HTTP client should not be called when governance denies")

    async def put(self, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG002
        self.calls.append("put")
        raise AssertionError("HTTP client should not be called when governance denies")

    async def aclose(self) -> None:
        return None


def _adapter_factories() -> list[tuple[str, Any, str]]:
    return [
        (
            "slack",
            lambda: SlackAdapter(bot_token="xoxb-test", signing_secret="secret"),
            "C123",
        ),
        (
            "discord",
            lambda: DiscordAdapter(bot_token="token", public_key="aa" * 32),
            "123",
        ),
        ("telegram", lambda: TelegramAdapter(token="token"), "123"),
        (
            "whatsapp",
            lambda: WhatsAppAdapter(
                access_token="token",
                phone_number_id="123",
                verify_token="verify",
                app_secret="secret",
            ),
            "15550001111",
        ),
        (
            "signal",
            lambda: SignalAdapter(
                bridge_url="https://signal.example",
                sender_number="+1555",
            ),
            "+1444",
        ),
        (
            "matrix",
            lambda: MatrixAdapter(
                homeserver_url="https://matrix.example.com",
                access_token="token",
                user_id="@agent33:example.com",
            ),
            "!room:example.com",
        ),
        (
            "imessage",
            lambda: IMessageAdapter(bridge_url="https://bb.example.com"),
            "chat-guid",
        ),
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("platform", "adapter_factory", "channel_id"),
    _adapter_factories(),
)
async def test_send_governance_blocked_prevents_http_call(
    monkeypatch: pytest.MonkeyPatch,
    platform: str,
    adapter_factory: Any,
    channel_id: str,
) -> None:
    monkeypatch.setattr("agent33.config.settings.connector_boundary_enabled", True)
    monkeypatch.setattr("agent33.config.settings.connector_policy_pack", "default")
    monkeypatch.setattr(
        "agent33.config.settings.connector_governance_blocked_connectors",
        f"messaging:{platform}",
    )
    monkeypatch.setattr("agent33.config.settings.connector_governance_blocked_operations", "")

    adapter = adapter_factory()
    client = _NeverCalledClient()
    adapter._client = client

    with pytest.raises(RuntimeError, match="Connector governance blocked"):
        await adapter.send(channel_id, "blocked")

    assert client.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("platform", "adapter_factory", "_channel_id"),
    _adapter_factories(),
)
async def test_health_check_governance_blocked_prevents_http_call(
    monkeypatch: pytest.MonkeyPatch,
    platform: str,
    adapter_factory: Any,
    _channel_id: str,  # noqa: ARG001
) -> None:
    monkeypatch.setattr("agent33.config.settings.connector_boundary_enabled", True)
    monkeypatch.setattr("agent33.config.settings.connector_policy_pack", "default")
    monkeypatch.setattr(
        "agent33.config.settings.connector_governance_blocked_connectors",
        f"messaging:{platform}",
    )
    monkeypatch.setattr("agent33.config.settings.connector_governance_blocked_operations", "")

    adapter = adapter_factory()
    client = _NeverCalledClient()
    adapter._client = client

    result = await adapter.health_check()

    assert result.status == "unavailable"
    assert "Connector governance blocked" in result.detail
    assert client.calls == []


@pytest.mark.asyncio
async def test_telegram_poll_loop_governance_blocked_prevents_http_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("agent33.config.settings.connector_boundary_enabled", True)
    monkeypatch.setattr("agent33.config.settings.connector_policy_pack", "default")
    monkeypatch.setattr(
        "agent33.config.settings.connector_governance_blocked_connectors",
        "messaging:telegram",
    )
    monkeypatch.setattr("agent33.config.settings.connector_governance_blocked_operations", "")

    adapter = TelegramAdapter(token="token")
    client = _NeverCalledClient()
    adapter._client = client
    adapter._running = True

    async def _stop_sleep(_seconds: float) -> None:
        adapter._running = False

    monkeypatch.setattr("agent33.messaging.telegram.asyncio.sleep", _stop_sleep)

    await asyncio.wait_for(adapter._poll_loop(), timeout=1)
    assert client.calls == []


@pytest.mark.asyncio
async def test_matrix_sync_loop_governance_blocked_prevents_http_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("agent33.config.settings.connector_boundary_enabled", True)
    monkeypatch.setattr("agent33.config.settings.connector_policy_pack", "default")
    monkeypatch.setattr(
        "agent33.config.settings.connector_governance_blocked_connectors",
        "messaging:matrix",
    )
    monkeypatch.setattr("agent33.config.settings.connector_governance_blocked_operations", "")

    adapter = MatrixAdapter(
        homeserver_url="https://matrix.example.com",
        access_token="token",
        user_id="@agent33:example.com",
    )
    client = _NeverCalledClient()
    adapter._client = client
    adapter._running = True

    async def _stop_sleep(_seconds: float) -> None:
        adapter._running = False

    monkeypatch.setattr("agent33.messaging.matrix.asyncio.sleep", _stop_sleep)

    await asyncio.wait_for(adapter._sync_loop(), timeout=1)
    assert client.calls == []
