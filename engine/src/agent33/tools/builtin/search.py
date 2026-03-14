"""Web search tool backed by the provider-aware research service."""

from __future__ import annotations

from typing import Any

from agent33.tools.base import ToolContext, ToolResult
from agent33.web_research import create_default_web_research_service


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
        try:
            service = create_default_web_research_service()
            response = await service.search(
                query,
                limit=num_results,
                categories=categories,
            )
        except ValueError as exc:
            return ToolResult.fail(str(exc))

        if not response.results:
            return ToolResult.ok("No results found.")

        lines: list[str] = []
        for item in response.results:
            lines.append(
                "\n".join(
                    [
                        f"{item.rank}. {item.title} [{item.trust_level.value}]",
                        f"   {item.url}",
                        f"   {item.snippet}",
                        f"   Trust: {item.trust_reason}",
                    ]
                )
            )

        return ToolResult.ok("\n\n".join(lines))
