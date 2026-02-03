"""RSS/Atom feed ingestion worker."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import AsyncIterator
from html import unescape
import re

import httpx

from agent33.ingestion.base import BaseWorker, IngestResult

# Optional: use feedparser if available for better parsing
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False


class RSSWorker(BaseWorker):
    """Worker that fetches and parses RSS/Atom feeds."""

    @property
    def source_type(self) -> str:
        return "rss"

    async def fetch(self) -> AsyncIterator[IngestResult]:
        """Fetch and parse RSS feed items."""
        feed_url = self.config.get("url")
        if not feed_url:
            raise ValueError("RSS worker requires 'url' in config")

        max_items = self.config.get("max_items", 50)

        self._logger.info("fetching_rss", url=feed_url)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(feed_url)
            response.raise_for_status()
            content = response.text

        if HAS_FEEDPARSER:
            items = self._parse_with_feedparser(content, max_items)
        else:
            items = self._parse_simple(content, max_items)

        for item in items:
            yield item

    def _parse_with_feedparser(
        self, content: str, max_items: int
    ) -> list[IngestResult]:
        """Parse feed using feedparser library."""
        feed = feedparser.parse(content)
        results = []

        for entry in feed.entries[:max_items]:
            # Get published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass

            # Build content from summary/description
            content_text = ""
            if hasattr(entry, "summary"):
                content_text = self._strip_html(entry.summary)
            elif hasattr(entry, "description"):
                content_text = self._strip_html(entry.description)

            # Get link
            link = getattr(entry, "link", "") or ""
            if not link and hasattr(entry, "links") and entry.links:
                link = entry.links[0].get("href", "")

            results.append(
                IngestResult(
                    source_url=link,
                    title=getattr(entry, "title", "Untitled"),
                    content=content_text,
                    published_at=published_at,
                    metadata={
                        "feed_title": feed.feed.get("title", ""),
                        "author": getattr(entry, "author", ""),
                        "tags": [t.get("term", "") for t in getattr(entry, "tags", [])],
                    },
                )
            )

        return results

    def _parse_simple(self, content: str, max_items: int) -> list[IngestResult]:
        """Simple XML parsing fallback when feedparser is not available."""
        results = []

        # Very basic RSS parsing - extract items
        item_pattern = re.compile(
            r"<item[^>]*>(.*?)</item>", re.DOTALL | re.IGNORECASE
        )
        title_pattern = re.compile(r"<title[^>]*>(.*?)</title>", re.DOTALL | re.IGNORECASE)
        link_pattern = re.compile(r"<link[^>]*>(.*?)</link>", re.DOTALL | re.IGNORECASE)
        desc_pattern = re.compile(
            r"<description[^>]*>(.*?)</description>", re.DOTALL | re.IGNORECASE
        )
        pubdate_pattern = re.compile(
            r"<pubDate[^>]*>(.*?)</pubDate>", re.DOTALL | re.IGNORECASE
        )

        items = item_pattern.findall(content)[:max_items]

        for item_xml in items:
            title_match = title_pattern.search(item_xml)
            link_match = link_pattern.search(item_xml)
            desc_match = desc_pattern.search(item_xml)
            pubdate_match = pubdate_pattern.search(item_xml)

            title = self._strip_html(title_match.group(1)) if title_match else "Untitled"
            link = self._strip_html(link_match.group(1)) if link_match else ""
            description = self._strip_html(desc_match.group(1)) if desc_match else ""

            published_at = None
            if pubdate_match:
                try:
                    published_at = parsedate_to_datetime(pubdate_match.group(1))
                except Exception:
                    pass

            results.append(
                IngestResult(
                    source_url=link,
                    title=title,
                    content=description,
                    published_at=published_at,
                    metadata={},
                )
            )

        return results

    def _strip_html(self, text: str) -> str:
        """Remove HTML tags and decode entities."""
        # Remove CDATA wrappers
        text = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", text, flags=re.DOTALL)
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)
        # Decode HTML entities
        text = unescape(text)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
