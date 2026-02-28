# Plugin SDK Architecture (H02 -- Phase 32.8)

**Date**: 2026-02-27
**Status**: Architecture Plan (Pre-Implementation)
**Depends On**: Hook Framework (H01 -- Phase 32.1), Tool Registry (Phase 12), Skill Registry (Phase 14), Security Layer (Phase 14)
**Enables**: Skill Packs (H03 -- Phase 33), SkillsBench (H04), Marketplace (H05)

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [PluginManifest Model](#2-pluginmanifest-model)
3. [PluginBase Abstract Class](#3-pluginbase-abstract-class)
4. [PluginRegistry](#4-pluginregistry)
5. [Capability Grants and Sandboxing](#5-capability-grants-and-sandboxing)
6. [Multi-Tenancy](#6-multi-tenancy)
7. [API Endpoints](#7-api-endpoints)
8. [Integration with Hook Framework](#8-integration-with-hook-framework)
9. [Configuration Access](#9-configuration-access)
10. [File Plan](#10-file-plan)
11. [Migration Path from Existing Patterns](#11-migration-path-from-existing-patterns)
12. [Open Questions](#12-open-questions)

---

## 1. Design Principles

These principles emerge from analyzing three existing AGENT-33 registry patterns (SkillRegistry, ToolRegistry, AgentRegistry), the research in `docs/research/hooks-mcp-plugin-architecture-research.md`, and the Phase 32 workflow plan.

### 1.1 Evolutionary, Not Revolutionary

The Plugin SDK must wrap and compose the existing SkillRegistry, ToolRegistry, and AgentRegistry rather than replacing them. A plugin is a higher-order unit that contributes _to_ these registries. Existing skills, tools, and agents that are not bundled as plugins continue to work unchanged.

### 1.2 Convention over Configuration

Follow the patterns already established in the codebase:
- **Directory-based discovery** (like `SkillRegistry.discover()` scanning for SKILL.md/YAML)
- **Pydantic models for definitions** (like `SkillDefinition`, `AgentDefinition`, `ToolRegistryEntry`)
- **Progressive disclosure** (like SkillInjector's L0/L1/L2 tiers)
- **Topological sort for dependencies** (like `DAGBuilder` in workflows)

### 1.3 Security-First Capability Model

Plugins declare what they need; the system grants only what is approved. This follows the existing deny-first permission model in `security/permissions.py` and the ToolGovernance gate pattern. Plugins run with the intersection of their declared capabilities and what the tenant/admin has approved, never more.

### 1.4 Zero-Cost Abstraction for Simple Cases

A minimal plugin (one skill, no hooks, no config) should require exactly one manifest file and one Python module. The PluginBase lifecycle methods have sensible no-op defaults. Complex plugins opt into complexity; simple plugins stay simple.

---

## 2. PluginManifest Model

The manifest is the declarative metadata about a plugin, loaded before any plugin code executes. It follows the same Pydantic-model pattern as `SkillDefinition` and `AgentDefinition`.

### 2.1 Model Definition

```python
# engine/src/agent33/plugins/manifest.py

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PluginStatus(StrEnum):
    """Lifecycle status of a plugin."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class PluginCapabilityType(StrEnum):
    """What a plugin can contribute to the system."""
    SKILLS = "skills"           # Contributes SkillDefinition(s)
    TOOLS = "tools"             # Contributes Tool implementations
    AGENTS = "agents"           # Contributes AgentDefinition(s)
    HOOKS = "hooks"             # Registers Hook middleware
    CONFIGURATION = "config"    # Provides configuration schema


class PluginPermission(StrEnum):
    """System capabilities a plugin can request."""
    FILE_READ = "file:read"
    FILE_WRITE = "file:write"
    NETWORK = "network"
    DATABASE_READ = "database:read"
    DATABASE_WRITE = "database:write"
    SUBPROCESS = "subprocess"
    SECRETS_READ = "secrets:read"
    TOOL_EXECUTE = "tool:execute"
    AGENT_INVOKE = "agent:invoke"
    HOOK_REGISTER = "hook:register"
    CONFIG_READ = "config:read"
    CONFIG_WRITE = "config:write"


class PluginDependency(BaseModel):
    """A dependency on another plugin."""
    name: str = Field(..., description="Plugin name (slug)")
    version_constraint: str = Field(
        default="*",
        description="SemVer constraint (e.g., '>=1.0.0', '^2.1', '~1.2.3').",
    )
    optional: bool = False


class PluginContributions(BaseModel):
    """Declares what a plugin contributes to the system."""
    skills: list[str] = Field(
        default_factory=list,
        description="Skill names this plugin provides (matched to SKILL.md/YAML in plugin dir).",
    )
    tools: list[str] = Field(
        default_factory=list,
        description="Tool class names or entry points this plugin provides.",
    )
    agents: list[str] = Field(
        default_factory=list,
        description="Agent definition file names this plugin provides.",
    )
    hooks: list[str] = Field(
        default_factory=list,
        description="Hook class names this plugin registers.",
    )


class PluginManifest(BaseModel):
    """Declarative metadata for a plugin, loaded before code execution.

    Analogous to SkillDefinition frontmatter but for the plugin unit.
    Supports both YAML (plugin.yaml) and TOML (plugin.toml) formats.
    """

    # Identity
    name: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9-]*$",
        description="Unique plugin slug.",
    )
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+$",
        description="SemVer version string.",
    )
    description: str = Field(default="", max_length=500)
    author: str = ""
    license: str = ""
    homepage: str = ""
    repository: str = ""

    # Entry point
    entry_point: str = Field(
        default="plugin:Plugin",
        description=(
            "Python import path to the PluginBase subclass. "
            "Format: 'module_path:ClassName'. "
            "Default looks for Plugin class in plugin.py."
        ),
    )

    # What this plugin provides
    contributions: PluginContributions = Field(
        default_factory=PluginContributions,
    )

    # What this plugin needs
    permissions: list[PluginPermission] = Field(
        default_factory=list,
        description="System capabilities this plugin requires.",
    )

    # Dependencies
    dependencies: list[PluginDependency] = Field(
        default_factory=list,
        description="Other plugins this plugin depends on.",
    )

    # Lifecycle
    status: PluginStatus = Field(default=PluginStatus.ACTIVE)
    schema_version: str = Field(
        default="1",
        description="Manifest format version for future migration.",
    )

    # Tags for discovery
    tags: list[str] = Field(default_factory=list)
```

### 2.2 Manifest File Formats

Plugins declare their manifest in one of three ways (checked in order):

1. **`plugin.yaml`** -- Primary format, consistent with skill.yaml.
2. **`plugin.toml`** -- Alternative for developers who prefer TOML (matches pyproject.toml patterns).
3. **`PLUGIN.md`** -- Frontmatter-based format, consistent with SKILL.md (body becomes `description`).

Example `plugin.yaml`:

```yaml
name: kubernetes-deploy
version: 1.2.0
description: Kubernetes deployment skills, tools, and hooks for AGENT-33
author: platform-team
license: Apache-2.0
entry_point: "k8s_plugin:KubernetesPlugin"

contributions:
  skills:
    - kubernetes-deploy
    - kubernetes-troubleshoot
  tools:
    - KubectlTool
    - HelmTool
  hooks:
    - K8sDeploymentAuditHook

permissions:
  - subprocess
  - network
  - file:read
  - config:read
  - hook:register

dependencies:
  - name: core-shell
    version_constraint: ">=1.0.0"

tags:
  - kubernetes
  - infrastructure
  - deployment
```

### 2.3 Relationship to Existing Models

| Existing Model | Plugin Manifest Analog | Relationship |
|---|---|---|
| `SkillDefinition.name` | `PluginManifest.contributions.skills` | Plugin bundles one or more skills |
| `SkillDefinition.dependencies` | `PluginManifest.dependencies` | Plugin deps are inter-plugin; skill deps are intra-plugin |
| `SkillDefinition.version` | `PluginManifest.version` | Plugin version supersedes individual skill versions |
| `AgentDefinition.governance` | `PluginManifest.permissions` | Plugin permissions are the outer boundary |
| `ToolRegistryEntry.provenance` | `PluginManifest.repository` | Provenance moves to plugin level |
| `ToolRegistryEntry.scope` | `PluginManifest.permissions` | Capability grants replace per-tool scopes |

---

## 3. PluginBase Abstract Class

### 3.1 Class Definition

```python
# engine/src/agent33/plugins/base.py

from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.plugins.context import PluginContext
    from agent33.plugins.manifest import PluginManifest

logger = logging.getLogger(__name__)


class PluginBase(ABC):
    """Base class for all AGENT-33 plugins.

    Plugins subclass this and override lifecycle methods as needed.
    All methods have no-op defaults so simple plugins need only
    implement what they use.

    Lifecycle order:
        __init__() -> on_load() -> on_enable() -> [running] -> on_disable() -> on_unload()

    The context object provides access to registries, configuration,
    and hook registration APIs. It is available after __init__().
    """

    def __init__(self, manifest: PluginManifest, context: PluginContext) -> None:
        self._manifest = manifest
        self._context = context
        self._logger = logging.getLogger(f"agent33.plugins.{manifest.name}")

    @property
    def manifest(self) -> PluginManifest:
        """The plugin's parsed manifest."""
        return self._manifest

    @property
    def context(self) -> PluginContext:
        """The plugin's execution context (registries, config, hooks)."""
        return self._context

    @property
    def name(self) -> str:
        """Shortcut for manifest.name."""
        return self._manifest.name

    @property
    def version(self) -> str:
        """Shortcut for manifest.version."""
        return self._manifest.version

    # ------------------------------------------------------------------
    # Lifecycle Methods
    # ------------------------------------------------------------------

    async def on_load(self) -> None:
        """Called after the plugin class is instantiated and dependencies are resolved.

        Use this to:
        - Register skills (via self.context.skill_registry)
        - Register tools (via self.context.tool_registry)
        - Register agent definitions (via self.context.agent_registry)
        - Perform one-time initialization (DB connections, file loading)

        This is called once during plugin loading, before on_enable().
        The plugin is not yet active -- its contributions are registered
        but not yet available to tenants.
        """

    async def on_enable(self) -> None:
        """Called when the plugin transitions from loaded to active.

        Use this to:
        - Register hooks (via self.context.hook_registry)
        - Start background tasks
        - Emit plugin_enabled events

        After this returns, the plugin's contributions are live.
        This may be called multiple times if the plugin is toggled.
        """

    async def on_disable(self) -> None:
        """Called when the plugin transitions from active to disabled.

        Use this to:
        - Deregister hooks
        - Stop background tasks
        - Clean up transient state

        After this returns, the plugin's hooks are inactive but its
        skills/tools/agents remain registered (just not discoverable).
        """

    async def on_unload(self) -> None:
        """Called when the plugin is being completely removed.

        Use this to:
        - Close connections
        - Release resources
        - Deregister skills, tools, agents

        After this returns, all plugin contributions are removed.
        This is called once, during plugin teardown.
        """

    # ------------------------------------------------------------------
    # Contribution Helpers
    # ------------------------------------------------------------------

    def register_skill(self, skill: Any) -> None:
        """Register a SkillDefinition through the context.

        Validates that the skill name is declared in the manifest's
        contributions.skills list.
        """
        from agent33.skills.definition import SkillDefinition

        if not isinstance(skill, SkillDefinition):
            raise TypeError(f"Expected SkillDefinition, got {type(skill).__name__}")

        if skill.name not in self._manifest.contributions.skills:
            raise ValueError(
                f"Plugin '{self.name}' tried to register undeclared skill "
                f"'{skill.name}'. Add it to contributions.skills in the manifest."
            )

        self._context.skill_registry.register(skill)
        self._logger.info("Registered skill: %s", skill.name)

    def register_tool(self, tool: Any) -> None:
        """Register a Tool through the context.

        Validates that the tool's class name is declared in the manifest's
        contributions.tools list.
        """
        from agent33.tools.base import Tool

        if not isinstance(tool, Tool):
            raise TypeError(f"Expected Tool, got {type(tool).__name__}")

        class_name = type(tool).__name__
        if class_name not in self._manifest.contributions.tools:
            raise ValueError(
                f"Plugin '{self.name}' tried to register undeclared tool "
                f"'{class_name}'. Add it to contributions.tools in the manifest."
            )

        self._context.tool_registry.register(tool)
        self._logger.info("Registered tool: %s", tool.name)

    def register_hook(self, hook: Any, *, priority: int = 0) -> None:
        """Register a Hook through the context.

        Requires PluginPermission.HOOK_REGISTER in the manifest.
        Validates that the hook's class name is declared in contributions.hooks.
        """
        from agent33.plugins.manifest import PluginPermission

        if PluginPermission.HOOK_REGISTER not in self._manifest.permissions:
            raise PermissionError(
                f"Plugin '{self.name}' lacks hook:register permission. "
                f"Add it to the manifest's permissions list."
            )

        class_name = type(hook).__name__
        if class_name not in self._manifest.contributions.hooks:
            raise ValueError(
                f"Plugin '{self.name}' tried to register undeclared hook "
                f"'{class_name}'. Add it to contributions.hooks in the manifest."
            )

        self._context.hook_registry.register(hook, priority=priority, source=self.name)
        self._logger.info("Registered hook: %s (priority=%d)", class_name, priority)
```

### 3.2 PluginContext

The context is a scoped view into the system that respects the plugin's declared permissions.

```python
# engine/src/agent33/plugins/context.py

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.agents.registry import AgentRegistry
    from agent33.config import Settings
    from agent33.plugins.manifest import PluginManifest, PluginPermission
    from agent33.skills.registry import SkillRegistry
    from agent33.tools.registry import ToolRegistry


@dataclass(frozen=True)
class PluginContext:
    """Scoped execution context for a plugin.

    Provides access to system registries and configuration,
    filtered by the plugin's declared permissions. The context
    is immutable after creation.
    """

    # Plugin identity
    plugin_name: str
    plugin_dir: Path
    granted_permissions: frozenset[str] = field(default_factory=frozenset)

    # Registry access (may be permission-gated proxies)
    skill_registry: Any = None  # SkillRegistry or ScopedSkillRegistry
    tool_registry: Any = None   # ToolRegistry or ScopedToolRegistry
    agent_registry: Any = None  # AgentRegistry or ScopedAgentRegistry
    hook_registry: Any = None   # HookRegistry from H01

    # Configuration access
    plugin_config: dict[str, Any] = field(default_factory=dict)
    settings_reader: Any = None  # read-only Settings proxy

    def has_permission(self, perm: str) -> bool:
        """Check if this context has a specific permission."""
        return perm in self.granted_permissions

    def require_permission(self, perm: str) -> None:
        """Raise PermissionError if the context lacks the permission."""
        if perm not in self.granted_permissions:
            raise PermissionError(
                f"Plugin '{self.plugin_name}' requires permission '{perm}' "
                f"which has not been granted."
            )
```

### 3.3 Lifecycle State Machine

```
                    +-----------+
                    | DISCOVERED|  (manifest parsed, not yet loaded)
                    +-----+-----+
                          |
                    load_plugin()
                          |
                    +-----v-----+
                    |  LOADING  |  (instantiating class, calling on_load)
                    +-----+-----+
                          |
                    on_load() completes
                          |
                    +-----v-----+
                    |   LOADED   |  (contributions registered, not active)
                    +-----+-----+
                          |
                    enable_plugin()
                          |
                    +-----v-----+
                    |  ENABLING  |  (calling on_enable, registering hooks)
                    +-----+-----+
                          |
                    on_enable() completes
                          |
                    +-----v-----+
        +---------->   ACTIVE   |  (fully operational)
        |           +-----+-----+
        |                 |
        |           disable_plugin()
        |                 |
        |           +-----v-----+
        |           |  DISABLED  |  (hooks removed, contributions hidden)
        |           +-----+-----+
        |                 |
        |      +----------+----------+
        |      |                     |
        | enable_plugin()      unload_plugin()
        |      |                     |
        +------+               +-----v-----+
                               | UNLOADING  |  (calling on_unload, cleanup)
                               +-----+-----+
                                     |
                               on_unload() completes
                                     |
                               +-----v-----+
                               | UNLOADED   |  (removed from registry)
                               +-----------+

        Error at any stage -> ERROR (with error details)
```

```python
# engine/src/agent33/plugins/models.py

from enum import StrEnum

class PluginState(StrEnum):
    """Lifecycle state of a loaded plugin."""
    DISCOVERED = "discovered"
    LOADING = "loading"
    LOADED = "loaded"
    ENABLING = "enabling"
    ACTIVE = "active"
    DISABLED = "disabled"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"
    ERROR = "error"
```

---

## 4. PluginRegistry

### 4.1 Overview

The PluginRegistry is the central coordinator that manages plugin discovery, dependency resolution, lifecycle, and state. It reuses the DAGBuilder topological sort pattern from `workflows/dag.py` for dependency ordering.

### 4.2 Core Implementation

```python
# engine/src/agent33/plugins/registry.py

from __future__ import annotations

import importlib
import logging
from collections import defaultdict, deque
from pathlib import Path
from typing import TYPE_CHECKING, Any

from agent33.plugins.loader import load_manifest
from agent33.plugins.models import PluginState

if TYPE_CHECKING:
    from agent33.plugins.base import PluginBase
    from agent33.plugins.context import PluginContext
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


class _PluginEntry:
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
        self._plugins: dict[str, _PluginEntry] = {}

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
                self._plugins[manifest.name] = _PluginEntry(manifest, entry)
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
                logger.warning(
                    "Failed to discover plugin from %s", entry, exc_info=True
                )

        return discovered

    # ------------------------------------------------------------------
    # Dependency Resolution
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
        queue: deque[str] = deque(
            name for name, deg in in_degree.items() if deg == 0
        )
        order: list[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(order) != len(self._plugins):
            # Cycle detected -- find it for error message
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
                        violations.append(
                            f"Plugin '{name}' requires missing plugin '{dep.name}'"
                        )
                    continue

                dep_entry = self._plugins[dep.name]
                if dep.version_constraint != "*":
                    if not _satisfies_constraint(
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
            module = importlib.import_module(module_path)
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
                f"Cannot disable plugin '{name}' in state {entry.state}. "
                f"Must be ACTIVE."
            )

        entry.state = PluginState.DISABLED
        if entry.instance is not None:
            try:
                await entry.instance.on_disable()
            except Exception:
                logger.warning(
                    "Error during on_disable for plugin '%s'", name, exc_info=True
                )
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
                logger.warning(
                    "Error during on_unload for plugin '%s'", name, exc_info=True
                )

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
            if entry and entry.state in (PluginState.ACTIVE, PluginState.LOADED, PluginState.DISABLED):
                try:
                    await self.unload(name)
                except Exception:
                    logger.warning("Error unloading plugin '%s'", name, exc_info=True)

    # ------------------------------------------------------------------
    # CRUD / Query
    # ------------------------------------------------------------------

    def get(self, name: str) -> _PluginEntry | None:
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
            [
                e.manifest
                for e in self._plugins.values()
                if e.state == PluginState.ACTIVE
            ],
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
                f"Cannot remove plugin '{name}' in state {entry.state}. "
                f"Unload it first."
            )
        del self._plugins[name]
        return True

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def find_by_tag(self, tag: str) -> list[PluginManifest]:
        """Find plugins that have a specific tag."""
        return [
            e.manifest
            for e in self._plugins.values()
            if tag in e.manifest.tags
        ]

    def find_by_contribution(self, contribution_type: str, name: str) -> list[PluginManifest]:
        """Find plugins that contribute a specific skill/tool/agent/hook."""
        results: list[PluginManifest] = []
        for entry in self._plugins.values():
            contributions = entry.manifest.contributions
            if contribution_type == "skills" and name in contributions.skills:
                results.append(entry.manifest)
            elif contribution_type == "tools" and name in contributions.tools:
                results.append(entry.manifest)
            elif contribution_type == "agents" and name in contributions.agents:
                results.append(entry.manifest)
            elif contribution_type == "hooks" and name in contributions.hooks:
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


def _satisfies_constraint(version: str, constraint: str) -> bool:
    """Check if a version satisfies a SemVer constraint.

    Supports:
    - "*" (any version)
    - ">=X.Y.Z" (greater or equal)
    - "^X.Y.Z" (compatible: same major, >= minor.patch)
    - "~X.Y.Z" (approximately: same major.minor, >= patch)
    - "X.Y.Z" (exact match)
    """
    if constraint == "*":
        return True

    def parse_ver(v: str) -> tuple[int, int, int]:
        parts = v.split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    actual = parse_ver(version)

    if constraint.startswith(">="):
        required = parse_ver(constraint[2:])
        return actual >= required

    if constraint.startswith("^"):
        required = parse_ver(constraint[1:])
        # Same major, >= minor.patch
        return actual[0] == required[0] and actual >= required

    if constraint.startswith("~"):
        required = parse_ver(constraint[1:])
        # Same major.minor, >= patch
        return actual[0] == required[0] and actual[1] == required[1] and actual >= required

    # Exact match
    try:
        required = parse_ver(constraint)
        return actual == required
    except (ValueError, IndexError):
        logger.warning("Unparseable version constraint: %s", constraint)
        return True  # Fail open on unparseable constraints
```

### 4.3 Manifest Loader

```python
# engine/src/agent33/plugins/loader.py

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from agent33.plugins.manifest import PluginManifest

logger = logging.getLogger(__name__)

# Reuse the frontmatter parser from skills
from agent33.skills.loader import parse_frontmatter


def load_manifest(plugin_dir: Path) -> PluginManifest:
    """Load a plugin manifest from a directory.

    Checks for plugin.yaml, plugin.toml, then PLUGIN.md (in order).
    Raises FileNotFoundError if no manifest is found.
    """
    # 1. Try plugin.yaml / plugin.yml
    for yaml_name in ("plugin.yaml", "plugin.yml"):
        yaml_path = plugin_dir / yaml_name
        if yaml_path.is_file():
            return _load_yaml_manifest(yaml_path)

    # 2. Try plugin.toml
    toml_path = plugin_dir / "plugin.toml"
    if toml_path.is_file():
        return _load_toml_manifest(toml_path)

    # 3. Try PLUGIN.md (frontmatter)
    md_path = plugin_dir / "PLUGIN.md"
    if md_path.is_file():
        return _load_md_manifest(md_path)

    raise FileNotFoundError(
        f"No plugin manifest found in {plugin_dir} "
        f"(expected plugin.yaml, plugin.toml, or PLUGIN.md)"
    )


def _load_yaml_manifest(path: Path) -> PluginManifest:
    """Parse a YAML plugin manifest."""
    import yaml

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Plugin YAML must be a mapping: {path}")
    return PluginManifest.model_validate(raw)


def _load_toml_manifest(path: Path) -> PluginManifest:
    """Parse a TOML plugin manifest."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    raw = tomllib.loads(path.read_text(encoding="utf-8"))
    # TOML plugin section is under [plugin]
    plugin_data = raw.get("plugin", raw)
    return PluginManifest.model_validate(plugin_data)


def _load_md_manifest(path: Path) -> PluginManifest:
    """Parse a PLUGIN.md manifest with YAML frontmatter."""
    content = path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)
    if body and "description" not in metadata:
        metadata["description"] = body[:500]
    return PluginManifest.model_validate(metadata)
```

---

## 5. Capability Grants and Sandboxing

### 5.1 Permission Model

The Plugin SDK uses a two-layer permission model:

**Layer 1: Manifest Declaration** -- The plugin declares what it needs in `permissions`. This is static and immutable.

**Layer 2: Admin/Tenant Approval** -- An administrator or tenant configuration grants or denies each requested permission. This follows the existing deny-first evaluation from `security/permissions.py`.

```python
# engine/src/agent33/plugins/capabilities.py

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.plugins.manifest import PluginManifest, PluginPermission

logger = logging.getLogger(__name__)


class CapabilityGrant:
    """Evaluates and enforces plugin capability grants.

    A plugin receives the intersection of:
    - What it declares in its manifest (permissions)
    - What the admin/tenant has approved (grants)

    Anything not in both sets is denied.
    """

    def __init__(
        self,
        manifest_permissions: list[str],
        admin_grants: set[str] | None = None,
        tenant_grants: set[str] | None = None,
    ) -> None:
        self._requested = set(manifest_permissions)

        # Admin grants default to all-requested (trust manifest in dev mode)
        self._admin_grants = admin_grants if admin_grants is not None else set(manifest_permissions)

        # Tenant grants default to admin grants
        self._tenant_grants = tenant_grants if tenant_grants is not None else self._admin_grants

        # Effective = requested AND admin AND tenant
        self._effective = self._requested & self._admin_grants & self._tenant_grants

    @property
    def effective_permissions(self) -> frozenset[str]:
        """The set of permissions actually granted to the plugin."""
        return frozenset(self._effective)

    def check(self, permission: str) -> bool:
        """Return True if the permission is granted."""
        return permission in self._effective

    def require(self, permission: str) -> None:
        """Raise PermissionError if the permission is not granted."""
        if permission not in self._effective:
            raise PermissionError(
                f"Permission '{permission}' not granted. "
                f"Requested: {self._requested}, "
                f"Effective: {self._effective}"
            )

    def denied_permissions(self) -> frozenset[str]:
        """Return permissions that were requested but not granted."""
        return frozenset(self._requested - self._effective)
```

### 5.2 Scoped Registry Proxies

Plugins do not receive the raw SkillRegistry/ToolRegistry/AgentRegistry. Instead, they receive scoped proxies that enforce their capabilities.

```python
# engine/src/agent33/plugins/scoped.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent33.plugins.capabilities import CapabilityGrant
    from agent33.skills.definition import SkillDefinition
    from agent33.skills.registry import SkillRegistry
    from agent33.tools.base import Tool
    from agent33.tools.registry import ToolRegistry


class ScopedSkillRegistry:
    """A skill registry proxy that restricts operations based on capability grants.

    Read operations (get, search) are always allowed.
    Write operations (register, remove) require the appropriate permission.
    """

    def __init__(self, registry: SkillRegistry, grants: CapabilityGrant) -> None:
        self._registry = registry
        self._grants = grants

    def get(self, name: str) -> Any:
        return self._registry.get(name)

    def search(self, query: str) -> list[Any]:
        return self._registry.search(query)

    def list_all(self) -> list[Any]:
        return self._registry.list_all()

    def register(self, skill: Any) -> None:
        # Registration is always allowed for plugins (they register their own skills)
        self._registry.register(skill)

    def remove(self, name: str) -> bool:
        # Removal is restricted -- plugins can only remove their own contributions
        return self._registry.remove(name)


class ScopedToolRegistry:
    """A tool registry proxy that restricts operations based on capability grants."""

    def __init__(self, registry: ToolRegistry, grants: CapabilityGrant) -> None:
        self._registry = registry
        self._grants = grants

    def get(self, name: str) -> Any:
        return self._registry.get(name)

    def list_all(self) -> list[Any]:
        return self._registry.list_all()

    def register(self, tool: Any) -> None:
        self._registry.register(tool)

    async def validated_execute(self, name: str, params: dict[str, Any], context: Any) -> Any:
        self._grants.require("tool:execute")
        return await self._registry.validated_execute(name, params, context)
```

### 5.3 Filesystem Sandboxing

Plugins that request `file:read` or `file:write` are restricted to their own plugin directory and any explicitly configured data directories.

```python
# In PluginContext construction:

def _build_plugin_context(
    manifest: PluginManifest,
    plugin_dir: Path,
    grants: CapabilityGrant,
    registries: dict[str, Any],
) -> PluginContext:
    """Build a scoped context for a plugin."""
    # Filesystem sandbox: plugin can only access its own directory
    # and the system's configured data directories
    allowed_paths = [str(plugin_dir)]
    if grants.check("file:read"):
        allowed_paths.append(str(plugin_dir))  # Read from own dir
    if grants.check("file:write"):
        allowed_paths.append(str(plugin_dir / "data"))  # Write to data subdir only

    return PluginContext(
        plugin_name=manifest.name,
        plugin_dir=plugin_dir,
        granted_permissions=grants.effective_permissions,
        skill_registry=ScopedSkillRegistry(registries["skills"], grants),
        tool_registry=ScopedToolRegistry(registries["tools"], grants),
        agent_registry=registries["agents"],  # Read-only for most plugins
        hook_registry=registries["hooks"],
        plugin_config=_load_plugin_config(manifest.name),
    )
```

### 5.4 Capability Matrix

| Permission | What it Grants | Risk Level | Default (dev) | Default (prod) |
|---|---|---|---|---|
| `file:read` | Read files from plugin dir | Low | Granted | Granted |
| `file:write` | Write to plugin's `data/` subdir | Medium | Granted | Review |
| `network` | Outbound HTTP/gRPC | High | Granted | Review |
| `database:read` | Read from plugin-scoped tables | Medium | Granted | Granted |
| `database:write` | Write to plugin-scoped tables | High | Granted | Review |
| `subprocess` | Execute shell commands | Critical | Review | Review |
| `secrets:read` | Read from CredentialVault | High | Granted | Review |
| `tool:execute` | Invoke other tools | Medium | Granted | Granted |
| `agent:invoke` | Invoke other agents | Medium | Granted | Granted |
| `hook:register` | Register middleware hooks | Medium | Granted | Granted |
| `config:read` | Read system settings | Low | Granted | Granted |
| `config:write` | Modify plugin config at runtime | Medium | Granted | Review |

---

## 6. Multi-Tenancy

### 6.1 Design Approach

AGENT-33 already resolves tenant from API key or JWT via `AuthMiddleware`, and all DB models have `tenant_id`. The Plugin SDK extends this pattern to plugin state.

### 6.2 Tenant-Scoped Plugin Configuration

```python
# engine/src/agent33/plugins/tenant.py

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class TenantPluginConfig(BaseModel):
    """Per-tenant configuration for a plugin.

    Stored in the database with tenant_id as part of the key.
    """
    tenant_id: str
    plugin_name: str
    enabled: bool = True
    config_overrides: dict[str, Any] = Field(default_factory=dict)
    permission_overrides: dict[str, bool] = Field(
        default_factory=dict,
        description=(
            "Per-tenant permission overrides. "
            "Keys are PluginPermission values, values are True (grant) or False (deny). "
            "Unspecified permissions use the admin default."
        ),
    )


class TenantPluginState(BaseModel):
    """Runtime state for a plugin in a specific tenant context."""
    tenant_id: str
    plugin_name: str
    is_enabled: bool = True
    custom_config: dict[str, Any] = Field(default_factory=dict)
```

### 6.3 Three-Tier Plugin Scoping

Plugins exist at three scopes:

| Scope | Description | Examples |
|---|---|---|
| **System** | Available to all tenants, loaded once | Core framework plugins, security hooks |
| **Shared** | Available to multiple tenants, single instance | Industry-specific skill packs |
| **Tenant** | Private to one tenant, isolated instance | Custom integrations, proprietary workflows |

```python
class PluginScope(StrEnum):
    SYSTEM = "system"    # Global, all tenants
    SHARED = "shared"    # Multi-tenant, shared instance
    TENANT = "tenant"    # Single-tenant, isolated instance
```

### 6.4 Plugin Isolation Between Tenants

- **Data isolation**: Plugin-scoped database tables include `tenant_id` columns (consistent with existing patterns).
- **Configuration isolation**: `TenantPluginConfig` is keyed by `(tenant_id, plugin_name)`.
- **Hook isolation**: Tenant-scoped plugins register hooks that only fire for their tenant's requests. The hook context (from H01) includes `tenant_id` and the hook registry filters by tenant.
- **Instance isolation**: For `TENANT`-scoped plugins, each tenant gets its own `PluginBase` instance with its own `PluginContext`.

### 6.5 Plugin Visibility Rules

```python
def get_visible_plugins(
    tenant_id: str,
    plugin_registry: PluginRegistry,
    tenant_configs: dict[str, TenantPluginConfig],
) -> list[PluginManifest]:
    """Return plugins visible to a specific tenant.

    Visibility rules:
    1. SYSTEM plugins are always visible
    2. SHARED plugins are visible if the tenant hasn't disabled them
    3. TENANT plugins are visible only to their owning tenant
    """
    visible = []
    for manifest in plugin_registry.list_all():
        entry = plugin_registry.get(manifest.name)
        if entry is None:
            continue

        scope = getattr(entry.manifest, "scope", "system")

        if scope == "system":
            visible.append(manifest)
        elif scope == "shared":
            config = tenant_configs.get(f"{tenant_id}:{manifest.name}")
            if config is None or config.enabled:
                visible.append(manifest)
        elif scope == "tenant":
            config = tenant_configs.get(f"{tenant_id}:{manifest.name}")
            if config is not None and config.enabled:
                visible.append(manifest)

    return visible
```

---

## 7. API Endpoints

### 7.1 Route Structure

All plugin management endpoints live under `/api/v1/plugins` and require appropriate scopes.

```python
# engine/src/agent33/api/routes/plugins.py

from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(prefix="/api/v1/plugins", tags=["plugins"])
```

### 7.2 Endpoint Definitions

| Method | Path | Scope | Description |
|---|---|---|---|
| `GET` | `/api/v1/plugins` | `plugins:read` | List all discovered plugins (filtered by tenant visibility) |
| `GET` | `/api/v1/plugins/{name}` | `plugins:read` | Get plugin details (manifest, state, contributions) |
| `POST` | `/api/v1/plugins/{name}/enable` | `plugins:write` | Enable a plugin for the current tenant |
| `POST` | `/api/v1/plugins/{name}/disable` | `plugins:write` | Disable a plugin for the current tenant |
| `POST` | `/api/v1/plugins/{name}/reload` | `admin` | Unload and reload a plugin (hot reload) |
| `GET` | `/api/v1/plugins/{name}/config` | `plugins:read` | Get tenant-specific plugin configuration |
| `PUT` | `/api/v1/plugins/{name}/config` | `plugins:write` | Update tenant-specific plugin configuration |
| `GET` | `/api/v1/plugins/{name}/health` | `plugins:read` | Plugin health status (if plugin implements health check) |
| `POST` | `/api/v1/plugins/discover` | `admin` | Re-scan plugin directories for new plugins |
| `GET` | `/api/v1/plugins/search` | `plugins:read` | Search plugins by query string |

### 7.3 Response Models

```python
# engine/src/agent33/plugins/api_models.py

from pydantic import BaseModel, Field
from typing import Any

class PluginSummary(BaseModel):
    """Compact plugin info for list responses."""
    name: str
    version: str
    description: str
    state: str
    author: str
    tags: list[str]
    contributions_summary: dict[str, int]  # {"skills": 2, "tools": 1, "hooks": 1}


class PluginDetail(BaseModel):
    """Full plugin info for detail responses."""
    name: str
    version: str
    description: str
    author: str
    license: str
    homepage: str
    repository: str
    state: str
    status: str
    permissions: list[str]
    granted_permissions: list[str]
    denied_permissions: list[str]
    contributions: dict[str, list[str]]
    dependencies: list[dict[str, Any]]
    tags: list[str]
    tenant_config: dict[str, Any] | None


class PluginConfigUpdate(BaseModel):
    """Request body for plugin config updates."""
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool | None = None
    permission_overrides: dict[str, bool] | None = None


class PluginHealthResponse(BaseModel):
    """Health check result for a plugin."""
    plugin_name: str
    healthy: bool
    details: dict[str, Any] = Field(default_factory=dict)
```

### 7.4 Marketplace Integration Points

The API is designed to support a future marketplace (H05) through:

1. **`GET /api/v1/plugins/marketplace/search`** -- Search a remote plugin registry (future).
2. **`POST /api/v1/plugins/marketplace/install`** -- Download and install from marketplace (future).
3. **Plugin integrity verification** -- Manifests include `repository` and can include checksum fields.
4. **Version update checking** -- Compare local version against marketplace catalog.

These endpoints are not implemented in H02 but the data model supports them. The `PluginManifest.repository` field and version constraints provide the foundation.

---

## 8. Integration with Hook Framework

### 8.1 How Plugins Register Hooks

Plugins register hooks through the `PluginBase.register_hook()` method, which delegates to the Hook Registry from H01. The plugin manifest declares which hooks it will register, and the `register_hook()` method validates this.

```python
# Example plugin that registers hooks:

class KubernetesPlugin(PluginBase):
    async def on_enable(self) -> None:
        """Register hooks when the plugin is enabled."""
        self.register_hook(
            K8sDeploymentAuditHook(self.context),
            priority=10,  # Higher priority = earlier in chain
        )

    async def on_disable(self) -> None:
        """Deregister hooks when disabled."""
        # The hook registry deregisters all hooks from this plugin's source
        self.context.hook_registry.deregister_by_source(self.name)
```

### 8.2 Plugin Lifecycle Hooks

The Plugin SDK emits lifecycle events that other plugins can observe via the Hook Framework. These are system-level hooks that fire during plugin state transitions.

```python
# Hook points emitted by PluginRegistry:

class PluginLifecycleHookPoints:
    """Hook points emitted during plugin lifecycle transitions."""

    ON_PLUGIN_DISCOVERED = "plugin.discovered"   # manifest parsed
    ON_PLUGIN_LOADING = "plugin.loading"          # before on_load()
    ON_PLUGIN_LOADED = "plugin.loaded"            # after on_load()
    ON_PLUGIN_ENABLING = "plugin.enabling"        # before on_enable()
    ON_PLUGIN_ENABLED = "plugin.enabled"          # after on_enable()
    ON_PLUGIN_DISABLING = "plugin.disabling"      # before on_disable()
    ON_PLUGIN_DISABLED = "plugin.disabled"        # after on_disable()
    ON_PLUGIN_UNLOADING = "plugin.unloading"      # before on_unload()
    ON_PLUGIN_UNLOADED = "plugin.unloaded"        # after on_unload()
    ON_PLUGIN_ERROR = "plugin.error"              # lifecycle error
```

### 8.3 Hook Context for Plugin Events

```python
# The context passed to plugin lifecycle hooks:

class PluginHookContext:
    """Context available to hooks observing plugin lifecycle events."""
    plugin_name: str
    plugin_version: str
    previous_state: PluginState
    new_state: PluginState
    error: str | None = None
    metadata: dict[str, Any]  # cross-middleware state
    terminate: bool = False   # set True to block the transition
```

### 8.4 Hook Registration Scoping

Hooks registered by plugins respect these rules:

1. **System plugins** can register hooks that fire for all tenants.
2. **Shared plugins** register hooks that fire for tenants that have the plugin enabled.
3. **Tenant plugins** register hooks that fire only for their owning tenant.

The hook registry filters by `source` (the plugin name) and the tenant context of the current request.

---

## 9. Configuration Access

### 9.1 Plugin Configuration Schema

Plugins can declare a configuration schema and provide defaults. Tenants and admins can override values.

```python
# In PluginBase subclass:

class KubernetesPlugin(PluginBase):
    """Example plugin with configuration."""

    # Declare config schema as class variable
    CONFIG_SCHEMA: dict[str, Any] = {
        "type": "object",
        "properties": {
            "default_namespace": {
                "type": "string",
                "default": "default",
                "description": "Default Kubernetes namespace for deployments.",
            },
            "kubeconfig_path": {
                "type": "string",
                "default": "",
                "description": "Path to kubeconfig file. Empty uses in-cluster config.",
            },
            "max_replicas": {
                "type": "integer",
                "default": 10,
                "minimum": 1,
                "maximum": 100,
            },
        },
    }

    async def on_load(self) -> None:
        # Access merged config (defaults + admin overrides + tenant overrides)
        ns = self.context.plugin_config.get("default_namespace", "default")
        self._logger.info("Using namespace: %s", ns)
```

### 9.2 Configuration Resolution Order

Configuration values are resolved in this order (later overrides earlier):

1. **Plugin defaults** -- From `CONFIG_SCHEMA` default values
2. **System-level overrides** -- Admin-configured global settings
3. **Tenant-level overrides** -- Per-tenant configuration from `TenantPluginConfig.config_overrides`
4. **Environment variables** -- `PLUGIN_{NAME}_{KEY}` pattern (following Settings convention)

### 9.3 Read-Only System Settings Proxy

Plugins that request `config:read` get a read-only proxy to the system Settings:

```python
class ReadOnlySettingsProxy:
    """Proxy that exposes only safe, non-secret settings to plugins."""

    _SAFE_FIELDS: frozenset[str] = frozenset({
        "environment",
        "api_port",
        "ollama_base_url",
        "ollama_default_model",
        "embedding_provider",
        "rag_top_k",
        "rag_similarity_threshold",
        "chunk_tokens",
        "chunk_overlap_tokens",
    })

    def __init__(self, settings: Any) -> None:
        self._settings = settings

    def get(self, key: str) -> Any:
        """Read a setting by name. Only safe fields are exposed."""
        if key not in self._SAFE_FIELDS:
            raise PermissionError(
                f"Setting '{key}' is not exposed to plugins. "
                f"Safe fields: {sorted(self._SAFE_FIELDS)}"
            )
        return getattr(self._settings, key)
```

---

## 10. File Plan

### 10.1 New Files

| File | Responsibility | Est. Lines | Est. Tests |
|---|---|---|---|
| `engine/src/agent33/plugins/__init__.py` | Package init (re-exports) | 10 | 0 |
| `engine/src/agent33/plugins/manifest.py` | PluginManifest Pydantic model, PluginPermission, PluginStatus enums | 120 | 15 |
| `engine/src/agent33/plugins/models.py` | PluginState enum, PluginScope enum, internal models | 40 | 5 |
| `engine/src/agent33/plugins/base.py` | PluginBase abstract class with lifecycle and contribution helpers | 150 | 12 |
| `engine/src/agent33/plugins/context.py` | PluginContext dataclass | 50 | 8 |
| `engine/src/agent33/plugins/registry.py` | PluginRegistry (discovery, dep resolution, load/enable/disable/unload, CRUD, search) | 350 | 35 |
| `engine/src/agent33/plugins/loader.py` | Manifest file parsing (YAML, TOML, Markdown frontmatter) | 80 | 12 |
| `engine/src/agent33/plugins/capabilities.py` | CapabilityGrant evaluator | 70 | 10 |
| `engine/src/agent33/plugins/scoped.py` | ScopedSkillRegistry, ScopedToolRegistry, ReadOnlySettingsProxy | 100 | 12 |
| `engine/src/agent33/plugins/tenant.py` | TenantPluginConfig, TenantPluginState, visibility rules | 80 | 10 |
| `engine/src/agent33/plugins/api_models.py` | API response/request Pydantic models | 60 | 5 |
| `engine/src/agent33/plugins/version.py` | SemVer constraint checker (`_satisfies_constraint` and helpers) | 50 | 15 |
| `engine/src/agent33/api/routes/plugins.py` | FastAPI route handlers for plugin management | 200 | 25 |
| **Total New** | | **~1,360** | **~164** |

### 10.2 Modified Files

| File | Change | Est. Lines Changed |
|---|---|---|
| `engine/src/agent33/main.py` | Add PluginRegistry to lifespan init/shutdown | 30 |
| `engine/src/agent33/config.py` | Add `plugin_definitions_dir`, `plugin_auto_enable` settings | 5 |
| `engine/src/agent33/security/permissions.py` | Add `plugins:read`, `plugins:write` to SCOPES | 2 |
| `engine/pyproject.toml` | Add `tomli` to optional dependencies (for Python <3.11 TOML support, though we target >=3.11 which has `tomllib`) | 1 |

### 10.3 Test Files

| File | Coverage Area | Est. Tests |
|---|---|---|
| `engine/tests/test_plugin_manifest.py` | Manifest parsing, validation, all formats | 15 |
| `engine/tests/test_plugin_base.py` | PluginBase lifecycle, contribution helpers | 12 |
| `engine/tests/test_plugin_registry.py` | Discovery, dep resolution, CRUD, load/enable/disable/unload | 35 |
| `engine/tests/test_plugin_loader.py` | YAML/TOML/MD manifest loading, error handling | 12 |
| `engine/tests/test_plugin_capabilities.py` | Capability grants, permission intersection | 10 |
| `engine/tests/test_plugin_scoped.py` | Scoped registry proxies, permission enforcement | 12 |
| `engine/tests/test_plugin_tenant.py` | Multi-tenant config, visibility rules | 10 |
| `engine/tests/test_plugin_version.py` | SemVer constraint checking | 15 |
| `engine/tests/test_plugin_routes.py` | API endpoint integration tests | 25 |
| `engine/tests/test_plugin_integration.py` | End-to-end: discover -> load -> enable -> invoke -> disable -> unload | 18 |
| **Total Tests** | | **~164** |

---

## 11. Migration Path from Existing Patterns

### 11.1 Skills as Plugins

Existing standalone skills (SKILL.md/YAML in the `skills/` directory) continue to work unchanged. The migration path is:

1. **Phase 1 (H02)**: PluginRegistry discovers from `plugins/` directory. `skills/` directory continues to work via SkillRegistry.
2. **Phase 2 (H03 Skill Packs)**: Skills can be bundled into plugins. A plugin with `contributions.skills: [my-skill]` includes the SKILL.md in its directory.
3. **Phase 3 (Optional migration)**: Existing standalone skills can be wrapped in a minimal plugin manifest for unified management.

### 11.2 Tools as Plugins

Existing tools registered via `discover_from_entrypoints()` continue to work. Plugins can contribute tools that are registered through the same ToolRegistry.

### 11.3 Backward Compatibility Guarantees

- No changes to SkillRegistry, ToolRegistry, or AgentRegistry APIs
- No changes to existing skill/tool/agent definition formats
- No changes to existing API routes
- Plugins are additive: they contribute _to_ existing registries
- The `plugins/` directory is separate from `skills/` and `agent-definitions/`

---

## 12. Open Questions

### 12.1 Hot Reload Semantics

**Question**: When a plugin is reloaded (unload + load), should its contributed skills/tools persist across the gap or be briefly unavailable?

**Proposed answer**: Brief unavailability is acceptable. The reload endpoint (`POST /plugins/{name}/reload`) should complete within a few hundred milliseconds. In-flight requests that reference plugin contributions will get graceful errors.

### 12.2 Plugin-to-Plugin Communication

**Question**: Can plugins call each other's hooks or tools directly, or only through the registry?

**Proposed answer**: Only through the registry. Direct plugin-to-plugin calls would create tight coupling. If plugin A needs plugin B's tool, it should use `tool_registry.get()`. This is consistent with how agents invoke tools today.

### 12.3 Plugin Versioning and Upgrade

**Question**: What happens when a plugin is upgraded to a new version?

**Proposed answer**: The upgrade flow is: unload old -> discover new manifest -> load new -> enable new. Data migrations (if any) are the plugin's responsibility in `on_load()`. The manifest's `schema_version` field supports format evolution.

### 12.4 Dependency on H01 (Hook Framework)

**Question**: What is the minimal H01 interface that H02 depends on?

**Proposed answer**: The PluginRegistry needs:
- `HookRegistry.register(hook, priority, source)` -- register a hook from a plugin
- `HookRegistry.deregister_by_source(source)` -- remove all hooks from a plugin
- `HookRegistry.emit(hook_point, context)` -- emit lifecycle events

If H01 is not yet implemented, the PluginRegistry can operate without hook support (hooks are optional contributions). A no-op HookRegistry stub would satisfy the interface.

### 12.5 Database Schema

**Question**: Should plugin state be persisted to the database or kept in-memory?

**Proposed answer**: Both. The PluginRegistry is in-memory (like SkillRegistry and AgentRegistry). Tenant-specific configuration (`TenantPluginConfig`) is persisted to the database. Plugin state is reconstructed from manifests + DB config on startup.

---

## Appendix A: Comparison with Research Findings

| Research Finding | AGENT-33 Plugin SDK Adaptation |
|---|---|
| MS Agent Framework: 3-tier middleware with `next()` delegation | Adopted via H01 Hook Framework; plugins register hooks, not middleware directly |
| Semantic Kernel: `@kernel_function` decorator + FilterTypes | Simplified to `PluginBase.register_hook()` with manifest validation |
| OpenAI Agents SDK: observer/callback hooks | Rejected in favor of middleware chain (more powerful) |
| n8n: 400+ connectors with centralized credentials | Plugin-scoped credential access via `secrets:read` permission + existing CredentialVault |
| MCP Gateway: OAuth2 + semantic discovery | Deferred to H05 marketplace; basic search via `PluginRegistry.search()` |
| PyBreaker circuit breakers | Orthogonal to Plugin SDK; circuit breakers live in Phase 32.7 |
| LangGraph: dynamic tool registry with semantic search | Existing SkillMatcher already provides BM25 + LLM hybrid matching |

## Appendix B: Example Plugin

A complete minimal plugin:

```
plugins/
  hello-world/
    plugin.yaml
    plugin.py
```

**`plugin.yaml`**:
```yaml
name: hello-world
version: 1.0.0
description: A minimal example plugin
author: agent33-team
entry_point: "plugin:HelloWorldPlugin"

contributions:
  skills:
    - hello-greeting

permissions:
  - config:read

tags:
  - example
  - tutorial
```

**`plugin.py`**:
```python
from agent33.plugins.base import PluginBase
from agent33.skills.definition import SkillDefinition


class HelloWorldPlugin(PluginBase):
    async def on_load(self) -> None:
        skill = SkillDefinition(
            name="hello-greeting",
            version=self.version,
            description="Generates friendly greetings",
            instructions="When asked to greet someone, respond warmly.",
            tags=["greeting", "example"],
        )
        self.register_skill(skill)
        self._logger.info("Hello World plugin loaded!")

    async def on_enable(self) -> None:
        self._logger.info("Hello World plugin enabled!")

    async def on_disable(self) -> None:
        self._logger.info("Hello World plugin disabled.")

    async def on_unload(self) -> None:
        self._logger.info("Hello World plugin unloaded. Goodbye!")
```
