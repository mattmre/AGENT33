"""Web search tool backed by a SearXNG instance."""

from __future__ import annotations

from typing import Any

import httpx

from agent33.config import settings
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

        try:
            async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
                resp = await client.get(url, params=request_params)
            resp.raise_for_status()
        except httpx.ConnectError:
            return ToolResult.fail(
                f"Could not connect to SearXNG at {settings.searxng_url}."
            )
        except httpx.TimeoutException:
            return ToolResult.fail("SearXNG request timed out.")
        except httpx.HTTPStatusError as exc:
            return ToolResult.fail(
                f"SearXNG returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:500]}"
            )
        except httpx.RequestError as exc:
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
