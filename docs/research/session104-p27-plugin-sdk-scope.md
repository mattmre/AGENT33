# P2.7 Plugin SDK Contracts and Packaging -- Scope Memo

**Session**: 104
**Slice**: P2.7
**Date**: 2026-03-24

## Objective

Define and harden the public extension surface for third-party AGENT-33 plugins.
This slice adds allowlist-based trust enforcement, multi-path discovery, and
developer documentation on top of the existing plugin framework (Phase 32.8).

## Plugin vs Skill vs Tool

| Concept   | Scope                                    | Packaging                         | Trust Boundary          |
| --------- | ---------------------------------------- | --------------------------------- | ----------------------- |
| **Tool**  | Single callable with JSON Schema params  | Python class registered at startup | Governance allowlist    |
| **Skill** | Domain knowledge bundle (instructions, tool config, references) | YAML/Markdown file or directory  | SkillInjector disclosure |
| **Plugin**| Composite extension unit that can contribute tools, skills, agents, and hooks | Directory with manifest + Python code | Allowlist + capability grants |

- A **Tool** is the atomic execution unit: one function, one JSON Schema.
- A **Skill** is a knowledge/configuration bundle that can be attached to agents.
- A **Plugin** is the packaging and lifecycle unit that can contribute any
  combination of tools, skills, agent definitions, and hooks. It has its own
  manifest, dependency graph, permission model, and lifecycle state machine.

## What a Plugin Can Extend

Plugins declare their contributions in the manifest's `contributions` section:

1. **Skills** -- Register `SkillDefinition` objects via `PluginBase.register_skill()`.
2. **Tools** -- Register `Tool` instances via `PluginBase.register_tool()`.
3. **Agents** -- Provide agent definition JSON files loaded during `on_load()`.
4. **Hooks** -- Register lifecycle hooks (requires `hook:register` permission).

Plugins access system registries through a **scoped context** (`PluginContext`)
that enforces capability grants. A plugin cannot access resources beyond what its
manifest declares and what the admin/tenant approves.

## Trust Model

### Allowlist-Only (Current)

The plugin registry enforces an **allowlist-only** trust model when
`PLUGIN_ALLOWLIST` is configured (comma-separated plugin names). When set:

- Only plugins whose names appear in the allowlist can be discovered.
- Plugins not on the allowlist are rejected at discovery time with a
  `PermissionError`.
- When the allowlist is empty or unset, all plugins are allowed (development
  mode).

### Capability Grants (Existing)

Each plugin declares permissions in its manifest. The effective grant is the
intersection of:

1. What the manifest requests
2. What the admin approves (defaults to all requested in dev mode)
3. What the tenant approves (defaults to admin grants)

Denied permissions are logged and surfaced via the plugin doctor diagnostic.

### Signed Manifests (Future)

Not implemented in this slice. A future enhancement could add cryptographic
manifest signing to verify plugin integrity and authorship without relying
solely on name-based allowlists.

## Versioning

- Plugin versions use **SemVer** format (`X.Y.Z`), enforced by the manifest
  `version` field pattern.
- Inter-plugin dependencies use **SemVer constraints**: `>=`, `<=`, `>`, `<`,
  `^` (compatible), `~` (approximate), `*` (any), or exact match.
- The `min_agent33_version` field (planned for future manifest extension)
  would allow plugins to declare the minimum engine version they support.

## Multi-Path Discovery

Plugins can be discovered from multiple directories:

1. **Primary**: `PLUGIN_DEFINITIONS_DIR` (default: `plugins/`)
2. **Extra**: `PLUGIN_DISCOVERY_PATHS` (comma-separated, optional)

All paths are scanned at startup. This allows separating system plugins from
user-installed or tenant-specific plugins.

## Non-Goals

The following are explicitly out of scope for P2.7:

1. **Plugin marketplace** -- No remote discovery, download, or rating system.
2. **Signing infrastructure** -- No PKI, no manifest signing, no trust chains.
3. **Runtime hot-reload** -- Plugins are loaded at startup and can be enabled/
   disabled, but there is no file-watcher or hot-swap mechanism.
4. **Plugin sandboxing** -- Plugins run in the same Python process. The scoped
   context limits registry access but does not provide OS-level isolation.
5. **Plugin versioned migration** -- No automatic data migration between plugin
   versions.

## Deliverables

1. Config additions: `plugin_allowlist`, `plugin_discovery_paths`
2. Registry allowlist enforcement: `is_allowed()` method, rejection at discover time
3. Multi-path discovery wiring in `main.py`
4. Developer documentation: `docs/plugins/README.md`
5. SDK contract tests: `engine/tests/test_plugin_sdk.py`
6. This scope memo
