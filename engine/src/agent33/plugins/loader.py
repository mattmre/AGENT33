"""Plugin discovery and loading via setuptools entry points."""

from __future__ import annotations

import importlib.metadata
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)

_PLUGIN_GROUP = "agent33.plugins"


class PluginLoader:
    """Discover plugins advertised under the ``agent33.plugins`` entry-point
    group and register their tools and adapters.

    Each plugin entry point must resolve to a callable (typically a module-level
    ``register`` function) with the signature::

        def register(registry: ToolRegistry, adapters: dict[str, Any]) -> None:
            ...

    The function receives the global tool registry and a mutable dict of
    messaging adapters so it can contribute new tools and/or adapters.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        adapter_registry: dict[str, Any] | None = None,
    ) -> None:
        self._tool_registry = tool_registry
        self._adapter_registry: dict[str, Any] = adapter_registry or {}
        self._loaded_plugins: list[str] = []

    @property
    def loaded_plugins(self) -> list[str]:
        return list(self._loaded_plugins)

    def discover_and_load(self) -> int:
        """Scan entry points and invoke each plugin's register function.

        Returns the number of plugins successfully loaded.
        """
        count = 0
        eps = importlib.metadata.entry_points()
        selected = (
            eps.select(group=_PLUGIN_GROUP)
            if hasattr(eps, "select")
            else eps.get(_PLUGIN_GROUP, [])  # type: ignore[arg-type]
        )
        for ep in selected:
            try:
                register_fn = ep.load()
                register_fn(self._tool_registry, self._adapter_registry)
                self._loaded_plugins.append(ep.name)
                count += 1
                logger.info("Loaded plugin: %s", ep.name)
            except Exception:
                logger.exception("Failed to load plugin: %s", ep.name)
        return count
