# AGENT-33 Plugin SDK

This document describes how to create, package, and register plugins for the
AGENT-33 engine.

## Overview

A plugin is a self-contained extension that can contribute tools, skills, agent
definitions, and hooks to the AGENT-33 runtime. Plugins are discovered from the
filesystem, loaded in dependency order, and managed through a lifecycle state
machine.

### Plugin vs Skill vs Tool

- **Tool**: A single callable with JSON Schema-validated parameters. Registered
  in the `ToolRegistry`.
- **Skill**: A domain-knowledge bundle (instructions, tool configuration,
  references) loaded from YAML or Markdown. Registered in the `SkillRegistry`.
- **Plugin**: A composite packaging unit that can contribute any combination of
  tools, skills, agents, and hooks. Has its own manifest, dependency graph,
  permission model, and lifecycle.

## Creating a Plugin

### 1. Create the Plugin Directory

```
my-plugin/
  plugin.yaml       # manifest (required)
  plugin.py          # entry point (required)
```

### 2. Write the Manifest

Create `plugin.yaml` with the following fields:

```yaml
name: my-plugin                  # [a-z][a-z0-9-]*, max 64 chars
version: "1.0.0"                 # SemVer (X.Y.Z)
description: "A brief summary"
author: "Your Name"
license: "MIT"

entry_point: "plugin:MyPlugin"   # module_path:ClassName

contributions:
  skills:
    - my-custom-skill            # skill names this plugin provides
  tools:
    - MyCustomTool               # tool class names this plugin provides
  hooks:
    - MyCustomHook               # hook class names this plugin registers

permissions:
  - file:read                    # system capabilities this plugin needs
  - tool:execute
  - hook:register

dependencies:                    # other plugins this depends on
  - name: base-utils
    version_constraint: ">=1.0.0"
    optional: false

tags:
  - utilities
  - data-processing

status: active                   # active | deprecated | experimental
```

#### Manifest Field Reference

| Field           | Type           | Required | Description                                  |
| --------------- | -------------- | -------- | -------------------------------------------- |
| `name`          | string         | Yes      | Unique slug matching `^[a-z][a-z0-9-]*$`     |
| `version`       | string         | Yes      | SemVer string (`X.Y.Z`)                      |
| `description`   | string         | No       | Short description (max 500 chars)             |
| `author`        | string         | No       | Plugin author                                |
| `license`       | string         | No       | License identifier                           |
| `homepage`      | string         | No       | URL to plugin homepage                       |
| `repository`    | string         | No       | URL to source repository                     |
| `entry_point`   | string         | No       | Python import path (`module:Class`). Default: `plugin:Plugin` |
| `contributions` | object         | No       | What the plugin contributes (skills, tools, agents, hooks) |
| `permissions`   | list of string | No       | System capabilities requested                |
| `dependencies`  | list of object | No       | Other plugins this depends on                |
| `status`        | string         | No       | Lifecycle status (default: `active`)         |
| `tags`          | list of string | No       | Discovery tags                               |

#### Supported Manifest Formats

- **YAML**: `plugin.yaml` or `plugin.yml` (recommended)
- **TOML**: `plugin.toml` (plugin data under `[plugin]` section)
- **Markdown**: `PLUGIN.md` (YAML frontmatter)

### 3. Implement the Plugin Class

Create `plugin.py` with a class that extends `PluginBase`:

```python
from agent33.plugins.base import PluginBase
from agent33.plugins.manifest import PluginManifest
from agent33.plugins.context import PluginContext
from agent33.skills.definition import SkillDefinition
from agent33.tools.base import Tool, ToolContext, ToolResult


class MyCustomTool(Tool):
    """Example tool contributed by the plugin."""

    name = "my-custom-tool"
    description = "Does something useful"

    async def execute(self, params: dict, context: ToolContext) -> ToolResult:
        return ToolResult.ok({"result": "success"})


class MyPlugin(PluginBase):
    """Example AGENT-33 plugin."""

    async def on_load(self) -> None:
        """Register skills and tools during loading."""
        # Register a tool (must be declared in contributions.tools)
        self.register_tool(MyCustomTool())

        # Register a skill (must be declared in contributions.skills)
        skill = SkillDefinition(
            name="my-custom-skill",
            version="1.0.0",
            description="Custom skill from my-plugin",
            instructions="Detailed instructions here...",
        )
        self.register_skill(skill)

    async def on_enable(self) -> None:
        """Start background tasks or register hooks."""
        self._logger.info("Plugin enabled!")

    async def on_disable(self) -> None:
        """Stop background tasks or deregister hooks."""
        self._logger.info("Plugin disabled!")

    async def on_unload(self) -> None:
        """Release resources."""
        self._logger.info("Plugin unloaded!")
```

### 4. Lifecycle Methods

| Method       | When Called                           | Typical Usage                           |
| ------------ | ------------------------------------ | --------------------------------------- |
| `on_load`    | After instantiation, before enable   | Register skills, tools, agents          |
| `on_enable`  | Transitioning to active state        | Register hooks, start background tasks  |
| `on_disable` | Transitioning from active to disabled | Deregister hooks, stop background tasks |
| `on_unload`  | Plugin being completely removed      | Close connections, release resources    |

All methods have no-op defaults. Override only the ones your plugin needs.

## Registering a Plugin

### Filesystem Discovery

Place plugin directories under the configured `PLUGIN_DEFINITIONS_DIR`
(default: `plugins/`):

```
engine/plugins/
  my-plugin/
    plugin.yaml
    plugin.py
  another-plugin/
    plugin.yaml
    plugin.py
```

Plugins are discovered and loaded automatically at startup.

### Extra Discovery Paths

Set `PLUGIN_DISCOVERY_PATHS` to scan additional directories (comma-separated):

```bash
export PLUGIN_DISCOVERY_PATHS="/opt/agent33/system-plugins,/home/user/my-plugins"
```

### Programmatic Registration

Use the `PluginInstaller` for runtime installation:

```python
from pathlib import Path

installer = app.state.plugin_installer
result = await installer.install_from_local(
    Path("/path/to/my-plugin"),
    mode="copy",      # copy files into plugins dir
    enable=True,       # enable after loading
)
```

## Trust Model and Allowlist

### Allowlist Enforcement

By default, all plugins are allowed (development mode). In production, set the
`PLUGIN_ALLOWLIST` environment variable to restrict which plugins can be loaded:

```bash
export PLUGIN_ALLOWLIST="trusted-plugin-a,trusted-plugin-b,my-org-plugin"
```

When the allowlist is set:

- Only plugins whose names appear in the list can be discovered.
- Plugins not on the list are rejected with a `PermissionError` at discovery
  time.
- The allowlist is checked before any plugin code is executed.

### Permission Model

Plugins declare the system capabilities they need in the manifest's
`permissions` field. Available permissions:

| Permission       | Description                                 |
| ---------------- | ------------------------------------------- |
| `file:read`      | Read files from the filesystem              |
| `file:write`     | Write files to the filesystem               |
| `network`        | Make network requests                       |
| `database:read`  | Read from the database                      |
| `database:write` | Write to the database                       |
| `subprocess`     | Spawn subprocesses                          |
| `secrets:read`   | Read secrets from the vault                 |
| `tool:execute`   | Execute tools via the registry              |
| `agent:invoke`   | Invoke agents                               |
| `hook:register`  | Register lifecycle hooks                    |
| `config:read`    | Read system configuration (safe fields only)|
| `config:write`   | Modify plugin configuration                 |

The effective permissions are the intersection of:

1. What the manifest requests
2. What the admin approves
3. What the tenant approves (for multi-tenant deployments)

## Version Compatibility

Plugin versions use SemVer (`X.Y.Z`). Dependencies between plugins support
these constraint formats:

| Constraint | Meaning                                    | Example        |
| ---------- | ------------------------------------------ | -------------- |
| `*`        | Any version                                | `*`            |
| `X.Y.Z`   | Exact match                                | `1.2.3`        |
| `>=X.Y.Z` | Greater than or equal                      | `>=1.0.0`      |
| `<=X.Y.Z` | Less than or equal                         | `<=2.0.0`      |
| `>X.Y.Z`  | Strictly greater                           | `>1.0.0`       |
| `<X.Y.Z`  | Strictly less                              | `<3.0.0`       |
| `^X.Y.Z`  | Compatible (same major, >= minor.patch)    | `^1.2.0`       |
| `~X.Y.Z`  | Approximate (same major.minor, >= patch)   | `~1.2.3`       |

## Plugin Diagnostics

The plugin doctor can diagnose issues with any registered plugin:

```python
doctor = app.state.plugin_doctor
report = await doctor.diagnose("my-plugin")
# report.overall_status: "healthy" | "degraded" | "broken"
# report.checks: list of individual diagnostic checks
# report.permissions: requested, granted, and denied permissions
```

## Configuration

| Environment Variable         | Default                         | Description                          |
| ---------------------------- | ------------------------------- | ------------------------------------ |
| `PLUGIN_DEFINITIONS_DIR`     | `plugins`                       | Primary plugin directory             |
| `PLUGIN_AUTO_ENABLE`         | `true`                          | Auto-enable plugins after loading    |
| `PLUGIN_STATE_STORE_PATH`    | `var/plugin_lifecycle_state.json` | Lifecycle state persistence file   |
| `PLUGIN_ALLOWLIST`           | (empty)                         | Comma-separated allowed plugin names |
| `PLUGIN_DISCOVERY_PATHS`     | (empty)                         | Comma-separated extra discovery dirs |
