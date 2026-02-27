"""Web search tool backed by a SearXNG instance."""

from __future__ import annotations

from typing import Any

import httpx

from agent33.config import settings
from agent33.connectors.boundary import (
    build_connector_boundary_executor,
    map_connector_exception,
)
from agent33.connectors.models import ConnectorRequest
from agent33.tools.base import ToolContext, ToolResult

_DEFAULT_TIMEOUT = 15


class SearchTool:
    """Query a SearXNG instance and return formatted search results."""

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Search the web via SearXNG and return a numbered list of results."

    async def execute(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Run a web search.

        Parameters
        ----------
        params:
            query       : str  - Search query (required).
            num_results : int  - Maximum results to return (default 10).
            categories  : str  - SearXNG category filter (default "general").
        """
        query: str = params.get("query", "").strip()
        if not query:
            return ToolResult.fail("No search query provided.")

        num_results: int = params.get("num_results", 10)
        categories: str = params.get("categories", "general")
        url = f"{settings.searxng_url}/search"
        request_params = {
            "q": query,
            "format": "json",
            "pageno": 1,
            "categories": categories,
        }

        async def _perform_search(_request: ConnectorRequest) -> httpx.Response:
            async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
                return await client.get(url, params=request_params)

        boundary_executor = build_connector_boundary_executor(
            default_timeout_seconds=float(_DEFAULT_TIMEOUT),
            retry_attempts=1,
        )
        try:
            if boundary_executor is None:
                resp = await _perform_search(
                    ConnectorRequest(connector="search:searxng", operation="GET")
                )
            else:
                req = ConnectorRequest(
                    connector="search:searxng",
                    operation="GET",
                    payload={"url": url, "params": request_params},
                    metadata={"timeout_seconds": float(_DEFAULT_TIMEOUT)},
                )
                resp = await boundary_executor.execute(req, _perform_search)
            resp.raise_for_status()
        except Exception as exc:
            if boundary_executor is not None:
                mapped = map_connector_exception(exc, "search:searxng", "GET")
                return ToolResult.fail(str(mapped))
            if isinstance(exc, httpx.ConnectError):
                return ToolResult.fail(f"Could not connect to SearXNG at {settings.searxng_url}.")
            if isinstance(exc, httpx.TimeoutException):
                return ToolResult.fail("SearXNG request timed out.")
            if isinstance(exc, httpx.HTTPStatusError):
                return ToolResult.fail(
                    f"SearXNG returned HTTP {exc.response.status_code}: {exc.response.text[:500]}"
                )
            if isinstance(exc, httpx.RequestError):
                return ToolResult.fail(f"SearXNG request error: {exc}")
            return ToolResult.fail(f"SearXNG request error: {exc}")

        data = resp.json()
        results = data.get("results", [])[:num_results]

        if not results:
            return ToolResult.ok("No results found.")

        lines: list[str] = []
        for idx, item in enumerate(results, start=1):
            title = item.get("title", "Untitled")
            link = item.get("url", "")
            snippet = item.get("content", "").strip()
            lines.append(f"{idx}. {title}\n   {link}\n   {snippet}")

        return ToolResult.ok("\n\n".join(lines))
