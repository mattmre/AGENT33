"""Tests for the SearchTool."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agent33.tools.base import ToolContext
from agent33.tools.builtin.search import SearchTool


@pytest.fixture
def tool() -> SearchTool:
    return SearchTool()


@pytest.fixture
def context() -> ToolContext:
    return ToolContext()


async def test_name(tool: SearchTool) -> None:
    assert tool.name == "search"


async def test_missing_query(tool: SearchTool, context: ToolContext) -> None:
    result = await tool.execute({}, context)
    assert not result.success


@patch("agent33.tools.builtin.search.settings")
async def test_search_returns_results(mock_settings: AsyncMock, tool: SearchTool, context: ToolContext) -> None:
    mock_settings.searxng_url = "http://searxng:8080"

    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "results": [
            {"title": "Result 1", "url": "https://example.com/1", "content": "Snippet 1"},
            {"title": "Result 2", "url": "https://example.com/2", "content": "Snippet 2"},
        ]
    }
    mock_resp.raise_for_status = AsyncMock()

    with patch("agent33.tools.builtin.search.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        result = await tool.execute({"query": "test query"}, context)
        assert result.success
        assert "Result 1" in result.output
        assert "Result 2" in result.output


@patch("agent33.tools.builtin.search.settings")
async def test_search_connection_error(mock_settings: AsyncMock, tool: SearchTool, context: ToolContext) -> None:
    mock_settings.searxng_url = "http://searxng:8080"

    with patch("agent33.tools.builtin.search.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        import httpx
        mock_client.get.side_effect = httpx.ConnectError("Connection refused")
        mock_client_cls.return_value = mock_client

        result = await tool.execute({"query": "test"}, context)
        assert not result.success
