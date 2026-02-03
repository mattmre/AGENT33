"""Ingestion workers for the Observatory.

This package contains workers that pull content from various sources:
- GDELT: Global news monitoring
- RSS: RSS/Atom feed parsing
- YouTube: Video transcript extraction

The IngestionCoordinator manages background workers for continuous ingestion,
while IngestionManager provides on-demand ingestion with database persistence.
"""

from agent33.ingestion.base import BaseWorker, IngestResult
from agent33.ingestion.coordinator import (
    WORKER_CLASSES,
    IngestionCoordinator,
    WorkerStatus,
)
from agent33.ingestion.gdelt import GDELTWorker
from agent33.ingestion.manager import IngestionManager
from agent33.ingestion.rss import RSSWorker
from agent33.ingestion.youtube import YouTubeWorker

__all__ = [
    "BaseWorker",
    "IngestResult",
    "GDELTWorker",
    "RSSWorker",
    "YouTubeWorker",
    "IngestionManager",
    "IngestionCoordinator",
    "WorkerStatus",
    "WORKER_CLASSES",
]
