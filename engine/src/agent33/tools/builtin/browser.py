"""Browser automation tool using Playwright (optional dependency)."""

from __future__ import annotations

import base64
import logging
from typing import Any

from agent33.tools.base import ToolContext, ToolResult

logger = logging.getLogger(__name__)

_PLAYWRIGHT_AVAILABLE = True
try:
    from playwright.async_api import async_playwright  # type: ignore[import-untyped]
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

_DEFAULT_TIMEOUT_MS = 30_000


class BrowserTool:
    """Navigate pages, take screenshots, and extract text via Playwright.

    Degrades gracefully when Playwright is not installed.
    """

    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return (
            "Open a URL in a headless browser, optionally take a screenshot "
            "or extract page text."
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Run a browser action.

        Parameters
        ----------
        params:
            url        : str  - Page URL to navigate to.
            action     : str  - 'navigate', 'screenshot', or 'extract_text' (default 'navigate').
            timeout_ms : int  - Navigation timeout in milliseconds (default 30000).
        """
        if not _PLAYWRIGHT_AVAILABLE:
            return ToolResult.fail(
                "Playwright is not installed. "
                "Install it with: pip install playwright && playwright install chromium"
            )

        url: str = params.get("url", "").strip()
        if not url:
            return ToolResult.fail("No URL provided")

        action: str = params.get("action", "navigate")
        timeout_ms: int = params.get("timeout_ms", _DEFAULT_TIMEOUT_MS)

        if action not in ("navigate", "screenshot", "extract_text"):
            return ToolResult.fail(f"Unknown action: {action}")

        try:
            return await self._run(url, action, timeout_ms)
        except Exception as exc:
            logger.exception("Browser tool error")
            return ToolResult.fail(f"Browser error: {exc}")

    async def _run(self, url: str, action: str, timeout_ms: int) -> ToolResult:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            try:
                page = await browser.new_page()
                await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")

                if action == "navigate":
                    title = await page.title()
                    return ToolResult.ok(f"Navigated to {url} - title: {title}")

                if action == "screenshot":
                    raw = await page.screenshot(full_page=True, type="png")
                    encoded = base64.b64encode(raw).decode()
                    return ToolResult.ok(encoded)

                if action == "extract_text":
                    text = await page.inner_text("body")
                    return ToolResult.ok(text[:100_000])

                return ToolResult.fail(f"Unhandled action: {action}")
            finally:
                await browser.close()
