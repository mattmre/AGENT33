"""Ingestion coordinator - manages background workers for continuous ingestion.

This module provides centralized coordination of all ingestion workers,
running them as background tasks with proper lifecycle management.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

# Import SourceResponse for type hints - use string annotation to avoid circular import
# The actual type is from agent33.api.routes.sources
from typing import TYPE_CHECKING, Any
from uuid import UUID

import structlog

from agent33.db.models import SourceType
from agent33.ingestion.base import BaseWorker, IngestResult
from agent33.ingestion.gdelt import GDELTWorker
from agent33.ingestion.rss import RSSWorker
from agent33.ingestion.youtube import YouTubeWorker

if TYPE_CHECKING:
    from agent33.api.routes.sources import SourceResponse

logger = structlog.get_logger()


# Map source types to their worker implementations
WORKER_CLASSES: dict[SourceType, type[BaseWorker]] = {
    SourceType.GDELT: GDELTWorker,
    SourceType.RSS: RSSWorker,
    SourceType.YOUTUBE: YouTubeWorker,
}


@dataclass
class WorkerStatus:
    """Status information for a running ingestion worker."""

    source_id: UUID
    source_name: str
    is_running: bool
    last_fetch_at: datetime | None = None
    items_fetched_total: int = 0
    errors_total: int = 0
    next_fetch_at: datetime | None = None


@dataclass
class _WorkerContext:
    """Internal context for managing a worker's lifecycle."""

    source_id: UUID
    source_name: str
    source_type: SourceType
    tenant_id: str
    config: dict[str, Any]
    poll_interval_seconds: int
    task: asyncio.Task[None] | None = None
    is_running: bool = False
    last_fetch_at: datetime | None = None
    items_fetched_total: int = 0
    errors_total: int = 0
    next_fetch_at: datetime | None = None
    _stop_event: asyncio.Event = field(default_factory=asyncio.Event)

    def to_status(self) -> WorkerStatus:
        """Convert internal context to public status."""
        return WorkerStatus(
            source_id=self.source_id,
            source_name=self.source_name,
            is_running=self.is_running,
            last_fetch_at=self.last_fetch_at,
            items_fetched_total=self.items_fetched_total,
            errors_total=self.errors_total,
            next_fetch_at=self.next_fetch_at,
        )


# Type aliases for callback functions
EmitActivityCallback = Callable[[str, str, dict[str, Any]], Awaitable[None]]
StoreContentCallback = Callable[[UUID, IngestResult], Awaitable[bool]]
UpdateCursorCallback = Callable[[UUID, datetime], Awaitable[None]]


class IngestionCoordinator:
    """Coordinates all ingestion workers as background tasks.

    This class manages the lifecycle of ingestion workers, including:
    - Starting/stopping workers for individual sources
    - Running workers as background asyncio tasks
    - Tracking worker status and health
    - Thread-safe access to worker state

    Example usage:
        async def emit_activity(activity_type, message, metadata):
            # Log activity to database
            pass

        async def store_content(source_id, result):
            # Store ingested content
            return True

        async def update_cursor(source_id, timestamp):
            # Update source's last_fetched_at
            pass

        coordinator = IngestionCoordinator(
            emit_activity=emit_activity,
            store_content=store_content,
            update_source_cursor=update_cursor,
        )

        # Start workers for all active sources
        await coordinator.start_all(active_sources)

        # Check health
        health = await coordinator.health_check()

        # Shutdown
        await coordinator.stop_all()
    """

    def __init__(
        self,
        emit_activity: EmitActivityCallback,
        store_content: StoreContentCallback,
        update_source_cursor: UpdateCursorCallback,
    ) -> None:
        """Initialize the coordinator with callback functions.

        Args:
            emit_activity: Callback to emit activity events.
                Signature: (activity_type: str, message: str, metadata: dict) -> None
            store_content: Callback to store ingested content.
                Signature: (source_id: UUID, result: IngestResult) -> bool (True if new)
            update_source_cursor: Callback to update source's last fetch timestamp.
                Signature: (source_id: UUID, timestamp: datetime) -> None
        """
        self._emit_activity = emit_activity
        self._store_content = store_content
        self._update_source_cursor = update_source_cursor
        self._workers: dict[UUID, _WorkerContext] = {}
        self._lock = asyncio.Lock()
        self._logger = logger.bind(component="ingestion_coordinator")
        self._shutdown_event = asyncio.Event()

    async def start_worker(self, source: SourceResponse) -> bool:
        """Start a background worker for the given source.

        Args:
            source: The source configuration to start a worker for.

        Returns:
            True if the worker was started, False if already running or unsupported.
        """
        source_id = UUID(source.id) if isinstance(source.id, str) else source.id

        async with self._lock:
            # Check if worker is already running
            if source_id in self._workers and self._workers[source_id].is_running:
                self._logger.warning(
                    "worker_already_running",
                    source_id=str(source_id),
                    source_name=source.name,
                )
                return False

            # Check if we support this source type
            try:
                source_type = SourceType(source.source_type)
            except ValueError:
                self._logger.error(
                    "unsupported_source_type",
                    source_type=source.source_type,
                    source_id=str(source_id),
                )
                return False

            if source_type not in WORKER_CLASSES:
                self._logger.warning(
                    "no_worker_for_source_type",
                    source_type=source_type.value,
                    source_id=str(source_id),
                )
                return False

            # Get poll interval from config, default to 5 minutes
            poll_interval = source.config.get("poll_interval_seconds", 300)

            # Create worker context
            context = _WorkerContext(
                source_id=source_id,
                source_name=source.name,
                source_type=source_type,
                tenant_id=source.config.get("tenant_id", "default"),
                config={"url": source.url, **source.config},
                poll_interval_seconds=poll_interval,
            )

            # Start the background task
            context.task = asyncio.create_task(
                self._run_worker_loop(context),
                name=f"ingestion_worker_{source_id}",
            )
            context.is_running = True

            self._workers[source_id] = context

            self._logger.info(
                "worker_started",
                source_id=str(source_id),
                source_name=source.name,
                source_type=source_type.value,
                poll_interval=poll_interval,
            )

            return True

    async def stop_worker(self, source_id: UUID) -> bool:
        """Stop a running worker.

        Args:
            source_id: The source ID to stop.

        Returns:
            True if the worker was stopped, False if not found or not running.
        """
        async with self._lock:
            if source_id not in self._workers:
                return False

            context = self._workers[source_id]
            if not context.is_running:
                return False

            # Signal the worker to stop
            context._stop_event.set()
            context.is_running = False

            # Cancel the task
            if context.task and not context.task.done():
                context.task.cancel()
                try:
                    await asyncio.wait_for(
                        asyncio.shield(context.task), timeout=5.0
                    )
                except (TimeoutError, asyncio.CancelledError):
                    pass

            self._logger.info(
                "worker_stopped",
                source_id=str(source_id),
                source_name=context.source_name,
            )

            # Remove from workers dict
            del self._workers[source_id]

            return True

    async def restart_worker(self, source: SourceResponse) -> bool:
        """Restart a worker with potentially updated configuration.

        Args:
            source: The source configuration.

        Returns:
            True if restart succeeded, False otherwise.
        """
        source_id = UUID(source.id) if isinstance(source.id, str) else source.id

        # Stop if running
        await self.stop_worker(source_id)

        # Start with new config
        return await self.start_worker(source)

    async def start_all(self, sources: list[SourceResponse]) -> int:
        """Start workers for all provided sources.

        Args:
            sources: List of source configurations to start workers for.

        Returns:
            Number of workers successfully started.
        """
        started = 0
        for source in sources:
            if source.is_active:
                if await self.start_worker(source):
                    started += 1

        self._logger.info(
            "started_all_workers",
            requested=len(sources),
            started=started,
        )

        return started

    async def stop_all(self) -> int:
        """Stop all running workers.

        Returns:
            Number of workers stopped.
        """
        self._shutdown_event.set()

        async with self._lock:
            source_ids = list(self._workers.keys())

        stopped = 0
        for source_id in source_ids:
            if await self.stop_worker(source_id):
                stopped += 1

        self._logger.info("stopped_all_workers", stopped=stopped)

        return stopped

    def get_status(self, source_id: UUID) -> WorkerStatus | None:
        """Get status for a specific worker.

        Args:
            source_id: The source ID to get status for.

        Returns:
            WorkerStatus if found, None otherwise.
        """
        context = self._workers.get(source_id)
        if context:
            return context.to_status()
        return None

    def get_all_statuses(self) -> list[WorkerStatus]:
        """Get status for all workers.

        Returns:
            List of all worker statuses.
        """
        return [ctx.to_status() for ctx in self._workers.values()]

    async def health_check(self) -> dict[str, Any]:
        """Get aggregate health information for all workers.

        Returns:
            Dictionary with health metrics.
        """
        async with self._lock:
            total_workers = len(self._workers)
            running_workers = sum(1 for ctx in self._workers.values() if ctx.is_running)
            total_items = sum(ctx.items_fetched_total for ctx in self._workers.values())
            total_errors = sum(ctx.errors_total for ctx in self._workers.values())

            worker_details = []
            for ctx in self._workers.values():
                worker_details.append({
                    "source_id": str(ctx.source_id),
                    "source_name": ctx.source_name,
                    "source_type": ctx.source_type.value,
                    "is_running": ctx.is_running,
                    "items_fetched": ctx.items_fetched_total,
                    "errors": ctx.errors_total,
                    "last_fetch_at": ctx.last_fetch_at.isoformat() if ctx.last_fetch_at else None,
                    "next_fetch_at": ctx.next_fetch_at.isoformat() if ctx.next_fetch_at else None,
                })

        return {
            "status": "healthy" if running_workers == total_workers else "degraded",
            "total_workers": total_workers,
            "running_workers": running_workers,
            "stopped_workers": total_workers - running_workers,
            "total_items_fetched": total_items,
            "total_errors": total_errors,
            "workers": worker_details,
        }

    async def _run_worker_loop(self, context: _WorkerContext) -> None:
        """Run the worker loop for a source.

        This runs continuously, fetching items at the configured interval
        until stopped or cancelled.
        """
        worker_logger = self._logger.bind(
            source_id=str(context.source_id),
            source_name=context.source_name,
            source_type=context.source_type.value,
        )

        worker_cls = WORKER_CLASSES.get(context.source_type)
        if not worker_cls:
            worker_logger.error("worker_class_not_found")
            return

        while not context._stop_event.is_set() and not self._shutdown_event.is_set():
            try:
                # Create a fresh worker instance for each fetch cycle
                worker = worker_cls(
                    tenant_id=context.tenant_id,
                    source_id=str(context.source_id),
                    config=context.config,
                )

                worker_logger.info("fetch_cycle_starting")

                # Run the fetch
                items_fetched = 0
                new_items = 0

                try:
                    async for result in worker.fetch():
                        # Store the content via callback
                        is_new = await self._store_content(context.source_id, result)
                        items_fetched += 1
                        if is_new:
                            new_items += 1

                    # Update context stats
                    context.last_fetch_at = datetime.now(UTC)
                    context.items_fetched_total += items_fetched

                    # Update cursor via callback
                    await self._update_source_cursor(
                        context.source_id, context.last_fetch_at
                    )

                    # Emit activity
                    await self._emit_activity(
                        "ingested",
                        f"Ingested {items_fetched} items from {context.source_name}",
                        {
                            "source_id": str(context.source_id),
                            "source_name": context.source_name,
                            "items_fetched": items_fetched,
                            "new_items": new_items,
                        },
                    )

                    worker_logger.info(
                        "fetch_cycle_complete",
                        items_fetched=items_fetched,
                        new_items=new_items,
                    )

                except Exception as e:
                    context.errors_total += 1
                    worker_logger.error(
                        "fetch_cycle_failed",
                        error=str(e),
                        error_count=context.errors_total,
                    )

                    # Emit error activity
                    await self._emit_activity(
                        "error",
                        f"Ingestion error for {context.source_name}: {str(e)}",
                        {
                            "source_id": str(context.source_id),
                            "source_name": context.source_name,
                            "error": str(e),
                        },
                    )

                # Calculate next fetch time
                context.next_fetch_at = datetime.now(UTC)
                # Add poll interval - handled in the sleep below

                # Wait for next poll interval or until stopped
                try:
                    await asyncio.wait_for(
                        context._stop_event.wait(),
                        timeout=context.poll_interval_seconds,
                    )
                    # If we get here, stop_event was set
                    break
                except TimeoutError:
                    # Normal timeout, continue to next fetch
                    pass

            except asyncio.CancelledError:
                worker_logger.info("worker_cancelled")
                break
            except Exception as e:
                # Unexpected error - log and continue after a delay
                context.errors_total += 1
                worker_logger.exception(
                    "worker_loop_unexpected_error",
                    error=str(e),
                )
                # Wait a bit before retrying to avoid tight loop on persistent errors
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    break

        context.is_running = False
        worker_logger.info("worker_loop_exited")
