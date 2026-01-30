"""Agent registry -- discovers and stores agent definitions."""

from __future__ import annotations

import logging
from pathlib import Path

from agent33.agents.definition import AgentDefinition

logger = logging.getLogger(__name__)


class AgentRegistry:
    """In-memory registry of agent definitions keyed by name."""

    def __init__(self) -> None:
        self._agents: dict[str, AgentDefinition] = {}

    # -- discovery --------------------------------------------------------

    def discover(self, path: str | Path) -> int:
        """Scan *path* for .json agent definitions and load them.

        Returns the number of definitions successfully loaded.
        """
        directory = Path(path)
        if not directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        loaded = 0
        for json_file in sorted(directory.glob("*.json")):
            try:
                definition = AgentDefinition.load_from_file(json_file)
                self._agents[definition.name] = definition
                loaded += 1
                logger.info("loaded agent definition: %s (v%s)", definition.name, definition.version)
            except Exception:
                logger.exception("failed to load agent definition from %s", json_file)

        return loaded

    # -- CRUD -------------------------------------------------------------

    def register(self, definition: AgentDefinition) -> None:
        """Add or replace an agent definition."""
        self._agents[definition.name] = definition

    def get(self, name: str) -> AgentDefinition | None:
        """Return the definition for *name*, or ``None``."""
        return self._agents.get(name)

    def list_all(self) -> list[AgentDefinition]:
        """Return all registered definitions, sorted by name."""
        return sorted(self._agents.values(), key=lambda d: d.name)

    def remove(self, name: str) -> bool:
        """Remove an agent by name. Returns True if it existed."""
        return self._agents.pop(name, None) is not None

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        return name in self._agents
