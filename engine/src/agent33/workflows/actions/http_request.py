"""Action that performs an HTTP request as a workflow step."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

logger = structlog.get_logger()


async def execute(
    url: str | None,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: Any | None = None,
    timeout_seconds: int = 30,
    inputs: dict[str, Any] | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Make an HTTP request and return the response.

    Args:
        url: Target URL (required).
        method: HTTP method (GET, POST, PUT, etc.).
        headers: Optional request headers.
        body: Optional request body (dict/list sends as JSON,
            anything else as text).
        timeout_seconds: Request timeout in seconds.
        inputs: Additional context (unused, kept for action signature
            consistency).
        dry_run: If True, log but skip actual request.

    Returns:
        A dict with ``status_code``, ``headers``, ``body`` (text),
        and ``json`` (parsed JSON or None).

    Raises:
        ValueError: If *url* is not provided.
    """
    if not url:
        raise ValueError("http-request action requires a 'url' field")

    logger.info("http_request", url=url, method=method, dry_run=dry_run)

    if dry_run:
        return {"dry_run": True, "url": url, "method": method}

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        kwargs: dict[str, Any] = {"headers": headers or {}}
        if body is not None:
            if isinstance(body, (dict, list)):
                kwargs["json"] = body
            else:
                kwargs["content"] = str(body)
        response = await client.request(method, url, **kwargs)

    response_body = response.text
    try:
        response_json = response.json()
    except Exception:
        response_json = None

    logger.info(
        "http_request_complete",
        url=url,
        status_code=response.status_code,
    )

    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response_body,
        "json": response_json,
    }
