"""Plugin registry: discovery, dependency resolution, lifecycle management, and search."""

from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from collections import defaultdict, deque
from typing import TYPE_CHECKING, Any

from agent33.plugins.loader import load_manifest
from agent33.plugins.models import PluginState
from agent33.plugins.version import satisfies_constraint

if TYPE_CHECKING:
    from pathlib import Path

    from agent33.plugins.base import PluginBase
    from agent33.plugins.manifest import PluginManifest

logger = logging.getLogger(__name__)


class PluginConflictError(Exception):
    """Raised when two plugins conflict (same name, incompatible versions)."""


class PluginDependencyError(Exception):
    """Raised when plugin dependencies cannot be resolved."""


class CyclicDependencyError(PluginDependencyError):
    """Raised when plugins have circular dependencies."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        super().__init__(f"Cyclic plugin dependency: {' -> '.join(cycle)}")


class PluginEntry:
    """Internal tracking entry for a discovered/loaded plugin."""

    __slots__ = ("manifest", "state", "instance", "error", "plugin_dir")

    def __init__(self, manifest: PluginManifest, plugin_dir: Path) -> None:
        self.manifest = manifest
        self.plugin_dir = plugin_dir
        self.state = PluginState.DISCOVERED
        self.instance: PluginBase | None = None
        self.error: str | None = None


class PluginRegistry:
    """Central registry for plugin discovery, lifecycle, and management.

    Discovery flow:
    1. Scan plugin directories for manifest files (plugin.yaml/toml/PLUGIN.md)
    2. Parse manifests and validate against PluginManifest schema
    3. Resolve dependencies via topological sort (Kahn's algorithm)
    4. Load plugins in dependency order
    5. Enable plugins that are marked active

    This follows the same patterns as:
    - SkillRegistry.discover() for directory scanning
    - DAGBuilder for topological dependency resolution
    - AgentRegistry for in-memory CRUD
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PluginEntry] = {}

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self, path: Path) -> int:
        """Scan a directory for plugin manifests.

        Each subdirectory is checked for plugin.yaml, plugin.toml,
        or PLUGIN.md. Returns the number of plugins discovered.

        This only parses manifests -- it does not load or enable plugins.
        Call load_all() or load(name) afterwards.
        """
        if not path.is_dir():
            logger.warning("Plugin directory not found: %s", path)
            return 0

        discovered = 0
        for entry in sorted(path.iterdir()):
            if not entry.is_dir():
                continue
            try:
                manifest = load_manifest(entry)
                if manifest.name in self._plugins:
                    existing = self._plugins[manifest.name]
                    logger.warning(
                        "Plugin '%s' v%s already discovered (existing: v%s from %s)",
                        manifest.name,
                        manifest.version,
                        existing.manifest.version,
                        existing.plugin_dir,
                    )
                    continue
                self._plugins[manifest.name] = PluginEntry(manifest, entry)
                discovered += 1
                logger.info(
                    "Discovered plugin: %s v%s from %s",
                    manifest.name,
                    manifest.version,
                    entry,
                )
            except FileNotFoundError:
                # Directory has no manifest -- not a plugin, skip silently
                pass
            except Exception:
                logger.warning("Failed to discover plugin from %s", entry, exc_info=True)

        return discovered

    # ------------------------------------------------------------------
    # Dependency Resolution (Kahn's algorithm)
    # ------------------------------------------------------------------

    def resolve_load_order(self) -> list[str]:
        """Compute the topological load order for all discovered plugins.

        Uses Kahn's algorithm (same as workflows/dag.py DAGBuilder).
        Raises CyclicDependencyError if circular dependencies exist.
        Raises PluginDependencyError if required dependencies are missing.
        """
        # Validate all required dependencies exist
        for name, entry in self._plugins.items():
            for dep in entry.manifest.dependencies:
                if not dep.optional and dep.name not in self._plugins:
                    raise PluginDependencyError(
                        f"Plugin '{name}' requires '{dep.name}' which is not discovered."
                    )

        # Build adjacency list (dependency -> dependent)
        adjacency: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = {name: 0 for name in self._plugins}

        for name, entry in self._plugins.items():
            for dep in entry.manifest.dependencies:
                if dep.name in self._plugins:
                    adjacency[dep.name].append(name)
                    in_degree[name] += 1

        # Kahn's algorithm
        queue: deque[str] = deque(name for name, deg in in_degree.items() if deg == 0)
        order: list[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self._plugins):
            # Cycle detected -- find the involved nodes for error message
            visited = set(order)
            remaining = [n for n in self._plugins if n not in visited]
            raise CyclicDependencyError(remaining + [remaining[0]])

        return order

    # ------------------------------------------------------------------
    # Version Constraint Checking
    # ------------------------------------------------------------------

    def check_version_constraints(self) -> list[str]:
        """Validate all version constraints between plugins.

        Returns a list of violation descriptions (empty if all OK).
        """
        violations: list[str] = []
        for name, entry in self._plugins.items():
            for dep in entry.manifest.dependencies:
                if dep.name not in self._plugins:
                    if not dep.optional:
                        violations.append(f"Plugin '{name}' requires missing plugin '{dep.name}'")
                    continue

                dep_entry = self._plugins[dep.name]
                if dep.version_constraint != "*" and not satisfies_constraint(
                    dep_entry.manifest.version, dep.version_constraint
                ):
                    violations.append(
                        f"Plugin '{name}' requires '{dep.name}' "
                        f"{dep.version_constraint} but found "
                        f"{dep_entry.manifest.version}"
                    )
        return violations

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    async def load_all(self, context_factory: Any) -> int:
        """Load all discovered plugins in dependency order.

        context_factory is a callable(manifest, plugin_dir) -> PluginContext.
        Returns the number of successfully loaded plugins.
        """
        order = self.resolve_load_order()
        loaded = 0
        for name in order:
            try:
                await self.load(name, context_factory)
                loaded += 1
            except Exception:
                logger.warning("Failed to load plugin '%s'", name, exc_info=True)
        return loaded

    async def load(self, name: str, context_factory: Any) -> None:
        """Load a single plugin: instantiate class, call on_load().

        Raises KeyError if plugin not discovered.
        """
        entry = self._plugins.get(name)
        if entry is None:
            raise KeyError(f"Plugin '{name}' not discovered")

        if entry.state not in (PluginState.DISCOVERED, PluginState.UNLOADED):
            logger.info("Plugin '%s' already in state %s, skipping load", name, entry.state)
            return

        entry.state = PluginState.LOADING
        try:
            # Create scoped context
            context = context_factory(entry.manifest, entry.plugin_dir)

            # Import and instantiate plugin class
            module_path, class_name = entry.manifest.entry_point.rsplit(":", 1)

            # Use spec_from_file_location to load plugin modules from their
            # specific directories. This avoids module cache collisions when
            # multiple plugins use the same module name (e.g. "plugin").
            module_file = entry.plugin_dir / (module_path.replace(".", "/") + ".py")
            unique_module_name = f"agent33.plugins._loaded.{name}.{module_path}"

            if module_file.is_file():
                spec = importlib.util.spec_from_file_location(unique_module_name, str(module_file))
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot create module spec for {module_file}")
                module = importlib.util.module_from_spec(spec)
                sys.modules[unique_module_name] = module
                spec.loader.exec_module(module)
            else:
                # Fallback: try standard import (for installed packages)
                plugin_dir_str = str(entry.plugin_dir)
                path_added = False
                if plugin_dir_str not in sys.path:
                    sys.path.insert(0, plugin_dir_str)
                    path_added = True
                try:
                    module = importlib.import_module(module_path)
                finally:
                    if path_added and plugin_dir_str in sys.path:
                        sys.path.remove(plugin_dir_str)

            plugin_class = getattr(module, class_name)

            instance = plugin_class(entry.manifest, context)

            # Call on_load lifecycle
            await instance.on_load()

            entry.instance = instance
            entry.state = PluginState.LOADED
            logger.info("Loaded plugin: %s v%s", name, entry.manifest.version)
        except Exception as exc:
            entry.state = PluginState.ERROR
            entry.error = str(exc)
            raise

    # ------------------------------------------------------------------
    # Enable / Disable
    # ------------------------------------------------------------------

    async def enable(self, name: str) -> None:
        """Enable a loaded plugin: call on_enable(), make contributions active."""
        entry = self._plugins.get(name)
        if entry is None:
            raise KeyError(f"Plugin '{name}' not discovered")

        if entry.state not in (PluginState.LOADED, PluginState.DISABLED):
            raise RuntimeError(
                f"Cannot enable plugin '{name}' in state {entry.state}. "
                f"Must be LOADED or DISABLED."
            )

        entry.state = PluginState.ENABLING
        try:
            if entry.instance is not None:
                await entry.instance.on_enable()
            entry.state = PluginState.ACTIVE
            logger.info("Enabled plugin: %s", name)
        except Exception as exc:
            entry.state = PluginState.ERROR
            entry.error = str(exc)
            raise

    async def disable(self, name: str) -> None:
        """Disable an active plugin: call on_disable(), remove hooks."""
        entry = self._plugins.get(name)
        if entry is None:
            raise KeyError(f"Plugin '{name}' not discovered")

        if entry.state != PluginState.ACTIVE:
            raise RuntimeError(
                f"Cannot disable plugin '{name}' in state {entry.state}. Must be ACTIVE."
            )

        entry.state = PluginState.DISABLED
        if entry.instance is not None:
            try:
                await entry.instance.on_disable()
            except Exception:
                logger.warning("Error during on_disable for plugin '%s'", name, exc_info=True)
        logger.info("Disabled plugin: %s", name)

    # ------------------------------------------------------------------
    # Unloading
    # ------------------------------------------------------------------

    async def unload(self, name: str) -> None:
        """Unload a plugin: call on_unload(), remove all contributions."""
        entry = self._plugins.get(name)
        if entry is None:
            raise KeyError(f"Plugin '{name}' not discovered")

        if entry.state == PluginState.ACTIVE:
            await self.disable(name)

        entry.state = PluginState.UNLOADING
        if entry.instance is not None:
            try:
                await entry.instance.on_unload()
            except Exception:
                logger.warning("Error during on_unload for plugin '%s'", name, exc_info=True)

        entry.instance = None
        entry.state = PluginState.UNLOADED
        logger.info("Unloaded plugin: %s", name)

    async def unload_all(self) -> None:
        """Unload all plugins in reverse dependency order."""
        try:
            order = self.resolve_load_order()
        except Exception:
            order = list(self._plugins.keys())
        for name in reversed(order):
            entry = self._plugins.get(name)
            if entry and entry.state in (
                PluginState.ACTIVE,
                PluginState.LOADED,
                PluginState.DISABLED,
            ):
                try:
                    await self.unload(name)
                except Exception:
                    logger.warning("Error unloading plugin '%s'", name, exc_info=True)

    # ------------------------------------------------------------------
    # CRUD / Query
    # ------------------------------------------------------------------

    def get(self, name: str) -> PluginEntry | None:
        """Return the entry for a plugin, or None."""
        return self._plugins.get(name)

    def get_manifest(self, name: str) -> PluginManifest | None:
        """Return the manifest for a plugin, or None."""
        entry = self._plugins.get(name)
        return entry.manifest if entry else None

    def list_all(self) -> list[PluginManifest]:
        """Return all discovered plugin manifests, sorted by name."""
        return sorted(
            [e.manifest for e in self._plugins.values()],
            key=lambda m: m.name,
        )

    def list_active(self) -> list[PluginManifest]:
        """Return manifests of all active plugins."""
        return sorted(
            [e.manifest for e in self._plugins.values() if e.state == PluginState.ACTIVE],
            key=lambda m: m.name,
        )

    def get_state(self, name: str) -> PluginState | None:
        """Return the current state of a plugin."""
        entry = self._plugins.get(name)
        return entry.state if entry else None

    @property
    def count(self) -> int:
        """Total number of discovered plugins."""
        return len(self._plugins)

    @property
    def active_count(self) -> int:
        """Number of currently active plugins."""
        return sum(1 for e in self._plugins.values() if e.state == PluginState.ACTIVE)

    def remove(self, name: str) -> bool:
        """Remove a plugin entry (must be UNLOADED or DISCOVERED)."""
        entry = self._plugins.get(name)
        if entry is None:
            return False
        if entry.state not in (PluginState.DISCOVERED, PluginState.UNLOADED):
            raise RuntimeError(
                f"Cannot remove plugin '{name}' in state {entry.state}. Unload it first."
            )
        del self._plugins[name]
        return True

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def find_by_tag(self, tag: str) -> list[PluginManifest]:
        """Find plugins that have a specific tag."""
        return [e.manifest for e in self._plugins.values() if tag in e.manifest.tags]

    def find_by_contribution(self, contribution_type: str, name: str) -> list[PluginManifest]:
        """Find plugins that contribute a specific skill/tool/agent/hook."""
        results: list[PluginManifest] = []
        for entry in self._plugins.values():
            contributions = entry.manifest.contributions
            match = (
                (contribution_type == "skills" and name in contributions.skills)
                or (contribution_type == "tools" and name in contributions.tools)
                or (contribution_type == "agents" and name in contributions.agents)
                or (contribution_type == "hooks" and name in contributions.hooks)
            )
            if match:
                results.append(entry.manifest)
        return results

    def search(self, query: str) -> list[PluginManifest]:
        """Simple text search across plugin names, descriptions, and tags."""
        query_lower = query.lower()
        results: list[PluginManifest] = []
        for entry in self._plugins.values():
            m = entry.manifest
            if (
                query_lower in m.name.lower()
                or query_lower in m.description.lower()
                or any(query_lower in t.lower() for t in m.tags)
            ):
                results.append(m)
        return sorted(results, key=lambda m: m.name)
