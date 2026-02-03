"""Base classes for ingestion workers."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class IngestResult:
    """Result of ingesting a single item."""

    source_url: str
    title: str
    content: str
    content_hash: str = field(default="")
    published_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()


class BaseWorker(ABC):
    """Base class for all ingestion workers."""

    def __init__(
        self,
        tenant_id: str,
        source_id: str,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.tenant_id = tenant_id
        self.source_id = source_id
        self.config = config or {}
        self._logger = logger.bind(
            worker=self.__class__.__name__,
            tenant_id=tenant_id,
            source_id=source_id,
        )

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Return the source type identifier."""
        ...

    @abstractmethod
    async def fetch(self) -> AsyncIterator[IngestResult]:
        """Fetch and yield items from the source.

        Yields:
            IngestResult for each item fetched.
        """
        ...

    async def run(self) -> list[IngestResult]:
        """Run the worker and collect all results.

        Returns:
            List of all ingested items.
        """
        self._logger.info("worker_starting")
        results: list[IngestResult] = []

        try:
            async for result in self.fetch():
                results.append(result)
                self._logger.debug(
                    "item_ingested",
                    url=result.source_url,
                    title=result.title[:50] if result.title else None,
                )
        except Exception as e:
            self._logger.error("worker_failed", error=str(e))
            raise

        self._logger.info("worker_completed", items_count=len(results))
        return results
