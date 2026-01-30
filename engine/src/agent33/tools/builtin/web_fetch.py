"""HTTP fetch tool with domain allowlist and size limits."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from agent33.tools.base import ToolContext, ToolResult

_DEFAULT_TIMEOUT = 30
_MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB


class WebFetchTool:
    """Perform HTTP GET/POST requests with governance controls."""

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch a URL via HTTP GET or POST, returning the response body."

    async def execute(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Fetch a URL.

        Parameters
        ----------
        params:
            url     : str            - Target URL.
            method  : str            - 'GET' or 'POST' (default GET).
            headers : dict[str,str]  - Optional extra headers.
            body    : str            - Optional request body for POST.
            timeout : int            - Seconds (default 30).
        """
        url: str = params.get("url", "").strip()
        if not url:
            return ToolResult.fail("No URL provided")

        parsed = urlparse(url)
        domain = parsed.hostname or ""

        if context.domain_allowlist and not any(
            domain == allowed or domain.endswith(f".{allowed}")
            for allowed in context.domain_allowlist
        ):
            return ToolResult.fail(
                f"Domain '{domain}' is not in the allowlist: "
                f"{context.domain_allowlist}"
            )

        method: str = params.get("method", "GET").upper()
        if method not in ("GET", "POST"):
            return ToolResult.fail(f"Unsupported method: {method}")

        headers: dict[str, str] = params.get("headers", {})
        body: str | None = params.get("body")
        timeout: int = params.get("timeout", _DEFAULT_TIMEOUT)

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                if method == "GET":
                    resp = await client.get(url, headers=headers)
                else:
                    resp = await client.post(url, headers=headers, content=body)

            resp.raise_for_status()

            content_length = len(resp.content)
            if content_length > _MAX_RESPONSE_BYTES:
                return ToolResult.fail(
                    f"Response too large ({content_length} bytes, "
                    f"limit {_MAX_RESPONSE_BYTES})"
                )

            return ToolResult.ok(resp.text)

        except httpx.TimeoutException:
            return ToolResult.fail(f"Request timed out after {timeout}s")
        except httpx.HTTPStatusError as exc:
            return ToolResult.fail(
                f"HTTP {exc.response.status_code}: {exc.response.text[:500]}"
            )
        except httpx.RequestError as exc:
            return ToolResult.fail(f"Request error: {exc}")
