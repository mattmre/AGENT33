"""File-change sensor using polling (os.stat mtime checks)."""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Awaitable

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Type of file system change detected."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass(frozen=True, slots=True)
class FileChangeEvent:
    """A detected file system change."""

    path: str
    change_type: ChangeType


@dataclass
class _WatchEntry:
    """Internal state for a single watch configuration."""

    path: str
    patterns: list[str]
    callback: Callable[[list[FileChangeEvent]], Awaitable[Any]]
    snapshot: dict[str, float] = field(default_factory=dict)


class FileChangeSensor:
    """Polls directories for file changes at a configurable interval.

    Detects new, modified, and deleted files matching glob patterns.
    """

    def __init__(self, poll_interval_seconds: float = 5.0) -> None:
        self._poll_interval = poll_interval_seconds
        self._watches: list[_WatchEntry] = []
        self._task: asyncio.Task[None] | None = None
        self._running = False

    def watch(
        self,
        path: str | Path,
        patterns: list[str],
        callback: Callable[[list[FileChangeEvent]], Awaitable[Any]],
    ) -> None:
        """Register a directory to watch for file changes.

        Parameters
        ----------
        path:
            Directory path to monitor.
        patterns:
            List of glob patterns to match (e.g. ``["*.py", "*.json"]``).
        callback:
            Async callable invoked with a list of change events when
            changes are detected.
        """
        resolved = str(Path(path).resolve())
        entry = _WatchEntry(path=resolved, patterns=patterns, callback=callback)
        # Take initial snapshot so first poll only reports new changes.
        entry.snapshot = self._scan(resolved, patterns)
        self._watches.append(entry)
        logger.info("Watching %s for patterns %s", resolved, patterns)

    # -- lifecycle ------------------------------------------------------------

    def start(self) -> None:
        """Start the background polling loop."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.ensure_future(self._poll_loop())
        logger.info("FileChangeSensor started (interval=%.1fs)", self._poll_interval)

    def stop(self) -> None:
        """Stop the background polling loop."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None
        logger.info("FileChangeSensor stopped")

    # -- internals ------------------------------------------------------------

    @staticmethod
    def _scan(directory: str, patterns: list[str]) -> dict[str, float]:
        """Return ``{filepath: mtime}`` for all files matching patterns."""
        result: dict[str, float] = {}
        try:
            entries = os.scandir(directory)
        except OSError:
            return result

        for entry in entries:
            if not entry.is_file():
                continue
            if any(fnmatch.fnmatch(entry.name, p) for p in patterns):
                try:
                    result[entry.path] = entry.stat().st_mtime
                except OSError:
                    pass
        return result

    async def _poll_loop(self) -> None:
        """Continuously poll watched directories."""
        while self._running:
            for watch in self._watches:
                events = self._diff(watch)
                if events:
                    try:
                        await watch.callback(events)
                    except Exception:
                        logger.exception("Error in file-change callback for %s", watch.path)
            await asyncio.sleep(self._poll_interval)

    def _diff(self, watch: _WatchEntry) -> list[FileChangeEvent]:
        """Compare current state to snapshot and update snapshot in-place."""
        current = self._scan(watch.path, watch.patterns)
        events: list[FileChangeEvent] = []

        # Check for new and modified files.
        for fpath, mtime in current.items():
            old_mtime = watch.snapshot.get(fpath)
            if old_mtime is None:
                events.append(FileChangeEvent(path=fpath, change_type=ChangeType.CREATED))
            elif mtime != old_mtime:
                events.append(FileChangeEvent(path=fpath, change_type=ChangeType.MODIFIED))

        # Check for deleted files.
        for fpath in watch.snapshot:
            if fpath not in current:
                events.append(FileChangeEvent(path=fpath, change_type=ChangeType.DELETED))

        watch.snapshot = current
        return events
