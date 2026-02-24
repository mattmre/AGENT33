"""Chat endpoint tests."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_chat_completions_returns_openai_format(client: TestClient) -> None:
    upstream_payload = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1700000000,
        "model": "gpt-4o-mini",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }

    mock_request = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.content = json.dumps(upstream_payload).encode("utf-8")
    mock_response.aread = AsyncMock(return_value=mock_response.content)

    with patch("agent33.api.routes.chat.httpx.AsyncClient") as mock_cls:
        mock_client = MagicMock()
        mock_client.build_request.return_value = mock_request
        mock_client.send = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_cls.return_value = mock_client

        r = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )

    assert r.status_code == 200
    assert r.json() == upstream_payload
    mock_client.build_request.assert_called_once()
    mock_client.send.assert_awaited_once_with(mock_request, stream=True)


def test_chat_completions_ollama_unavailable(client: TestClient) -> None:
    import httpx as _httpx

    with patch("agent33.api.routes.chat.httpx.AsyncClient") as mock_cls:
        mock_client = MagicMock()
        mock_client.build_request.return_value = MagicMock()
        mock_client.send = AsyncMock(side_effect=_httpx.ConnectError("refused"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_cls.return_value = mock_client

        r = client.post(
            "/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )

    assert r.status_code == 503
