"""GDELT news ingestion worker.

GDELT (Global Database of Events, Language, and Tone) provides free access
to global news monitoring data updated every 15 minutes.

API Documentation: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlencode

import httpx

from agent33.ingestion.base import BaseWorker, IngestResult


class GDELTWorker(BaseWorker):
    """Worker that fetches news from GDELT's DOC 2.0 API."""

    GDELT_API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    @property
    def source_type(self) -> str:
        return "gdelt"

    def _build_query(self) -> dict[str, str]:
        """Build GDELT API query parameters from config."""
        # Default: get recent news in English
        query = self.config.get("query", "")
        mode = self.config.get("mode", "artlist")  # artlist, timelinevol, etc.
        max_records = self.config.get("max_records", 50)
        timespan = self.config.get("timespan", "15min")  # 15min, 1h, 24h, etc.
        sort = self.config.get("sort", "datedesc")

        params = {
            "query": query or "sourcelang:eng",
            "mode": mode,
            "maxrecords": str(max_records),
            "timespan": timespan,
            "sort": sort,
            "format": "json",
        }

        # Optional: filter by domain, theme, etc.
        if "domain" in self.config:
            params["query"] += f" domain:{self.config['domain']}"
        if "theme" in self.config:
            params["query"] += f" theme:{self.config['theme']}"

        return params

    async def fetch(self) -> AsyncIterator[IngestResult]:
        """Fetch articles from GDELT."""
        params = self._build_query()
        url = f"{self.GDELT_API_URL}?{urlencode(params)}"

        self._logger.info("fetching_gdelt", query=params.get("query"))

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        articles = data.get("articles", [])
        self._logger.info("gdelt_response", article_count=len(articles))

        for article in articles:
            try:
                # Parse GDELT date format (YYYYMMDDHHMMSS)
                date_str = article.get("seendate", "")
                published_at = None
                if date_str and len(date_str) >= 14:
                    try:
                        published_at = datetime.strptime(
                            date_str[:14], "%Y%m%d%H%M%S"
                        ).replace(tzinfo=UTC)
                    except ValueError:
                        pass

                yield IngestResult(
                    source_url=article.get("url", ""),
                    title=article.get("title", "Untitled"),
                    content=self._build_content(article),
                    published_at=published_at,
                    metadata={
                        "domain": article.get("domain", ""),
                        "language": article.get("language", ""),
                        "source_country": article.get("sourcecountry", ""),
                        "tone": article.get("tone", 0),
                        "gdelt_url": article.get("url", ""),
                        "image_url": article.get("socialimage", ""),
                    },
                )
            except Exception as e:
                self._logger.warning(
                    "article_parse_error",
                    error=str(e),
                    article_url=article.get("url", "unknown"),
                )
                continue

    def _build_content(self, article: dict[str, Any]) -> str:
        """Build content string from article data.

        GDELT doesn't provide full article text, only metadata.
        We combine title and available metadata for the content.
        """
        parts = []

        title = article.get("title", "")
        if title:
            parts.append(f"Title: {title}")

        domain = article.get("domain", "")
        if domain:
            parts.append(f"Source: {domain}")

        language = article.get("language", "")
        if language:
            parts.append(f"Language: {language}")

        # GDELT provides tone score (-100 to +100)
        tone = article.get("tone")
        if tone is not None:
            sentiment = "positive" if tone > 0 else "negative" if tone < 0 else "neutral"
            parts.append(f"Sentiment: {sentiment} (tone: {tone:.1f})")

        return "\n".join(parts)
