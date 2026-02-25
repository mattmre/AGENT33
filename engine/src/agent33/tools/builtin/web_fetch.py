"""HTTP fetch tool with domain allowlist and size limits."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import httpx

from agent33.connectors.boundary import (
    build_connector_boundary_executor,
    map_connector_exception,
)
from agent33.connectors.models import ConnectorRequest
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

        if not context.domain_allowlist:
            return ToolResult.fail(
                "Domain allowlist not configured — all requests denied by default"
            )
        if not any(
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
        async def _perform_fetch(_request: ConnectorRequest) -> httpx.Response:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
                if method == "GET":
                    return await client.get(url, headers=headers)
                return await client.post(url, headers=headers, content=body)

        boundary_executor = build_connector_boundary_executor(
            default_timeout_seconds=float(timeout),
            retry_attempts=1,
        )
        try:
            if boundary_executor is None:
                resp = await _perform_fetch(
                    ConnectorRequest(connector="tool:web_fetch", operation=method)
                )
            else:
                req = ConnectorRequest(
                    connector="tool:web_fetch",
                    operation=method,
                    payload={"url": url, "headers": headers, "body": body},
                    metadata={"timeout_seconds": float(timeout)},
                )
                resp = await boundary_executor.execute(req, _perform_fetch)
            resp.raise_for_status()
            if 300 <= resp.status_code < 400:
                return ToolResult.fail("Redirect responses are blocked by policy")

            content_length = len(resp.content)
            if content_length > _MAX_RESPONSE_BYTES:
                return ToolResult.fail(
                    f"Response too large ({content_length} bytes, "
                    f"limit {_MAX_RESPONSE_BYTES})"
                )

            return ToolResult.ok(resp.text)

        except Exception as exc:
            if boundary_executor is not None:
                mapped = map_connector_exception(exc, "tool:web_fetch", method)
                return ToolResult.fail(str(mapped))
            if isinstance(exc, httpx.TimeoutException):
                return ToolResult.fail(f"Request timed out after {timeout}s")
            if isinstance(exc, httpx.HTTPStatusError):
                return ToolResult.fail(
                    f"HTTP {exc.response.status_code}: {exc.response.text[:500]}"
                )
            if isinstance(exc, httpx.RequestError):
                return ToolResult.fail(f"Request error: {exc}")
            return ToolResult.fail(f"Request error: {exc}")
