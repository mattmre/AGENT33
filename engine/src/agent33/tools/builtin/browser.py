"""Browser automation tool using Playwright (optional dependency)."""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from agent33.tools.base import ToolContext, ToolResult

logger = logging.getLogger(__name__)

_PLAYWRIGHT_AVAILABLE = True
try:
    from playwright.async_api import (  # type: ignore[import-untyped]
        Browser,
        Page,
        Playwright,
        async_playwright,
    )
except ImportError:
    _PLAYWRIGHT_AVAILABLE = False

_DEFAULT_TIMEOUT_MS = 30_000
_SESSION_TTL_SECONDS = 300  # 5 minutes idle


@dataclass
class BrowserSession:
    """Holds a persistent browser and page for multi-step automation."""

    pw: Any  # Playwright context manager
    browser: Any  # Browser instance
    page: Any  # Page instance
    last_used: float = field(default_factory=time.monotonic)


_sessions: dict[str, BrowserSession] = {}


async def _get_session(session_id: str) -> BrowserSession:
    """Get or create a browser session."""
    if session_id in _sessions:
        sess = _sessions[session_id]
        sess.last_used = time.monotonic()
        return sess

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    page = await browser.new_page()
    sess = BrowserSession(pw=pw, browser=browser, page=page)
    _sessions[session_id] = sess
    return sess


async def _close_session(session_id: str) -> None:
    """Close and remove a browser session."""
    sess = _sessions.pop(session_id, None)
    if sess:
        try:
            await sess.browser.close()
            await sess.pw.stop()
        except Exception:
            logger.debug("Error closing session %s", session_id, exc_info=True)


async def _cleanup_stale_sessions() -> None:
    """Close sessions idle beyond TTL."""
    now = time.monotonic()
    stale = [sid for sid, s in _sessions.items() if now - s.last_used > _SESSION_TTL_SECONDS]
    for sid in stale:
        await _close_session(sid)


_VALID_ACTIONS = frozenset({
    "navigate", "screenshot", "extract_text",
    "click", "type_text", "select", "scroll", "wait_for", "get_elements",
    "close_session",
})


class BrowserTool:
    """Navigate pages, take screenshots, extract text, and perform interactive
    automation via Playwright.

    Degrades gracefully when Playwright is not installed.
    """

    @property
    def name(self) -> str:
        return "browser"

    @property
    def description(self) -> str:
        return (
            "Headless browser automation: navigate, screenshot, extract text, "
            "click, type, select, scroll, wait for elements. Supports persistent "
            "sessions for multi-step interactions."
        )

    async def execute(self, params: dict[str, Any], context: ToolContext) -> ToolResult:
        """Run a browser action.

        Parameters
        ----------
        params:
            url         : str  - Page URL (required for navigate/screenshot/extract_text).
            action      : str  - One of: navigate, screenshot, extract_text, click,
                                 type_text, select, scroll, wait_for, get_elements,
                                 close_session.
            session_id  : str  - Optional session ID to reuse a browser across calls.
            selector    : str  - CSS selector (for click/type_text/select/wait_for/get_elements).
            text        : str  - Text to type (for type_text).
            value       : str  - Value to select (for select).
            direction   : str  - 'up' or 'down' (for scroll, default 'down').
            amount      : int  - Scroll pixels (for scroll, default 500).
            timeout_ms  : int  - Timeout in milliseconds (default 30000).
        """
        if not _PLAYWRIGHT_AVAILABLE:
            return ToolResult.fail(
                "Playwright is not installed. "
                "Install it with: pip install playwright && playwright install chromium"
            )

        action: str = params.get("action", "navigate")
        if action not in _VALID_ACTIONS:
            return ToolResult.fail(f"Unknown action: {action}")

        session_id: str | None = params.get("session_id")
        timeout_ms: int = params.get("timeout_ms", _DEFAULT_TIMEOUT_MS)

        try:
            await _cleanup_stale_sessions()

            if action == "close_session":
                if session_id:
                    await _close_session(session_id)
                    return ToolResult.ok(f"Session '{session_id}' closed")
                return ToolResult.fail("No session_id provided for close_session")

            # Session-based execution
            if session_id:
                return await self._run_with_session(session_id, action, params, timeout_ms)

            # Legacy one-shot execution (backward compatible)
            url: str = params.get("url", "").strip()
            if not url:
                return ToolResult.fail("No URL provided")
            return await self._run_oneshot(url, action, params, timeout_ms)

        except Exception as exc:
            logger.exception("Browser tool error")
            return ToolResult.fail(f"Browser error: {exc}")

    async def _run_with_session(
        self, session_id: str, action: str, params: dict[str, Any], timeout_ms: int
    ) -> ToolResult:
        sess = await _get_session(session_id)
        page = sess.page

        url: str = params.get("url", "").strip()
        if action == "navigate":
            if not url:
                return ToolResult.fail("No URL provided")
            await page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            title = await page.title()
            return ToolResult.ok(f"Navigated to {url} - title: {title}")

        if action == "screenshot":
            raw = await page.screenshot(full_page=True, type="png")
            return ToolResult.ok(base64.b64encode(raw).decode())

        if action == "extract_text":
            text = await page.inner_text("body")
            return ToolResult.ok(text[:100_000])

        return await self._run_interactive(page, action, params, timeout_ms)

    async def _run_oneshot(
        self, url: str, action: str, params: dict[str, Any], timeout_ms: int
    ) -> ToolResult:
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
                    return ToolResult.ok(base64.b64encode(raw).decode())

                if action == "extract_text":
                    text = await page.inner_text("body")
                    return ToolResult.ok(text[:100_000])

                return await self._run_interactive(page, action, params, timeout_ms)
            finally:
                await browser.close()

    async def _run_interactive(
        self, page: Any, action: str, params: dict[str, Any], timeout_ms: int
    ) -> ToolResult:
        selector: str = params.get("selector", "")

        if action == "click":
            if not selector:
                return ToolResult.fail("No selector provided for click")
            await page.click(selector, timeout=timeout_ms)
            return ToolResult.ok(f"Clicked: {selector}")

        if action == "type_text":
            if not selector:
                return ToolResult.fail("No selector provided for type_text")
            text: str = params.get("text", "")
            await page.fill(selector, text, timeout=timeout_ms)
            return ToolResult.ok(f"Typed into {selector}")

        if action == "select":
            if not selector:
                return ToolResult.fail("No selector provided for select")
            value: str = params.get("value", "")
            await page.select_option(selector, value, timeout=timeout_ms)
            return ToolResult.ok(f"Selected '{value}' in {selector}")

        if action == "scroll":
            direction: str = params.get("direction", "down")
            amount: int = params.get("amount", 500)
            delta = amount if direction == "down" else -amount
            await page.mouse.wheel(0, delta)
            return ToolResult.ok(f"Scrolled {direction} by {amount}px")

        if action == "wait_for":
            if not selector:
                return ToolResult.fail("No selector provided for wait_for")
            await page.wait_for_selector(selector, timeout=timeout_ms)
            return ToolResult.ok(f"Element found: {selector}")

        if action == "get_elements":
            if not selector:
                return ToolResult.fail("No selector provided for get_elements")
            elements = await page.query_selector_all(selector)
            texts = []
            for el in elements[:50]:  # cap at 50 elements
                txt = (await el.text_content() or "").strip()
                if txt:
                    texts.append(txt)
            return ToolResult.ok("\n".join(texts))

        return ToolResult.fail(f"Unhandled action: {action}")
