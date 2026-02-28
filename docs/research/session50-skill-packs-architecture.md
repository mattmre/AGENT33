# Skill Packs & Distribution Architecture (H03 -- Phase 33)

**Date**: 2026-02-27
**Status**: Architecture Proposal (Pre-Implementation)
**AEP ID**: AEP-20260227-H03
**Phase**: 33 (Skill Packs, Distribution & Capability Discovery)
**Depends On**: Phase 32.1 (Hook Framework / H01), Phase 32.8 (Plugin SDK / H02)
**Research Basis**: `docs/research/skillsbench-analysis.md`, `docs/research/hooks-mcp-plugin-architecture-research.md`, `docs/phases/PHASE-29-33-WORKFLOW-PLAN.md`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Existing Skills System Analysis](#2-existing-skills-system-analysis)
3. [Pack Manifest (PACK.yaml)](#3-pack-manifest-packyaml)
4. [Semver Dependency Resolution](#4-semver-dependency-resolution)
5. [Pack Registry](#5-pack-registry)
6. [Marketplace API](#6-marketplace-api)
7. [Agent Skills Standard Compatibility](#7-agent-skills-standard-compatibility)
8. [Integration Points](#8-integration-points)
9. [Security Model](#9-security-model)
10. [File Plan](#10-file-plan)
11. [Migration Strategy](#11-migration-strategy)
12. [Test Plan](#12-test-plan)

---

## 1. Executive Summary

### Problem Statement

AGENT-33's current skill system is monolithic: skills are individual SKILL.md/YAML files discovered from a single flat directory (`skill_definitions_dir`). There is no concept of grouping related skills into distributable units, no versioned dependency resolution between skills, no marketplace for sharing skills across deployments, and no compatibility layer with external skill standards (SkillsBench, MCP tools).

### Solution

Introduce **Skill Packs** -- versioned, distributable bundles of related skills with dependency management, a local and remote registry, and an adapter layer for external skill formats. The design follows established package distribution patterns (npm, pip, Cargo) while preserving AGENT-33's existing skill architecture (SkillDefinition, SkillRegistry, SkillInjector, progressive disclosure L0/L1/L2).

### Design Principles

1. **Additive, not disruptive.** Existing standalone skills continue to work unchanged. Packs are an organizational layer above individual skills.
2. **Semver-first.** All version constraints use semantic versioning. Lock files ensure reproducible deployments.
3. **Tenant-isolated.** Pack installation, enablement, and configuration are scoped per tenant, consistent with AGENT-33's multi-tenancy model.
4. **Security by default.** Pack installation validates integrity (checksums), origin (signed manifests), and capability requirements (no silent privilege escalation).
5. **Progressive adoption.** Teams can start with local packs (directory-based), graduate to a local registry, and optionally connect to a marketplace.

---

## 2. Existing Skills System Analysis

### Current Architecture

The skills subsystem consists of five modules in `engine/src/agent33/skills/`:

| Module | Responsibility | Key Types |
|--------|---------------|-----------|
| `definition.py` | Pydantic model for a single skill | `SkillDefinition`, `SkillDependency`, `SkillStatus`, `SkillInvocationMode`, `SkillExecutionContext` |
| `registry.py` | In-memory CRUD registry with discovery | `SkillRegistry` (discover, register, get, remove, list_all, find_by_tag, find_by_tool, search) |
| `injection.py` | Prompt injection and tool context resolution | `SkillInjector` (build_skill_metadata_block, build_skill_instructions_block, resolve_tool_context) |
| `loader.py` | File parsing: SKILL.md frontmatter, YAML, directory conventions | `parse_frontmatter`, `load_from_skillmd`, `load_from_yaml`, `load_from_directory` |
| `matching.py` | 4-stage hybrid skill matching pipeline | `SkillMatcher`, `SkillMatchResult`, `_SkillBM25` |

### Current Skill Definition Model

From `definition.py`, `SkillDefinition` has 20+ fields:

- **Identity**: `name` (slug, 1-64 chars), `version` (semver string), `description`, `author`, `tags`, `schema_version`
- **Content**: `instructions` (markdown body), `scripts_dir`, `templates_dir`, `references`
- **Governance**: `invocation_mode`, `execution_context`, `autonomy_level`, `approval_required_for`, `allowed_tools`, `disallowed_tools`, `tool_parameter_defaults`
- **Lifecycle**: `status` (active/deprecated/experimental), `dependencies` (list of `SkillDependency`)
- **Runtime**: `base_path` (excluded from serialization)

### Current Dependency Model

`SkillDependency` is minimal:

```python
class SkillDependency(BaseModel):
    name: str
    kind: str = "skill"  # "skill" or "tool"
    optional: bool = False
```

No version constraints, no conflict detection, no transitive resolution.

### Current Discovery Flow

1. `SkillRegistry.discover(path)` scans a directory
2. For each entry: directory -> `load_from_directory()` (SKILL.md first, then skill.yaml), YAML file -> `load_from_yaml()`, SKILL.md file -> `load_from_skillmd()`
3. Loaded skills registered via `register()` (last-write-wins on name collision)
4. At startup in `main.py`: `skill_registry.discover(Path(settings.skill_definitions_dir))`

### Progressive Disclosure

- **L0**: `SkillRegistry.get_metadata_only(name)` -- returns `{name, description}` for context budget
- **L1**: `SkillRegistry.get_full_instructions(name)` -- returns full markdown instructions
- **L2**: `SkillRegistry.get_resource(name, resource_path)` -- loads bundled file with path traversal protection

### Matching Pipeline (from SkillsBench integration)

The 4-stage `SkillMatcher` in `matching.py`:
1. BM25 text retrieval (skill-specific index over name/description/tags)
2. LLM lenient filter (generous, avoids false negatives)
3. Full content loading (implicit -- definitions already in memory)
4. LLM strict filter (rejects irrelevant and answer-leaking skills)

### Gaps That Packs Address

| Gap | Impact |
|-----|--------|
| No grouping of related skills | Cannot distribute a "Kubernetes Operations" bundle as a unit |
| No version constraints on dependencies | Cannot express "requires shell-utils >= 2.0.0" |
| No transitive dependency resolution | Installing pack A that depends on pack B requires manual intervention |
| No lock file for reproducibility | Deployments may drift between environments |
| No install/uninstall lifecycle | Skills are always present once discovered; no way to cleanly remove a set |
| No tenant-scoped enablement | All discovered skills are globally available |
| No external format adapter | Cannot consume SkillsBench skill folders or MCP tool definitions as packs |
| No integrity verification | Skills are loaded without checksum or signature validation |

---

## 3. Pack Manifest (PACK.yaml)

### Format Specification

A Skill Pack is a directory containing a `PACK.yaml` manifest and one or more skill definitions. The manifest is the pack's identity document.

```yaml
# PACK.yaml -- Skill Pack Manifest v1
schema_version: "1"

# Identity
name: kubernetes-operations
version: 2.1.0
description: "Production-grade Kubernetes deployment, monitoring, and troubleshooting skills"
author: "agent33-community"
license: "Apache-2.0"
homepage: "https://github.com/agent33-community/pack-kubernetes-operations"
repository: "https://github.com/agent33-community/pack-kubernetes-operations"

# Classification
tags:
  - devops
  - kubernetes
  - deployment
  - monitoring
category: infrastructure  # primary category for marketplace browsing

# Skills included in this pack
skills:
  - name: kubernetes-deploy
    path: skills/kubernetes-deploy       # relative to PACK.yaml
    description: "Deploy and update Kubernetes workloads"
    required: true                       # must be loaded for pack to function

  - name: kubernetes-monitor
    path: skills/kubernetes-monitor
    description: "Monitor cluster health and pod status"
    required: false                      # optional skill within the pack

  - name: kubernetes-troubleshoot
    path: skills/kubernetes-troubleshoot
    description: "Debug failing pods and services"
    required: false

# Dependencies
dependencies:
  packs:
    - name: shell-utilities
      version: "^2.0.0"                 # semver constraint
    - name: yaml-processing
      version: ">=1.0.0, <3.0.0"
  engine:
    min_version: "0.1.0"                 # minimum AGENT-33 engine version

# Compatibility
compatibility:
  agent_roles:                           # which agent roles can use this pack
    - code-worker
    - orchestrator
  capabilities:                          # required agent capabilities (from P/I/V/R/X taxonomy)
    - P-SHELL                            # needs shell access
    - I-WORKFLOW                         # needs workflow integration
  python_packages:                       # runtime Python dependencies
    - name: kubernetes
      version: ">=29.0.0"
    - name: pyyaml
      version: ">=6.0"

# Governance
governance:
  min_autonomy_level: supervised         # minimum autonomy required
  approval_required_for:
    - "kubectl delete"
    - "kubectl apply --force"
  max_instructions_chars: 16000          # override per-skill instruction limit
```

### Manifest Fields Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | string | yes | Manifest format version (currently "1") |
| `name` | string | yes | Pack slug (lowercase, hyphens, 1-64 chars), globally unique |
| `version` | string | yes | Semver (MAJOR.MINOR.PATCH), no pre-release tags in v1 |
| `description` | string | yes | Short description (max 500 chars) |
| `author` | string | yes | Author or organization name |
| `license` | string | no | SPDX license identifier |
| `homepage` | string | no | URL to pack documentation |
| `repository` | string | no | URL to source repository |
| `tags` | list[string] | no | Searchable tags |
| `category` | string | no | Primary category for browsing |
| `skills` | list[SkillEntry] | yes | Skills included in this pack |
| `skills[].name` | string | yes | Skill name (must match the skill's own name field) |
| `skills[].path` | string | yes | Relative path to skill directory or file |
| `skills[].description` | string | no | Override description (defaults to skill's own) |
| `skills[].required` | bool | no | Whether this skill must load successfully (default: true) |
| `dependencies.packs` | list[PackDep] | no | Other packs this pack depends on |
| `dependencies.packs[].name` | string | yes | Dependent pack name |
| `dependencies.packs[].version` | string | yes | Semver constraint string |
| `dependencies.engine.min_version` | string | no | Minimum AGENT-33 engine version |
| `compatibility.agent_roles` | list[string] | no | Agent roles that can use this pack |
| `compatibility.capabilities` | list[string] | no | Required capability codes |
| `compatibility.python_packages` | list[PkgDep] | no | Python packages needed at runtime |
| `governance` | object | no | Pack-level governance overrides |

### SkillEntry vs SkillDefinition

The `skills` list in PACK.yaml provides metadata about which skills the pack contains and where to find them. The actual skill definitions (SkillDefinition model) remain in their respective SKILL.md or skill.yaml files. The pack manifest provides:

1. **Inventory** -- which skills are in this pack
2. **Required/optional** -- which skills must load successfully
3. **Override descriptions** -- pack authors can provide pack-context descriptions

The loader reads PACK.yaml, then loads each skill from its `path` using the existing `load_from_directory()` / `load_from_yaml()` / `load_from_skillmd()` functions.

### Directory Structure

```
my-pack/
  PACK.yaml                          # Pack manifest
  README.md                          # Human-readable documentation (optional)
  skills/
    kubernetes-deploy/
      SKILL.md                       # Standard AGENT-33 skill definition
      scripts/
        deploy.sh
      templates/
        deployment.yaml.j2
    kubernetes-monitor/
      skill.yaml
      scripts/
        check-health.py
    kubernetes-troubleshoot/
      SKILL.md
  tests/                             # Pack-level tests (optional)
    test_skills_load.py
  CHECKSUMS.sha256                   # Integrity file (optional, required for marketplace)
  SIGNATURE.sig                      # Detached GPG/age signature (optional)
```

---

## 4. Semver Dependency Resolution

### Version Constraint Syntax

The system supports standard semver constraint operators, compatible with both npm and pip conventions:

| Syntax | Meaning | Example |
|--------|---------|---------|
| `^1.2.3` | Compatible with 1.x.x (>=1.2.3, <2.0.0) | `^1.0.0` matches 1.0.0 through 1.99.99 |
| `~1.2.3` | Approximately (>=1.2.3, <1.3.0) | `~1.2.0` matches 1.2.0 through 1.2.99 |
| `>=1.0.0` | Greater than or equal | Matches 1.0.0 and above |
| `<2.0.0` | Less than | Matches anything below 2.0.0 |
| `>=1.0.0, <2.0.0` | Range (comma-separated AND) | Matches 1.x.x only |
| `1.2.3` | Exact version | Only matches 1.2.3 |
| `*` | Any version | Matches all versions |

### Constraint Parsing

```python
@dataclass(frozen=True)
class VersionConstraint:
    """A parsed semver constraint."""
    raw: str                    # original string, e.g. "^1.2.0"
    ranges: list[VersionRange]  # parsed into one or more ranges

    def satisfies(self, version: Version) -> bool:
        """Check if a concrete version satisfies this constraint."""
        return all(r.contains(version) for r in self.ranges)

    @classmethod
    def parse(cls, raw: str) -> VersionConstraint:
        """Parse constraint string into ranges.

        Supports: ^, ~, >=, <=, >, <, =, exact, * (any).
        Comma-separated constraints are ANDed.
        """
        ...
```

### Resolution Algorithm

The resolver uses a **greedy backtracking algorithm** inspired by pip's resolver (PEP 665) and Cargo's resolver. It is simpler than npm's full SAT solver because the pack ecosystem will initially be small (hundreds, not millions of packages).

**Algorithm**:

1. Build a dependency graph from the root pack's requirements
2. For each unresolved dependency, query the registry for available versions
3. Select the highest version satisfying the constraint
4. Recursively resolve that version's dependencies
5. If a conflict arises (two packs require incompatible versions of a third), backtrack to the most recent decision point and try the next-highest version
6. If no solution is found, report the conflict chain

```python
class DependencyResolver:
    """Resolve pack dependencies using greedy backtracking."""

    def __init__(self, registry: PackRegistry) -> None:
        self._registry = registry

    def resolve(self, requirements: list[PackRequirement]) -> ResolutionResult:
        """Resolve a set of pack requirements to concrete versions.

        Returns a ResolutionResult containing either a resolved set of
        (pack_name, version) pairs, or a list of conflict descriptions.
        """
        ...

@dataclass(frozen=True)
class ResolutionResult:
    """Outcome of dependency resolution."""
    resolved: dict[str, str] | None     # {pack_name: version} if successful
    conflicts: list[ConflictDetail]     # non-empty if resolution failed
    graph: dict[str, list[str]]         # dependency graph for visualization

@dataclass(frozen=True)
class ConflictDetail:
    """Describes a dependency conflict."""
    package: str                        # conflicting pack name
    required_by: dict[str, str]         # {requirer_name: constraint_string}
    available_versions: list[str]       # versions in the registry
    reason: str                         # human-readable explanation
```

### Conflict Detection

Conflicts arise when:

1. **Version incompatibility**: Pack A requires `utils ^1.0.0` and Pack B requires `utils ^2.0.0`. No single version of `utils` satisfies both.
2. **Missing pack**: A dependency references a pack not present in any configured registry.
3. **Circular dependency**: Pack A depends on Pack B which depends on Pack A.
4. **Engine version mismatch**: A pack requires a newer engine version than the running instance.
5. **Capability mismatch**: A pack requires capabilities not available in the target agent roles.

Each conflict produces a `ConflictDetail` with a human-readable explanation and the full dependency chain.

### Lock File Format

After successful resolution, a lock file (`PACK.lock`) is generated for reproducibility:

```yaml
# PACK.lock -- Auto-generated, do not edit
# Resolved: 2026-02-27T14:30:00Z
# Engine: 0.1.0
# Resolver: greedy-backtrack-v1

lock_version: "1"
engine_version: "0.1.0"

packages:
  kubernetes-operations:
    version: "2.1.0"
    checksum: "sha256:a1b2c3d4e5f6..."
    source: local

  shell-utilities:
    version: "2.3.1"
    checksum: "sha256:f6e5d4c3b2a1..."
    source: marketplace
    resolved_from: "^2.0.0"

  yaml-processing:
    version: "1.5.0"
    checksum: "sha256:1a2b3c4d5e6f..."
    source: marketplace
    resolved_from: ">=1.0.0, <3.0.0"
```

The lock file records:
- Exact resolved version for each pack
- SHA-256 checksum for integrity verification
- Source (local, marketplace, or git URL)
- Original constraint that was resolved

When a lock file exists, the installer uses it directly instead of running the resolver, ensuring deterministic installations.

---

## 5. Pack Registry

The Pack Registry manages pack lifecycle on a single AGENT-33 instance. It sits between the filesystem (where packs are stored) and the SkillRegistry (where individual skills are registered).

### Architecture

```
  Marketplace API (remote)
        |
        v
  PackRegistry (local, per-instance)
        |
        +-- PackIndex (manifest cache + version index)
        |
        +-- PackInstaller (download, validate, extract)
        |
        +-- DependencyResolver (semver resolution)
        |
        +-- PackLoader (load pack -> load skills -> register)
        |
        v
  SkillRegistry (existing, unchanged)
```

### PackRegistry Class

```python
class PackRegistry:
    """Manages installed skill packs and their lifecycle."""

    def __init__(
        self,
        packs_dir: Path,
        skill_registry: SkillRegistry,
        resolver: DependencyResolver | None = None,
    ) -> None:
        self._packs_dir = packs_dir          # where packs are stored on disk
        self._skill_registry = skill_registry # existing skill registry
        self._resolver = resolver
        self._installed: dict[str, InstalledPack] = {}
        self._enabled: dict[str, set[str]] = {}  # tenant_id -> set of enabled pack names

    # -- Discovery & Loading -------------------------------------------------

    def discover(self, path: Path | None = None) -> int:
        """Scan a directory for PACK.yaml manifests.

        Each discovered pack is validated, its skills loaded, and the pack
        registered. Returns the number of packs loaded.
        """
        ...

    def load_pack(self, pack_dir: Path) -> InstalledPack:
        """Load a single pack from a directory containing PACK.yaml.

        Validates the manifest, loads each skill definition via the existing
        loader module, and returns an InstalledPack.
        """
        ...

    # -- Installation --------------------------------------------------------

    def install(self, source: PackSource) -> InstallResult:
        """Install a pack from a local path, tarball, or marketplace.

        Steps:
        1. Download/extract to a staging directory
        2. Parse and validate PACK.yaml
        3. Resolve dependencies
        4. Verify checksums (if CHECKSUMS.sha256 present)
        5. Move to packs_dir
        6. Load skills into SkillRegistry
        7. Generate/update PACK.lock
        """
        ...

    def uninstall(self, name: str) -> bool:
        """Uninstall a pack.

        Steps:
        1. Check no other installed pack depends on this one
        2. Remove skills from SkillRegistry
        3. Remove pack directory from packs_dir
        4. Update PACK.lock
        """
        ...

    # -- Enable/Disable (tenant-scoped) --------------------------------------

    def enable(self, name: str, tenant_id: str) -> bool:
        """Enable a pack for a specific tenant.

        Only enabled packs' skills are available via SkillInjector
        for that tenant's agents.
        """
        ...

    def disable(self, name: str, tenant_id: str) -> bool:
        """Disable a pack for a specific tenant."""
        ...

    def is_enabled(self, name: str, tenant_id: str) -> bool:
        """Check if a pack is enabled for a tenant."""
        ...

    def list_enabled(self, tenant_id: str) -> list[InstalledPack]:
        """List all packs enabled for a tenant."""
        ...

    # -- Version Management ---------------------------------------------------

    def upgrade(self, name: str, target_version: str | None = None) -> InstallResult:
        """Upgrade a pack to a newer version.

        If target_version is None, upgrades to the latest compatible version.
        Re-resolves dependencies after upgrade.
        """
        ...

    def downgrade(self, name: str, target_version: str) -> InstallResult:
        """Downgrade a pack to an older version."""
        ...

    # -- Query ----------------------------------------------------------------

    def get(self, name: str) -> InstalledPack | None:
        """Look up an installed pack by name."""
        ...

    def list_installed(self) -> list[InstalledPack]:
        """List all installed packs."""
        ...

    def search(self, query: str) -> list[InstalledPack]:
        """Search installed packs by name, description, or tags."""
        ...
```

### InstalledPack Model

```python
class InstalledPack(BaseModel):
    """Represents a pack that has been installed and validated."""

    name: str
    version: str
    description: str
    author: str
    license: str = ""
    tags: list[str] = Field(default_factory=list)
    category: str = ""

    # Skills
    skills: list[PackSkillEntry] = Field(default_factory=list)
    loaded_skill_names: list[str] = Field(default_factory=list)

    # Dependencies
    pack_dependencies: list[PackDependency] = Field(default_factory=list)
    engine_min_version: str = ""

    # Compatibility
    agent_roles: list[str] = Field(default_factory=list)
    capabilities: list[str] = Field(default_factory=list)

    # Installation metadata
    installed_at: datetime
    source: str                   # "local", "marketplace", or URL
    checksum: str = ""            # SHA-256 of the pack directory
    pack_dir: Path                # absolute path on disk

    # Governance
    governance: PackGovernance = Field(default_factory=PackGovernance)

class PackSkillEntry(BaseModel):
    """A skill entry within a pack manifest."""
    name: str
    path: str
    description: str = ""
    required: bool = True

class PackDependency(BaseModel):
    """A dependency on another pack."""
    name: str
    version_constraint: str       # raw semver constraint string

class PackGovernance(BaseModel):
    """Pack-level governance overrides."""
    min_autonomy_level: str = ""
    approval_required_for: list[str] = Field(default_factory=list)
    max_instructions_chars: int = 16000
```

### Pack Loading Flow

```
1. discover(path) or install(source)
   |
2. Parse PACK.yaml -> PackManifest
   |
3. Validate manifest (schema, required fields, name format)
   |
4. For each skill in manifest.skills:
   |   a. Resolve path relative to pack directory
   |   b. Call existing load_from_directory() / load_from_yaml() / load_from_skillmd()
   |   c. Set skill.base_path to the resolved skill directory
   |   d. Register in SkillRegistry with name-scoping: "{pack_name}/{skill_name}"
   |      (also register the bare skill_name as an alias for backward compat)
   |
5. Create InstalledPack record
   |
6. Store in _installed dict
```

### Tenant Enablement

Pack enablement is tenant-scoped, stored in-memory with optional persistence to the database:

```
Tenant A: [kubernetes-operations, data-analysis]
Tenant B: [kubernetes-operations, security-scanning]
Tenant C: []  (no packs enabled = only standalone skills)
```

When `SkillInjector.build_skill_metadata_block()` is called in the context of a tenant, only skills from enabled packs (plus standalone skills) are included. This requires a minor extension to the existing `SkillInjector` to accept a tenant context.

---

## 6. Marketplace API

The Marketplace is an optional remote service for publishing, discovering, and downloading skill packs. It is designed as a set of REST endpoints that can run as a standalone service or as additional routes on the AGENT-33 engine.

### Endpoints

#### Discovery

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/marketplace/packs` | List packs (paginated, filterable by tag/category/author) |
| `GET` | `/v1/marketplace/packs/{name}` | Get pack metadata |
| `GET` | `/v1/marketplace/packs/{name}/versions` | List all versions of a pack |
| `GET` | `/v1/marketplace/packs/{name}/versions/{version}` | Get specific version metadata |
| `GET` | `/v1/marketplace/search` | Search packs by query string |
| `GET` | `/v1/marketplace/categories` | List all categories with pack counts |
| `GET` | `/v1/marketplace/tags` | List popular tags |

#### Installation

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/marketplace/packs/{name}/versions/{version}/download` | Download pack tarball |
| `GET` | `/v1/marketplace/packs/{name}/versions/{version}/checksums` | Get checksum file |
| `POST` | `/v1/marketplace/install` | Install a pack from marketplace (convenience endpoint) |

#### Publishing

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/v1/marketplace/packs` | Publish a new pack |
| `PUT` | `/v1/marketplace/packs/{name}/versions/{version}` | Publish a new version |
| `DELETE` | `/v1/marketplace/packs/{name}/versions/{version}` | Yank a version (soft-delete) |
| `PATCH` | `/v1/marketplace/packs/{name}` | Update pack metadata (description, tags) |

#### Local Registry Management (on-instance)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/v1/packs` | List installed packs |
| `GET` | `/v1/packs/{name}` | Get installed pack details |
| `POST` | `/v1/packs/install` | Install a pack (local path, tarball, or marketplace) |
| `DELETE` | `/v1/packs/{name}` | Uninstall a pack |
| `POST` | `/v1/packs/{name}/enable` | Enable pack for current tenant |
| `POST` | `/v1/packs/{name}/disable` | Disable pack for current tenant |
| `GET` | `/v1/packs/enabled` | List packs enabled for current tenant |
| `POST` | `/v1/packs/{name}/upgrade` | Upgrade to latest/specified version |
| `POST` | `/v1/packs/resolve` | Dry-run dependency resolution |

### Publishing Workflow

```
Author                           Marketplace
  |                                  |
  |  1. Build pack (PACK.yaml +      |
  |     skills + tests)              |
  |                                  |
  |  2. Run pack validation          |
  |     (schema, tests, lint)        |
  |                                  |
  |  3. Generate checksums           |
  |     (CHECKSUMS.sha256)           |
  |                                  |
  |  4. Optionally sign              |
  |     (SIGNATURE.sig)              |
  |                                  |
  |  5. POST /v1/marketplace/packs   |
  |     (multipart: tarball + meta)  |
  |  -------------------------------->
  |                                  |
  |                   6. Validate manifest
  |                   7. Verify checksums
  |                   8. Run security scan
  |                   9. Index for search
  |                  10. Store tarball
  |                                  |
  |  <--- 201 Created (version URL) -|
  |                                  |
```

### Pack Publishing Validation

Before accepting a pack, the marketplace validates:

1. **Schema compliance**: PACK.yaml matches the manifest schema
2. **Name uniqueness**: Pack name is not already taken by another author (or author matches)
3. **Version monotonicity**: New version is strictly higher than the latest existing version
4. **Checksum match**: Uploaded tarball matches declared checksums
5. **Skill validity**: Each declared skill can be parsed without errors
6. **Dependency availability**: All declared pack dependencies exist in the marketplace
7. **Engine version**: Declared min_version is a valid AGENT-33 release
8. **Security scan**: No embedded credentials, suspicious commands, or known CVE patterns in scripts
9. **Size limits**: Total pack size < 50MB, individual skill instructions < 64KB

### Rating & Review System (Optional, Deferred)

A basic quality signal system can be added later:

- **Download count**: Automatically tracked per version
- **Star rating**: 1-5 stars per user (one rating per user per pack)
- **Compatibility reports**: Users can flag "works" or "broken" per engine version
- **Automated quality score**: Based on validation results, documentation completeness, test coverage

This is deferred to a v2 of the marketplace since it requires user identity management beyond tenant auth.

---

## 7. Agent Skills Standard Compatibility

### SkillsBench Skill Format

SkillsBench organizes skills as directories:

```
skills/
  {skill_name}/
    SKILL.md           # YAML frontmatter + markdown body
    scripts/           # Optional bundled scripts
    references/        # Optional reference files
    assets/            # Optional assets (not in AGENT-33)
```

The SKILL.md format is identical to AGENT-33's -- both follow the Anthropic standard. Key differences:

| Aspect | AGENT-33 | SkillsBench |
|--------|----------|-------------|
| Frontmatter fields | 20+ fields including governance | Lighter: name, description, version, tags |
| `assets/` directory | Not auto-discovered | Used for skill-bundled data files |
| Tool configuration | `allowed_tools`, `disallowed_tools`, `tool_parameter_defaults` | Not in format (tools are system-level) |
| Governance | Full (`invocation_mode`, `autonomy_level`, etc.) | None |
| Dependencies | `SkillDependency` model | None |

### Adapter Layer

An adapter converts external skill formats into AGENT-33's `SkillDefinition` model:

```python
class SkillFormatAdapter(ABC):
    """Base class for adapting external skill formats to SkillDefinition."""

    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Check if this adapter can handle the given path."""
        ...

    @abstractmethod
    def load(self, path: Path) -> list[SkillDefinition]:
        """Load and convert skills from the given path."""
        ...

class SkillsBenchAdapter(SkillFormatAdapter):
    """Adapt SkillsBench skill directories to AGENT-33 SkillDefinitions.

    Handles:
    - SKILL.md with Anthropic frontmatter (native, mostly passthrough)
    - `assets/` directory mapped to `references`
    - Missing governance fields filled with safe defaults
    """
    ...

class MCPToolAdapter(SkillFormatAdapter):
    """Adapt MCP tool definitions to AGENT-33 SkillDefinitions.

    Converts MCP tool JSON Schema definitions into skill definitions
    with the tool's description as instructions and its parameters
    encoded as tool_parameter_defaults.
    """
    ...
```

### Import/Export Capabilities

**Import**: Load skills from external formats into an AGENT-33 pack:

```python
class PackImporter:
    """Import external skill sources into AGENT-33 pack format."""

    def __init__(self, adapters: list[SkillFormatAdapter]) -> None:
        self._adapters = adapters

    def import_directory(self, source: Path, pack_name: str) -> Path:
        """Convert a directory of external skills into a PACK.yaml pack.

        Returns the path to the generated pack directory.
        """
        ...

    def import_skillsbench_task(self, task_dir: Path, pack_name: str) -> Path:
        """Import a SkillsBench task's bundled skills as a pack."""
        ...

    def import_mcp_tools(self, server_tools: list[dict], pack_name: str) -> Path:
        """Import MCP tool definitions as a skill pack."""
        ...
```

**Export**: Generate external-compatible skill directories from an AGENT-33 pack:

```python
class PackExporter:
    """Export AGENT-33 packs to external formats."""

    def export_skillsbench(self, pack: InstalledPack, output_dir: Path) -> Path:
        """Export a pack's skills in SkillsBench-compatible format.

        Strips AGENT-33-specific governance fields from frontmatter,
        maps templates/ to assets/, generates minimal SKILL.md files.
        """
        ...

    def export_manifest_only(self, pack: InstalledPack) -> dict:
        """Export pack metadata as a JSON-serializable dict."""
        ...
```

### Mapping Table

| AGENT-33 Field | SkillsBench Field | MCP Tool Field | Notes |
|---------------|-------------------|----------------|-------|
| `name` | `name` (frontmatter) | `name` (tool schema) | Direct mapping |
| `description` | `description` (frontmatter) | `description` (tool schema) | Direct mapping |
| `version` | `version` (frontmatter) | N/A | Default "1.0.0" for MCP |
| `instructions` | markdown body | Generated from description + parameters | MCP tools need instruction synthesis |
| `tags` | `tags` (frontmatter) | N/A | Empty for MCP imports |
| `allowed_tools` | N/A | N/A | AGENT-33 specific |
| `disallowed_tools` | N/A | N/A | AGENT-33 specific |
| `invocation_mode` | N/A | N/A | Default BOTH |
| `execution_context` | N/A | N/A | Default INLINE |
| `autonomy_level` | N/A | N/A | Default None |
| `scripts_dir` | `scripts/` | N/A | Auto-discovered |
| `templates_dir` | N/A (use `assets/`) | N/A | Map assets -> templates on import |
| `references` | `references/` | N/A | Auto-discovered |

---

## 8. Integration Points

### 8.1 Integration with SkillRegistry

The PackRegistry is a higher-level manager that delegates skill storage to the existing SkillRegistry. The relationship is compositional, not hierarchical:

```
PackRegistry
  |
  +-- owns --> InstalledPack records (pack metadata, versions, tenant enablement)
  |
  +-- delegates to --> SkillRegistry (actual skill storage, search, progressive disclosure)
```

**Loading**: When a pack is installed, its skills are loaded and registered in SkillRegistry using the existing `register()` method. Skill names may be qualified with pack name prefix (`pack_name/skill_name`) to avoid collisions between packs that define skills with the same name.

**Unloading**: When a pack is uninstalled, its skills are removed from SkillRegistry via `remove()`.

**Search**: `SkillRegistry.search()`, `find_by_tag()`, and `find_by_tool()` continue to work across all registered skills regardless of pack origin. A new `find_by_pack(pack_name)` method is added to filter skills from a specific pack.

**Progressive Disclosure**: L0/L1/L2 work unchanged. Skills loaded from packs are indistinguishable from standalone skills once registered.

**Matching**: The `SkillMatcher` works with all registered skills. Pack metadata does not affect the 4-stage matching pipeline -- only individual skill metadata matters.

### 8.2 Integration with PluginRegistry (H02)

Packs and plugins are complementary concepts:

| Concept | Purpose | Granularity |
|---------|---------|-------------|
| **Skill** | Domain knowledge + tool config for agent prompts | Single capability |
| **Pack** | Distributable bundle of related skills | Collection of skills |
| **Plugin** | Executable code extension (hooks, tools, adapters) | Runtime code module |

A pack MAY declare plugin dependencies:

```yaml
# In PACK.yaml
dependencies:
  plugins:
    - name: kubernetes-cli-tools
      version: "^1.0.0"
```

When a pack is installed, the PackInstaller checks that required plugins are available in the PluginRegistry. Plugins provide runtime capabilities (custom tools, middleware hooks) that skills within the pack may reference.

**Example**: A "kubernetes-operations" pack might contain skills that reference a `kubectl` tool. The pack declares a dependency on a `kubernetes-cli-tools` plugin that registers the `kubectl` tool in the ToolRegistry.

### 8.3 Integration with Hook Framework (H01)

Packs emit lifecycle events that hooks can observe:

| Event | Fired When | Hook Context |
|-------|------------|-------------|
| `pack.installed` | Pack installation completes | `{pack_name, version, skills_loaded}` |
| `pack.uninstalled` | Pack removal completes | `{pack_name, version}` |
| `pack.enabled` | Pack enabled for a tenant | `{pack_name, tenant_id}` |
| `pack.disabled` | Pack disabled for a tenant | `{pack_name, tenant_id}` |
| `pack.upgraded` | Pack version changes | `{pack_name, old_version, new_version}` |
| `pack.skill_loaded` | Individual skill from pack registered | `{pack_name, skill_name, version}` |
| `pack.validation_failed` | Pack validation rejects a manifest | `{pack_name, errors}` |

Hooks can intercept pack operations. For example, a security hook might block installation of packs from untrusted authors, or an audit hook might log all pack enablement changes.

### 8.4 Integration with Startup (main.py lifespan)

Pack loading is added to the lifespan initialization, after SkillRegistry setup and before the agent-workflow bridge:

```
... → SkillRegistry → SkillInjector → PackRegistry → Agent-Workflow Bridge → ...
```

```python
# In main.py lifespan, after skill_injector initialization:
from agent33.packs.registry import PackRegistry

pack_registry = PackRegistry(
    packs_dir=Path(settings.pack_definitions_dir),
    skill_registry=skill_registry,
)
pack_count = pack_registry.discover()
logger.info("pack_registry_loaded", count=pack_count)
app.state.pack_registry = pack_registry
```

### 8.5 Integration with SkillMatcher

When the `SkillMatcher` is reindexed, it automatically picks up skills from packs since they are in the same `SkillRegistry`. No changes to the matching pipeline are needed.

However, pack metadata can enhance matching:

- **Category hints**: Skills from a pack tagged "infrastructure" get a small relevance boost for infra-related queries
- **Co-occurrence**: If one skill from a pack is selected, sibling skills get a small boost (they are likely related)

These enhancements are optional and deferred to v2.

---

## 9. Security Model

### Threat Model

| Threat | Mitigation |
|--------|-----------|
| **Malicious skill content** (prompt injection via instructions) | Existing prompt injection detection in security module; pack validation scans instructions for known attack patterns |
| **Malicious scripts** (code execution in bundled scripts) | Scripts execute under existing SandboxConfig; pack validation scans for dangerous patterns (rm -rf, credential access) |
| **Dependency confusion** (attacker publishes pack with name similar to internal pack) | Namespace validation: marketplace packs use `author/name` format; local packs use bare `name` |
| **Supply chain attack** (compromised pack version) | Checksum verification via CHECKSUMS.sha256; optional GPG/age signatures; lock files pin exact versions |
| **Privilege escalation** (pack grants itself higher autonomy) | Pack governance cannot exceed the installing tenant's autonomy level; `approval_required_for` is additive only |
| **Tenant isolation bypass** (pack leaks skills across tenants) | Pack enablement is per-tenant; disabled packs' skills are not injected |
| **Path traversal in pack contents** | Existing path traversal protection in `SkillRegistry.get_resource()`; pack extraction validates all paths are within pack directory |
| **Oversized pack causing DoS** | Size limits enforced at install time (50MB total, 64KB per instruction) |

### Checksum Verification

```
CHECKSUMS.sha256 format:

sha256:a1b2c3d4...  PACK.yaml
sha256:e5f6a7b8...  skills/kubernetes-deploy/SKILL.md
sha256:c9d0e1f2...  skills/kubernetes-deploy/scripts/deploy.sh
...
```

During installation, the `PackInstaller`:
1. Reads `CHECKSUMS.sha256` from the pack
2. Computes SHA-256 of every file in the pack
3. Rejects installation if any checksum mismatches
4. Stores the pack's overall checksum in the lock file

### Capability Grants

When a pack declares `compatibility.capabilities`, the installer verifies that the target agents actually have those capabilities:

```python
def _check_capability_compatibility(
    self, pack: PackManifest, available_capabilities: set[str]
) -> list[str]:
    """Return list of missing capabilities."""
    required = set(pack.compatibility.capabilities)
    missing = required - available_capabilities
    return sorted(missing)
```

Missing capabilities are reported as warnings (not errors) since an agent might gain capabilities at runtime.

---

## 10. File Plan

### New Files

| File | Responsibility | Est. Lines |
|------|---------------|-----------|
| `engine/src/agent33/packs/__init__.py` | Package marker | 5 |
| `engine/src/agent33/packs/manifest.py` | `PackManifest` Pydantic model, PACK.yaml parsing, validation | 180 |
| `engine/src/agent33/packs/models.py` | `InstalledPack`, `PackSkillEntry`, `PackDependency`, `PackGovernance`, `InstallResult`, `PackSource` | 150 |
| `engine/src/agent33/packs/registry.py` | `PackRegistry` -- discovery, install, uninstall, enable/disable, upgrade, query | 350 |
| `engine/src/agent33/packs/resolver.py` | `VersionConstraint`, `DependencyResolver`, `ResolutionResult`, `ConflictDetail` | 280 |
| `engine/src/agent33/packs/loader.py` | `PackLoader` -- parse PACK.yaml, load skills, validate | 150 |
| `engine/src/agent33/packs/installer.py` | `PackInstaller` -- download, extract, verify checksums, stage, commit | 200 |
| `engine/src/agent33/packs/adapters.py` | `SkillFormatAdapter`, `SkillsBenchAdapter`, `MCPToolAdapter`, `PackImporter`, `PackExporter` | 250 |
| `engine/src/agent33/packs/routes.py` | FastAPI routes for local pack management (8 endpoints) | 200 |
| **Total new source** | | **~1,765** |

### Modified Files

| File | Change |
|------|--------|
| `engine/src/agent33/main.py` | Add PackRegistry initialization to lifespan (10-15 lines) |
| `engine/src/agent33/config.py` | Add `pack_definitions_dir`, `pack_marketplace_url`, `pack_max_size_mb` settings (5 lines) |
| `engine/src/agent33/skills/registry.py` | Add `find_by_pack(pack_name)` method (10 lines) |
| `engine/src/agent33/skills/injection.py` | Accept optional `tenant_id` for tenant-scoped skill filtering (15 lines) |
| `engine/src/agent33/skills/loader.py` | Add `assets/` directory auto-discovery (5 lines) |

### Test Files

| File | Tests | Scope |
|------|-------|-------|
| `engine/tests/test_pack_manifest.py` | 15-18 | PACK.yaml parsing, validation, field defaults, schema errors |
| `engine/tests/test_pack_models.py` | 10-12 | Model serialization, validation, defaults |
| `engine/tests/test_pack_registry.py` | 18-22 | Discovery, install, uninstall, enable/disable, upgrade, search, tenant isolation |
| `engine/tests/test_pack_resolver.py` | 15-18 | Constraint parsing, resolution algorithm, conflict detection, lock file |
| `engine/tests/test_pack_loader.py` | 10-12 | Pack loading from directory, skill loading, error handling |
| `engine/tests/test_pack_installer.py` | 10-12 | Checksum verification, staging, extraction, size limits |
| `engine/tests/test_pack_adapters.py` | 12-15 | SkillsBench import, MCP import, export, format detection |
| `engine/tests/test_pack_routes.py` | 10-12 | Endpoint CRUD, auth, tenant scoping |
| **Total new tests** | **~100-121** | |

### Estimated Total Effort

| Category | Count |
|----------|-------|
| New source files | 9 |
| Modified source files | 5 |
| New test files | 8 |
| New source lines (est.) | ~1,765 |
| New test lines (est.) | ~2,000 |
| New API endpoints | 8 (local) + 12 (marketplace, deferred) |
| Sessions estimate | 2-3 |

---

## 11. Migration Strategy

### Phase 1: Core Pack Infrastructure (Session 1)

**Goal**: Pack manifest, models, loader, registry (local only)

1. Create `packs/` package with `manifest.py`, `models.py`, `loader.py`, `registry.py`
2. Implement PACK.yaml parsing and validation
3. Implement `PackRegistry.discover()` and `PackRegistry.load_pack()`
4. Wire into `main.py` lifespan
5. Write tests for manifest parsing, loading, and registry operations

**Deliverables**: Local packs can be discovered and loaded from `pack_definitions_dir`. Skills appear in SkillRegistry. No dependency resolution yet.

### Phase 2: Dependency Resolution + Lock Files (Session 1-2)

**Goal**: Semver constraints, resolution algorithm, lock file generation

1. Implement `VersionConstraint.parse()` and `satisfies()`
2. Implement `DependencyResolver.resolve()`
3. Implement lock file generation and consumption
4. Implement conflict detection and reporting
5. Write resolver tests (happy path, conflicts, circular, missing)

**Deliverables**: Pack installation resolves dependencies. Lock files ensure reproducible deployments.

### Phase 3: Install/Uninstall + Tenant Enablement (Session 2)

**Goal**: Full pack lifecycle with tenant scoping

1. Implement `PackInstaller` (download, extract, verify, stage)
2. Implement `PackRegistry.install()`, `uninstall()`, `enable()`, `disable()`
3. Implement checksum verification
4. Add `find_by_pack()` to SkillRegistry
5. Add tenant-scoped filtering to SkillInjector
6. Write lifecycle tests

**Deliverables**: Packs can be installed from local paths, enabled/disabled per tenant. Uninstallation cleans up skills.

### Phase 4: Routes + Adapters (Session 2-3)

**Goal**: API endpoints and external format compatibility

1. Implement `packs/routes.py` with 8 local management endpoints
2. Implement `SkillsBenchAdapter` and `MCPToolAdapter`
3. Implement `PackImporter` and `PackExporter`
4. Add config settings
5. Write route tests and adapter tests

**Deliverables**: Full local pack management via API. SkillsBench and MCP skills can be imported as packs.

### Phase 5: Marketplace (Deferred)

**Goal**: Remote pack registry for sharing

This phase adds the marketplace server endpoints and the client-side marketplace integration in `PackInstaller`. It is deferred until the local pack system proves its value.

---

## 12. Test Plan

### Test Categories

**Unit Tests**: Each module has focused unit tests covering:
- Model validation (valid inputs, invalid inputs, edge cases)
- Parsing (well-formed YAML, malformed YAML, missing fields, extra fields)
- Algorithm correctness (constraint parsing, version comparison, resolution)
- Error handling (file not found, permission denied, corrupt data)

**Integration Tests**: Cross-module tests covering:
- Pack discovery -> skill loading -> registry registration
- Install -> resolve dependencies -> load skills -> verify in registry
- Enable/disable -> verify tenant isolation in SkillInjector
- Uninstall -> verify skills removed from registry
- Import external format -> verify pack structure

**Security Tests**: Focused on the threat model:
- Path traversal in pack contents
- Checksum mismatch rejection
- Oversized pack rejection
- Privilege escalation prevention (governance constraints)
- Namespace collision handling

### Test Quality Standards (per CLAUDE.md Anti-Corner-Cutting Rules)

Every test will:
1. **Assert on behavior**, not just route existence or infrastructure errors
2. **Use specific assertions** (no `assert status in (200, 201)` patterns)
3. **Mock only infrastructure dependencies** (database, filesystem), not the code under test
4. **Test error paths** as thoroughly as happy paths
5. **Verify state changes** (skills appear/disappear in registry, tenant enablement changes)

### Key Test Scenarios

**Pack Manifest Tests**:
- Valid PACK.yaml with all fields -> parses correctly
- Missing required field (name, version, skills) -> validation error with specific message
- Invalid semver version -> validation error
- Empty skills list -> validation error
- Skill path that does not exist -> load error
- Schema version "2" (unsupported) -> graceful error

**Dependency Resolver Tests**:
- Single pack, no dependencies -> resolves immediately
- Linear chain (A -> B -> C) -> resolves in order
- Diamond dependency (A -> B, A -> C, both -> D) -> resolves D once
- Version conflict (A needs D ^1.0, B needs D ^2.0) -> reports specific conflict
- Circular dependency (A -> B -> A) -> detects and reports
- Missing pack -> reports with available alternatives
- Lock file consumption -> skips resolution, verifies checksums
- Constraint syntax: ^, ~, >=, <, exact, * -> all parse correctly

**Pack Registry Tests**:
- Discover packs from directory -> all valid packs loaded
- Install from local path -> skills appear in SkillRegistry
- Uninstall with dependents -> blocked with error message
- Uninstall without dependents -> skills removed from SkillRegistry
- Enable for tenant A -> skills visible for A, invisible for B
- Disable for tenant -> skills invisible for that tenant
- Upgrade -> old skills removed, new skills loaded
- Downgrade -> version reverts, skills match old version
- Search by name/tag/description -> correct results

**Adapter Tests**:
- Import SkillsBench SKILL.md -> AGENT-33 SkillDefinition with correct field mapping
- Import SkillsBench with assets/ -> mapped to references
- Import MCP tool definition -> SkillDefinition with generated instructions
- Export AGENT-33 skill to SkillsBench format -> stripped governance fields
- Unrecognized format -> adapter reports "cannot handle"

**Route Tests**:
- `GET /v1/packs` -> list installed packs with pagination
- `POST /v1/packs/install` with valid path -> 201 with pack details
- `POST /v1/packs/install` with invalid path -> 400 with error
- `DELETE /v1/packs/{name}` -> 204, skills removed
- `DELETE /v1/packs/{name}` with dependents -> 409 conflict
- `POST /v1/packs/{name}/enable` -> 200, pack enabled for current tenant
- `POST /v1/packs/{name}/enable` (already enabled) -> 200 (idempotent)
- All endpoints without auth -> 401
- Tenant A cannot see Tenant B's enabled packs

---

## Appendix A: Config Settings

```python
# In config.py Settings class:
pack_definitions_dir: str = "packs"
pack_marketplace_url: str = ""           # empty = marketplace disabled
pack_max_size_mb: int = 50
pack_lock_file: str = "PACK.lock"
pack_checksums_required: bool = False     # True for production
pack_signature_required: bool = False     # True for high-security deployments
```

## Appendix B: Relationship to PHASE-29-33-WORKFLOW-PLAN.md

From the workflow plan, Phase 33 (Task T35) specifies:

> **Outputs**: Agent Skills-compatible packs, distribution, versioning, capability discovery, marketplace

This architecture document covers all specified outputs:

| Output | Section |
|--------|---------|
| Agent Skills-compatible packs | Section 7 (Agent Skills Standard Compatibility) |
| Distribution | Section 6 (Marketplace API) + Section 5 (Pack Registry) |
| Versioning | Section 4 (Semver Dependency Resolution) |
| Capability discovery | Section 3 (Pack Manifest compatibility fields) + Section 5 (search) |
| Marketplace | Section 6 (Marketplace API) |

The plan estimates 7-9 new files, 70-90 tests, 6-8 endpoints, and 2-3 sessions. This architecture aligns with those estimates: 9 new source files, ~100-121 tests, 8 local endpoints (12 marketplace endpoints deferred), and a 2-3 session implementation timeline.

## Appendix C: Open Questions

1. **Namespace format for marketplace packs**: Should marketplace packs use `author/pack-name` format (like npm scoped packages) or flat names with ownership verification (like PyPI)?

   **Recommendation**: Use `author/pack-name` for marketplace packs and bare `pack-name` for local packs. This avoids the name-squatting problem while keeping local usage simple.

2. **Pack-level vs skill-level versioning**: If a pack is at version 2.0.0, what version do individual skills within it have?

   **Recommendation**: Individual skills retain their own version fields. The pack version tracks the bundle's release cadence. When a pack is loaded, skill versions are informational only -- the pack version is what dependency resolution operates on.

3. **Marketplace hosting**: Should the marketplace be a separate service or part of the AGENT-33 engine?

   **Recommendation**: Start as routes within the engine (same FastAPI app) for simplicity. Extract to a standalone service if/when scale demands it.

4. **Backward compatibility period**: How long do we support standalone skills (not in packs) after packs are available?

   **Recommendation**: Indefinitely. Standalone skills are a valid deployment model for small installations. Packs are an organizational layer, not a replacement.

5. **Python package dependencies**: How are `compatibility.python_packages` enforced?

   **Recommendation**: At installation time, check `importlib.metadata.version()` for each declared package. Issue warnings for missing packages but do not block installation. This matches the existing optional-dependency pattern in AGENT-33 (e.g., PyNaCl, structlog).
