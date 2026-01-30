"""Tool registry for discovering and managing available tools."""

from __future__ import annotations

import importlib.metadata
import logging
from typing import Any

from agent33.tools.base import Tool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry of available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool instance. Overwrites any existing tool with the same name."""
        self._tools[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    def get(self, name: str) -> Tool | None:
        """Return the tool with the given name, or ``None``."""
        return self._tools.get(name)

    def list_all(self) -> list[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())

    def discover_from_entrypoints(self, group: str = "agent33.tools") -> int:
        """Load tools advertised via setuptools entry points.

        Each entry point must resolve to a callable that returns a ``Tool``
        instance (or a ``Tool`` class that can be instantiated with no args).

        Returns the number of tools discovered.
        """
        count = 0
        eps = importlib.metadata.entry_points()
        # Python 3.12+ returns a SelectableGroups / dict; 3.9+ has .select()
        selected = eps.select(group=group) if hasattr(eps, "select") else eps.get(group, [])
        for ep in selected:
            try:
                obj = ep.load()
                tool: Tool = obj() if callable(obj) and not isinstance(obj, Tool) else obj
                self.register(tool)
                count += 1
            except Exception:
                logger.exception("Failed to load tool entry point: %s", ep.name)
        return count
