# OpenClaw Tracks 3-6: Plugin Lifecycle, Pack Marketplace, Safe Mutation, Backup & Restore — Architecture

Date: 2026-03-10
Session: 59
Status: Research / pre-implementation

## 1. Scope

This document covers the architecture for OpenClaw parity tracks 3 through 6:

| Track | Title | Backlog items | Core outcome |
| --- | --- | --- | --- |
| 3 | Plugin Lifecycle Platform | OC-PLUG-001 through OC-PLUG-018 | Install, update, doctor, config persistence, health UX |
| 4 | Pack Distribution Platform | OC-PACK-001 through OC-PACK-016 | Marketplace provenance, tenant enablement matrix, rollback |
| 5 | Safe Mutation and Process Control | OC-MUTATE-001 through OC-MUTATE-016 | `apply_patch` runtime tool, process manager, governance |
| 6 | Backup and Restore Confidence | OC-BACKUP-001 through OC-BACKUP-016 | Archive-level backup create/verify/restore |

## 2. Existing Codebase Inventory

### Plugin System

| File | Role |
| --- | --- |
| `engine/src/agent33/api/routes/plugins.py` | FastAPI routes: list, detail, enable, disable, config, health, search, discover |
| `engine/src/agent33/plugins/` (presumed) | Plugin registry, models, API models, state machine |

Current state: Plugins can be discovered, toggled, and searched. Missing: install from path/archive/registry, update flows, version pinning, config persistence, doctor diagnostics, permission visibility, lifecycle events.

### Pack System

| File | Role |
| --- | --- |
| `engine/src/agent33/packs/registry.py` | `PackRegistry` — discover, install, uninstall, upgrade, downgrade, enable/disable (tenant-scoped) |
| `engine/src/agent33/packs/marketplace.py` | `LocalPackMarketplace` — filesystem-backed catalog, version resolution |
| `engine/src/agent33/packs/provenance.py` | HMAC-SHA256 signing, trust policy evaluation |
| `engine/src/agent33/packs/models.py` | `InstalledPack`, `PackSource`, `PackStatus`, `PackGovernance` |
| `engine/src/agent33/packs/manifest.py` | `PackManifest` parsing |
| `engine/src/agent33/packs/version.py` | Semver parsing and comparison |
| `engine/src/agent33/packs/conflicts.py` | Conflict detection |
| `engine/src/agent33/packs/adapter.py` | Format adapters |
| `engine/src/agent33/api/routes/packs.py` | FastAPI routes: list, install, uninstall, enable, disable, search |
| `engine/src/agent33/api/routes/marketplace.py` | Marketplace browsing routes |

Current state: Local install, upgrade, downgrade, tenant enablement, provenance signing, and conflict detection exist. Missing: remote marketplace sources, index fetch/caching, signature verification UI, trust policy management UI, rollback with preserved enablement, health status, audit trails.

### Tool System (Mutation Surface)

| File | Role |
| --- | --- |
| `engine/src/agent33/tools/governance.py` | `ToolGovernance` — permission checks, policy evaluation, audit logging |
| `engine/src/agent33/tools/approvals.py` | `ToolApprovalService` — approval request/consume lifecycle |
| `engine/src/agent33/api/routes/tool_approvals.py` | Approval management API |
| `engine/src/agent33/autonomy/` | Budget enforcement, preflight checks, runtime enforcer |
| `engine/src/agent33/execution/` | Code execution with sandbox, validation, adapters |

Current state: Governance, approvals, and autonomy enforcement are mature. Missing: `apply_patch` as a first-class tool, filesystem boundary enforcement for patches, dry-run preview, mutation audit trail, process manager.

### Backup Surface

| File | Role |
| --- | --- |
| `engine/src/agent33/api/routes/improvements.py` | Improvement-subsystem-specific backup/restore |

Current state: Backup is limited to improvement learning state. No platform-level backup manifest, archive creation, verification, or restore planning.

---

## 3. Track Phase 3: Plugin Lifecycle Platform

### 3.1 Problem

AGENT-33 plugins can be discovered and toggled, but operators cannot install a plugin from a path or archive, pin versions, persist config changes, diagnose failures, or understand permissions. This makes the plugin surface feel like a read-only inventory rather than a manageable extension platform.

### 3.2 Plugin Install Pipeline

```python
# engine/src/agent33/plugins/installer.py

class PluginInstallSource(BaseModel):
    """Describes where a plugin comes from."""
    source_type: str  # "local", "archive", "registry"
    path: str = ""
    archive_path: str = ""
    registry_spec: str = ""  # e.g. "my-plugin@1.2.0"
    version_pin: str = ""    # exact version or dist-tag
    prerelease: bool = False

class PluginInstallResult(BaseModel):
    success: bool
    plugin_name: str
    version: str = ""
    errors: list[str] = []
    warnings: list[str] = []
    install_provenance: PluginInstallProvenance | None = None

class PluginInstallProvenance(BaseModel):
    """Records how and when a plugin was installed."""
    source_type: str
    source_path: str
    version: str
    installed_at: datetime
    integrity_hash: str = ""
    installer_identity: str = ""

class PluginInstaller:
    """Handles plugin installation from multiple source types."""

    def __init__(self, plugin_registry, plugins_dir: Path) -> None: ...

    def install_from_local(self, path: Path, *, version_pin: str = "") -> PluginInstallResult: ...
    def install_from_archive(self, archive_path: Path) -> PluginInstallResult: ...
    def install_from_registry(self, spec: str, *, prerelease: bool = False) -> PluginInstallResult: ...
    def update(self, name: str, *, target_version: str = "") -> PluginInstallResult: ...
    def update_all(self) -> list[PluginInstallResult]: ...
    def link(self, name: str, local_path: Path) -> PluginInstallResult: ...
```

### 3.3 Plugin Config Persistence

```python
# engine/src/agent33/plugins/config_store.py

class PluginConfigStore:
    """Persists plugin configuration to disk."""

    def __init__(self, config_dir: Path) -> None:
        self._config_dir = config_dir

    def load(self, plugin_name: str) -> dict[str, Any]:
        """Load persisted config for a plugin."""
        ...

    def save(self, plugin_name: str, config: dict[str, Any]) -> None:
        """Persist config updates to disk."""
        ...

    def delete(self, plugin_name: str) -> None:
        """Remove persisted config on uninstall."""
        ...
```

Config is stored as `{config_dir}/{plugin_name}/config.json`. The plugin registry loads persisted config on startup and merges it with defaults from the plugin manifest's `configSchema`.

### 3.4 Plugin Doctor

```python
# engine/src/agent33/plugins/doctor.py

class PluginDoctorCheck(BaseModel):
    name: str
    status: str  # "ok", "warn", "error"
    message: str
    remediation: str = ""

class PluginDoctorReport(BaseModel):
    plugin_name: str
    checks: list[PluginDoctorCheck]
    overall_status: str  # "healthy", "degraded", "broken"

class PluginDoctor:
    """Runs diagnostic checks on installed plugins."""

    def diagnose(self, plugin_name: str) -> PluginDoctorReport:
        """Run all checks for a single plugin."""
        ...

    def diagnose_all(self) -> list[PluginDoctorReport]:
        """Run diagnostics across all installed plugins."""
        ...
```

Checks include:
- Manifest validity
- Required dependencies available
- Config schema matches persisted config
- Health check passes
- Permission grants are satisfied
- No version conflicts with other plugins

### 3.5 Plugin Health and Permissions

Extend the existing plugin model:

```python
class PluginHealthStatus(BaseModel):
    healthy: bool
    last_check: datetime | None = None
    last_failure: str = ""
    failure_count: int = 0

class PluginPermissionGrant(BaseModel):
    permission: str
    granted: bool
    reason: str = ""
```

### 3.6 Plugin Lifecycle Events

```python
class PluginLifecycleEvent(BaseModel):
    event_type: str  # "installed", "enabled", "disabled", "updated", "uninstalled", "error"
    plugin_name: str
    version: str = ""
    timestamp: datetime
    details: dict[str, Any] = {}
```

Events are emitted through the existing hook framework and stored for audit.

### 3.7 API Endpoints

Extend existing `/v1/plugins` router:

```
POST   /v1/plugins/install          — install from source
POST   /v1/plugins/{name}/update    — update to latest or pinned version
POST   /v1/plugins/update-all       — bulk update
POST   /v1/plugins/{name}/link      — link local dev path
PUT    /v1/plugins/{name}/config    — persist config (already exists, needs persistence backend)
GET    /v1/plugins/{name}/doctor    — run diagnostics
GET    /v1/plugins/doctor           — diagnostics for all plugins
GET    /v1/plugins/{name}/permissions — permission grants and denials
GET    /v1/plugins/{name}/routes    — exposed routes inventory
GET    /v1/plugins/{name}/commands  — exposed commands inventory
GET    /v1/plugins/{name}/events    — lifecycle event history
POST   /v1/plugins/{name}/reload    — hot-reload with diagnostics
```

### 3.8 New Files

```
engine/src/agent33/plugins/installer.py        — install pipeline
engine/src/agent33/plugins/config_store.py     — config persistence
engine/src/agent33/plugins/doctor.py           — diagnostic checks
engine/src/agent33/plugins/events.py           — lifecycle events
```

### 3.9 Modified Files

```
engine/src/agent33/plugins/models.py           — add HealthStatus, PermissionGrant
engine/src/agent33/plugins/registry.py         — integrate installer, config store, events
engine/src/agent33/plugins/api_models.py       — add install/update/doctor response models
engine/src/agent33/api/routes/plugins.py       — add new endpoints
engine/src/agent33/main.py                     — init config store and event emitter
```

### 3.10 Test Files

```
engine/tests/test_plugin_installer.py          — install from local/archive/registry
engine/tests/test_plugin_config_store.py       — config persistence lifecycle
engine/tests/test_plugin_doctor.py             — diagnostic check assertions
engine/tests/test_plugin_events.py             — lifecycle event emission
engine/tests/test_plugin_routes_lifecycle.py   — API endpoint integration tests
```

---

## 4. Track Phase 4: Pack Distribution Platform

### 4.1 Problem

AGENT-33's pack system supports local install, tenant enablement, and HMAC signing, but lacks remote marketplace integration, operator-visible trust management, conflict resolution UX, pack preview, rollback with preserved enablement, and per-pack audit trails.

### 4.2 Remote Marketplace Sources

```python
# engine/src/agent33/packs/remote_marketplace.py

class RemoteMarketplaceConfig(BaseModel):
    """Configuration for a remote pack marketplace."""
    name: str
    url: str
    auth_token: str = ""
    trust_level: TrustLevel = TrustLevel.COMMUNITY
    cache_ttl_seconds: int = 3600

class RemotePackIndex(BaseModel):
    """Cached remote marketplace index."""
    source: str
    fetched_at: datetime
    packs: list[MarketplacePackRecord]

class RemotePackMarketplace:
    """HTTP-backed marketplace for remote pack discovery and download."""

    def __init__(self, config: RemoteMarketplaceConfig) -> None: ...

    async def fetch_index(self) -> RemotePackIndex:
        """Fetch and cache the remote index."""
        ...

    async def download_pack(self, name: str, version: str = "") -> Path:
        """Download a pack archive to a temp directory."""
        ...

    def invalidate_cache(self) -> None:
        """Force re-fetch on next access."""
        ...
```

The existing `LocalPackMarketplace` and new `RemotePackMarketplace` both implement a common interface so the `PackRegistry.install()` method can resolve from either.

### 4.3 Marketplace Aggregator

```python
# engine/src/agent33/packs/marketplace_aggregator.py

class MarketplaceAggregator:
    """Aggregates local and remote marketplace sources."""

    def __init__(
        self,
        local: LocalPackMarketplace | None = None,
        remotes: list[RemotePackMarketplace] | None = None,
    ) -> None: ...

    async def search(self, query: str) -> list[MarketplacePackRecord]: ...
    async def get_pack(self, name: str) -> MarketplacePackRecord | None: ...
    async def resolve(self, name: str, version: str = "") -> Path | None: ...
```

### 4.4 Trust Policy Management

Extend existing `PackTrustPolicy` with operator-managed configuration:

```python
# Additions to engine/src/agent33/packs/provenance.py or new trust_manager.py

class TrustPolicyManager:
    """Manages pack trust policies with persistence."""

    def __init__(self, config_path: Path) -> None: ...

    def get_policy(self) -> PackTrustPolicy: ...
    def update_policy(self, updates: dict[str, Any]) -> PackTrustPolicy: ...
    def add_trusted_signer(self, signer_id: str) -> None: ...
    def remove_trusted_signer(self, signer_id: str) -> None: ...
    def set_min_trust_level(self, level: TrustLevel) -> None: ...
```

### 4.5 Tenant Enablement Matrix

The existing `PackRegistry` has `enable(name, tenant_id)` and `disable(name, tenant_id)`. The matrix view surfaces this as:

```python
class TenantEnablementMatrix(BaseModel):
    """Matrix of pack enablement across tenants."""
    packs: list[str]
    tenants: list[str]
    matrix: dict[str, dict[str, bool]]  # pack_name -> tenant_id -> enabled
```

API endpoint:
```
GET /v1/packs/enablement-matrix    — returns the full matrix
PUT /v1/packs/enablement-matrix    — bulk update enablement
```

### 4.6 Pack Rollback

```python
# engine/src/agent33/packs/rollback.py

class PackRollbackManager:
    """Manages rollback to previous pack versions."""

    def __init__(self, pack_registry: PackRegistry, archive_dir: Path) -> None: ...

    def archive_current(self, pack_name: str) -> Path:
        """Archive the current version before upgrade."""
        ...

    def rollback(self, pack_name: str) -> InstallResult:
        """Rollback to the previously archived version, preserving tenant enablement."""
        ...

    def list_archived_versions(self, pack_name: str) -> list[str]:
        """List available rollback versions."""
        ...
```

Key requirement: tenant enablement must be preserved across rollback. The rollback manager captures the enablement state before uninstall and restores it after reinstall.

### 4.7 Pack Health and Audit

```python
class PackHealthStatus(BaseModel):
    pack_name: str
    healthy: bool
    last_smoke_check: datetime | None = None
    skill_load_errors: list[str] = []
    dependency_issues: list[str] = []

class PackAuditEntry(BaseModel):
    pack_name: str
    action: str  # "installed", "upgraded", "downgraded", "uninstalled", "enabled", "disabled", "rollback"
    version: str = ""
    tenant_id: str = ""
    timestamp: datetime
    actor: str = ""
    details: dict[str, Any] = {}
```

### 4.8 API Endpoints

Extend existing `/v1/packs` router:

```
GET    /v1/packs/marketplace            — aggregated marketplace listing (local + remote)
GET    /v1/packs/marketplace/{name}     — pack detail with README, manifest, skills
POST   /v1/packs/marketplace/refresh    — force index refresh
GET    /v1/packs/{name}/trust           — trust and provenance detail
PUT    /v1/packs/trust-policy           — update trust policy
GET    /v1/packs/enablement-matrix      — tenant enablement matrix
PUT    /v1/packs/enablement-matrix      — bulk enablement update
GET    /v1/packs/{name}/conflicts       — conflict detection with resolution guidance
POST   /v1/packs/{name}/rollback        — rollback to prior version
GET    /v1/packs/{name}/health          — health status and smoke check
GET    /v1/packs/{name}/audit           — audit trail
GET    /v1/packs/{name}/preview         — preview before install (README, manifest, skills)
```

### 4.9 New Files

```
engine/src/agent33/packs/remote_marketplace.py      — remote HTTP marketplace
engine/src/agent33/packs/marketplace_aggregator.py   — aggregator across sources
engine/src/agent33/packs/trust_manager.py            — trust policy management
engine/src/agent33/packs/rollback.py                 — rollback with enablement preservation
engine/src/agent33/packs/audit.py                    — audit trail recording
engine/src/agent33/packs/health.py                   — health checks
```

### 4.10 Modified Files

```
engine/src/agent33/packs/registry.py                — integrate aggregator, rollback, audit
engine/src/agent33/packs/api_models.py              — add marketplace, trust, matrix models
engine/src/agent33/api/routes/packs.py              — add new endpoints
engine/src/agent33/api/routes/marketplace.py        — extend with remote sources
engine/src/agent33/main.py                          — init remote marketplaces and aggregator
```

### 4.11 Test Files

```
engine/tests/test_remote_marketplace.py              — index fetch, download, caching
engine/tests/test_marketplace_aggregator.py          — aggregation across local + remote
engine/tests/test_trust_manager.py                   — policy CRUD and signer management
engine/tests/test_pack_rollback.py                   — rollback with enablement preservation
engine/tests/test_pack_audit.py                      — audit entry recording and retrieval
engine/tests/test_pack_health.py                     — health checks and smoke tests
engine/tests/test_pack_enablement_matrix.py          — matrix view and bulk updates
engine/tests/test_pack_routes_marketplace.py         — API integration tests
```

---

## 5. Track Phase 5: Safe Mutation and Process Control

### 5.1 Problem

AGENT-33 has no first-class `apply_patch` tool. Agents that need to modify files must use the generic `file_ops` tool or `shell`, which lack structured diff semantics, dry-run preview, filesystem boundary enforcement, and patch-specific audit logging.

Additionally, there is no operator-visible process manager for background command sessions.

### 5.2 apply_patch Tool

```python
# engine/src/agent33/tools/builtin/apply_patch.py

class ApplyPatchTool:
    """Safe, governed file mutation via structured patches."""

    name = "apply_patch"
    description = "Apply structured file patches with workspace containment and audit logging"

    parameters_schema = {
        "type": "object",
        "properties": {
            "patches": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path relative to workspace"},
                        "operation": {
                            "type": "string",
                            "enum": ["create", "modify", "delete"],
                        },
                        "content": {"type": "string", "description": "New content (create) or diff (modify)"},
                        "diff_format": {
                            "type": "string",
                            "enum": ["unified", "search_replace"],
                            "default": "unified",
                        },
                    },
                    "required": ["path", "operation"],
                },
            },
            "dry_run": {"type": "boolean", "default": False},
            "workspace_root": {"type": "string", "description": "Workspace containment root"},
        },
        "required": ["patches"],
    }
```

### 5.3 Filesystem Boundary Enforcement

```python
# engine/src/agent33/tools/builtin/patch_security.py

class PatchSecurityValidator:
    """Validates patch operations against filesystem security boundaries."""

    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root.resolve()

    def validate_path(self, path: str) -> tuple[bool, str]:
        """Validate a patch path is safe.

        Checks:
        1. Path resolves within workspace_root
        2. No symlink escape
        3. No hardlink escape
        4. No path traversal (..)
        5. No alias escape (Windows junction points)
        """
        ...

    def validate_batch(self, patches: list[dict]) -> list[tuple[str, str]]:
        """Validate all paths in a patch batch. Returns list of (path, error) for failures."""
        ...
```

### 5.4 Configuration Gating

```python
# Additions to engine/src/agent33/config.py

apply_patch_enabled: bool = Field(
    default=False,
    description="Enable the apply_patch tool. Must be explicitly opted in.",
)
apply_patch_allowed_models: list[str] = Field(
    default_factory=list,
    description="Models allowed to use apply_patch. Empty list = all models when enabled.",
)
apply_patch_require_workspace_containment: bool = Field(
    default=True,
    description="Require all patch paths to resolve within the workspace root.",
)
apply_patch_allow_out_of_workspace: bool = Field(
    default=False,
    description="Allow patches outside workspace (requires explicit opt-in).",
)
```

### 5.5 Governance Integration

The `apply_patch` tool integrates with existing governance:

1. `ToolGovernance.pre_execute_check()` evaluates tool policies for `apply_patch`
2. In supervised autonomy, all patch operations require approval via `ToolApprovalService`
3. Policy groups allow shorthands: `mutation:*` covers `apply_patch`, `file_ops:write`, `shell`

```python
# Additions to engine/src/agent33/tools/governance.py

# Add policy group expansion
_POLICY_GROUPS: dict[str, list[str]] = {
    "mutation": ["apply_patch", "file_ops:write", "shell"],
    "files": ["file_ops", "apply_patch"],
    "runtime": ["shell", "execute_code"],
    "web": ["web_fetch", "web_search", "browser"],
    "sessions": ["session_create", "session_send"],
    "automation": ["cron_create", "webhook_create"],
}
```

### 5.6 Dry-Run Preview

```python
class PatchPreview(BaseModel):
    """Preview of what a patch would do."""
    path: str
    operation: str
    diff: str = ""           # unified diff for modify operations
    lines_added: int = 0
    lines_removed: int = 0
    would_create: bool = False
    would_delete: bool = False
    validation_errors: list[str] = []
```

The `apply_patch` tool returns `PatchPreview` objects when `dry_run=True`.

### 5.7 Mutation Audit Trail

```python
# engine/src/agent33/tools/builtin/patch_audit.py

class PatchAuditEntry(BaseModel):
    """Audit record for a patch application."""
    patch_id: str              # unique ID for the batch
    timestamp: datetime
    agent_id: str = ""
    session_id: str = ""
    tenant_id: str = ""
    workspace_root: str
    patches: list[dict]        # the applied patches
    dry_run: bool
    approval_id: str = ""      # if approval was required
    result: str                # "success", "partial", "failed"
    errors: list[str] = []

class PatchAuditLog:
    """Persistent audit log for patch operations."""

    def __init__(self, log_dir: Path) -> None: ...
    def record(self, entry: PatchAuditEntry) -> None: ...
    def query(self, *, session_id: str = "", tenant_id: str = "", limit: int = 50) -> list[PatchAuditEntry]: ...
```

### 5.8 Process Manager

```python
# engine/src/agent33/tools/process_manager.py

class ManagedProcess(BaseModel):
    """A background command session managed by the process manager."""
    process_id: str
    command: str
    status: str  # "running", "completed", "failed", "killed"
    started_at: datetime
    finished_at: datetime | None = None
    exit_code: int | None = None
    agent_id: str = ""
    session_id: str = ""
    tenant_id: str = ""

class ProcessManager:
    """Manages background command sessions with log tailing."""

    def __init__(self, log_dir: Path, max_processes: int = 10) -> None: ...

    async def start(self, command: str, *, session_id: str = "", tenant_id: str = "") -> ManagedProcess: ...
    async def kill(self, process_id: str) -> bool: ...
    def get_status(self, process_id: str) -> ManagedProcess | None: ...
    def list_processes(self, *, session_id: str = "", tenant_id: str = "") -> list[ManagedProcess]: ...
    async def read_log(self, process_id: str, *, tail: int = 100) -> str: ...
    async def write_stdin(self, process_id: str, data: str) -> bool: ...
    def cleanup_completed(self, *, max_age_seconds: int = 3600) -> int: ...
```

### 5.9 API Endpoints

```
POST   /v1/tools/apply-patch             — apply patches (with dry_run option)
GET    /v1/tools/apply-patch/audit        — query patch audit log
GET    /v1/tools/apply-patch/audit/{id}   — single audit entry

GET    /v1/processes                      — list managed processes
POST   /v1/processes                      — start a background process
GET    /v1/processes/{id}                 — process status
GET    /v1/processes/{id}/log             — tail process log
POST   /v1/processes/{id}/write           — write to process stdin
DELETE /v1/processes/{id}                 — kill process
POST   /v1/processes/cleanup              — cleanup completed processes
```

### 5.10 New Files

```
engine/src/agent33/tools/builtin/apply_patch.py     — apply_patch tool
engine/src/agent33/tools/builtin/patch_security.py  — filesystem boundary validation
engine/src/agent33/tools/builtin/patch_audit.py     — mutation audit trail
engine/src/agent33/tools/process_manager.py         — background process manager
engine/src/agent33/api/routes/apply_patch.py        — patch API endpoints
engine/src/agent33/api/routes/processes.py          — process manager API endpoints
```

### 5.11 Modified Files

```
engine/src/agent33/config.py                        — add apply_patch settings
engine/src/agent33/tools/governance.py              — add policy groups
engine/src/agent33/main.py                          — init process manager, register apply_patch tool
```

### 5.12 Test Files

```
engine/tests/test_apply_patch.py                    — patch tool execution, diff formats
engine/tests/test_patch_security.py                 — boundary enforcement: symlink, traversal, alias
engine/tests/test_patch_audit.py                    — audit recording and querying
engine/tests/test_patch_governance.py               — approval integration, policy groups
engine/tests/test_patch_dry_run.py                  — preview without mutation
engine/tests/test_process_manager.py                — process lifecycle, log tailing, cleanup
engine/tests/test_apply_patch_routes.py             — API integration tests
engine/tests/test_process_routes.py                 — process API integration tests
```

---

## 6. Track Phase 6: Backup and Restore Confidence

### 6.1 Problem

AGENT-33's backup capability is limited to improvement learning state via the improvements API. There is no platform-level backup that covers runtime configuration, plugin/pack state, agent definitions, workflow definitions, skill state, and session data.

### 6.2 Backup Manifest Schema

```python
# engine/src/agent33/backup/manifest.py

class BackupManifest(BaseModel):
    """Versioned manifest describing a backup archive."""
    schema_version: str = "1.0"
    backup_id: str
    created_at: datetime
    platform: str                       # e.g. "win32", "linux"
    runtime_version: str                # AGENT-33 version
    archive_root: str                   # absolute path of the backup source
    backup_mode: str                    # "full", "config-only", "no-workspace"
    assets: list[BackupAsset]
    checksums: dict[str, str] = {}      # relative_path -> sha256
    metadata: dict[str, Any] = {}       # arbitrary metadata

class BackupAsset(BaseModel):
    """A single asset included in the backup."""
    relative_path: str
    asset_type: str                     # "config", "agent_definitions", "workflow_definitions",
                                        # "skills", "packs", "plugins", "sessions", "database", "workspace"
    size_bytes: int = 0
    checksum: str = ""                  # sha256
    included: bool = True
    exclusion_reason: str = ""
```

### 6.3 Backup Modes

| Mode | What's included | What's excluded |
| --- | --- | --- |
| `full` | Config, agent/workflow/skill definitions, pack/plugin state, database export, workspace | Large binary artifacts, temp files |
| `config-only` | Config files, agent/workflow definitions, pack manifests | Database, workspace, session data |
| `no-workspace` | Everything except workspace directory | Workspace files |

### 6.4 Backup Service

```python
# engine/src/agent33/backup/service.py

class BackupService:
    """Creates and verifies platform-level backups."""

    def __init__(
        self,
        backup_dir: Path,
        config_dir: Path,
        data_dir: Path,
        workspace_dir: Path | None = None,
    ) -> None: ...

    async def create(
        self,
        *,
        mode: str = "full",
        label: str = "",
    ) -> BackupResult:
        """Create a backup archive.

        Steps:
        1. Gather asset inventory
        2. Create temp directory
        3. Copy assets to temp directory
        4. Compute checksums
        5. Write manifest
        6. Create archive atomically (write to .tmp, rename)
        7. Verify archive
        """
        ...

    async def verify(self, archive_path: Path) -> VerifyResult:
        """Verify a backup archive.

        Checks:
        1. Archive is readable
        2. Manifest is parseable and schema version is supported
        3. Archive root containment (no path escape)
        4. All manifest-declared assets are present
        5. Checksums match
        6. No duplicate normalized entries
        """
        ...

    def list_backups(self) -> list[BackupSummary]: ...
    def get_backup(self, backup_id: str) -> BackupManifest | None: ...
```

### 6.5 Backup Result Models

```python
class BackupResult(BaseModel):
    success: bool
    backup_id: str
    archive_path: str = ""
    manifest: BackupManifest | None = None
    size_bytes: int = 0
    asset_count: int = 0
    errors: list[str] = []
    warnings: list[str] = []
    provenance: BackupProvenance | None = None

class BackupProvenance(BaseModel):
    """Records who created the backup and from what state."""
    creator: str = ""
    source_roots: list[str] = []
    runtime_version: str = ""
    platform: str = ""
    created_at: datetime

class VerifyResult(BaseModel):
    valid: bool
    checks: list[VerifyCheck]
    warnings: list[str] = []

class VerifyCheck(BaseModel):
    name: str
    passed: bool
    message: str = ""
```

### 6.6 Restore Planning

Restore is deliberately separated from restore execution. Track Phase 6 implements restore *planning* (preview what would be restored); actual restore execution is a future phase.

```python
# engine/src/agent33/backup/restore_planner.py

class RestorePlan(BaseModel):
    """Preview of what a restore would do."""
    backup_id: str
    backup_version: str
    current_version: str
    assets_to_restore: list[RestoreAssetPlan]
    conflicts: list[RestoreConflict]
    warnings: list[str] = []
    estimated_duration: str = ""

class RestoreAssetPlan(BaseModel):
    relative_path: str
    asset_type: str
    action: str  # "create", "overwrite", "skip"
    current_exists: bool
    size_bytes: int = 0

class RestoreConflict(BaseModel):
    relative_path: str
    conflict_type: str  # "version_mismatch", "schema_change", "file_modified"
    message: str
    resolution: str  # "overwrite", "skip", "merge"

class RestorePlanner:
    """Generates restore plans from backup archives."""

    def plan(self, archive_path: Path) -> RestorePlan: ...
```

### 6.7 Archive Naming

Archives use lexically sortable names: `agent33-backup-{YYYYMMDD-HHmmss}-{mode}-{short_id}.tar.gz`

Example: `agent33-backup-20260310-143022-full-a1b2c3.tar.gz`

### 6.8 Safety Constraints

1. Backup output must never be written inside source roots (prevent recursive backup)
2. Archives are written atomically via temp file + rename
3. Restore planning is read-only; no state changes until explicit restore execution
4. Backup-first recommendations are surfaced before destructive operations (wired into the existing approval flow)

### 6.9 API Endpoints

```
POST   /v1/backups                      — create a backup
GET    /v1/backups                      — list backups
GET    /v1/backups/{id}                 — backup detail with manifest
POST   /v1/backups/{id}/verify          — verify an existing backup
POST   /v1/backups/{id}/restore-plan    — generate restore plan (preview only)
DELETE /v1/backups/{id}                 — delete a backup archive
GET    /v1/backups/inventory            — browse backup contents
```

### 6.10 New Files

```
engine/src/agent33/backup/__init__.py
engine/src/agent33/backup/manifest.py           — manifest and asset models
engine/src/agent33/backup/service.py            — create and verify
engine/src/agent33/backup/restore_planner.py    — restore planning (preview only)
engine/src/agent33/backup/archive.py            — archive creation and extraction utilities
engine/src/agent33/api/routes/backups.py        — backup API endpoints
```

### 6.11 Modified Files

```
engine/src/agent33/config.py                    — add backup_dir setting
engine/src/agent33/main.py                      — init BackupService
engine/src/agent33/tools/governance.py          — wire backup recommendations into destructive flows
```

### 6.12 Test Files

```
engine/tests/test_backup_manifest.py            — manifest serialization and validation
engine/tests/test_backup_service.py             — create and verify lifecycle
engine/tests/test_backup_verify.py              — verification checks (containment, checksums, duplicates)
engine/tests/test_restore_planner.py            — restore plan generation and conflict detection
engine/tests/test_backup_archive.py             — archive creation, naming, atomicity
engine/tests/test_backup_routes.py              — API integration tests
```

---

## 7. Shared API Patterns

### 7.1 Error Response Shape

All new endpoints use a consistent error response:

```python
class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
    code: str = ""  # machine-readable error code
```

### 7.2 Pagination

List endpoints support cursor-based pagination:

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    cursor: str | None = None
    has_more: bool = False
```

### 7.3 Tenant Scoping

All endpoints extract tenant_id from the authenticated principal via the existing `AuthMiddleware`. Responses are filtered by tenant where applicable (pack enablement, process visibility, backup access).

### 7.4 Health Endpoint Integration

New subsystems register health checks with the existing `/v1/health` endpoint:

```python
# Each service provides a health_check() method
# Wired in main.py lifespan alongside existing health checks

class SubsystemHealth(BaseModel):
    subsystem: str
    healthy: bool
    message: str = ""
    details: dict[str, Any] = {}
```

### 7.5 Scope Requirements

| Endpoint group | Required scope |
| --- | --- |
| Plugin install/update | `plugins:manage` |
| Plugin doctor/health | `plugins:read` |
| Pack marketplace | `packs:read` |
| Pack trust policy | `packs:manage` |
| apply_patch | `tools:execute` + governance check |
| Process manager | `processes:manage` |
| Backup create | `backups:create` |
| Backup verify/restore-plan | `backups:read` |

---

## 8. Combined Test Strategy

### Unit Test Requirements

Every test must:
1. Assert on specific expected values, not just status codes
2. Test real behavior (validation, error paths, state changes)
3. Mock only infrastructure dependencies (DB, filesystem, HTTP), not business logic
4. Verify tenant isolation where applicable

### Integration Test Requirements

1. Use `TestClient` with mocked `app.state` services
2. Test auth scoping (correct scope grants access, wrong scope returns 403)
3. Test error paths (missing resources return 404, validation errors return 422)
4. Test pagination and filtering

### Cross-Track Tests

Some behaviors span multiple tracks:

1. **Pack install + trust policy**: Installing a pack from a remote marketplace applies trust policy evaluation
2. **apply_patch + governance**: Patch operations in supervised autonomy require approval
3. **Backup + restore plan**: Creating a backup and then generating a restore plan from it
4. **Plugin + pack interaction**: Installing a plugin that depends on a pack skill

### Estimated Test Counts

| Track | Unit tests | Integration tests | Total |
| --- | --- | --- | --- |
| Track 3 (Plugins) | ~40 | ~20 | ~60 |
| Track 4 (Packs) | ~50 | ~25 | ~75 |
| Track 5 (Mutation) | ~60 | ~25 | ~85 |
| Track 6 (Backup) | ~45 | ~20 | ~65 |
| **Total** | **~195** | **~90** | **~285** |

---

## 9. Implementation Order

Recommended sequencing within a session:

1. **Track 3 + Track 4 together** (plugin and pack lifecycle are closely related; shared patterns for install, config, health, audit)
2. **Track 5** (safe mutation depends on governance but is otherwise independent)
3. **Track 6** (backup depends on understanding what subsystems exist to back up)

Within each track, implement in this order:
1. Data models and service logic
2. Unit tests for service logic
3. API routes and response models
4. Integration tests for API routes
5. Wire into `main.py` lifespan

---

## 10. Risks and Open Questions

1. **Remote marketplace authentication**: The `RemotePackMarketplace` needs a token-based auth flow. If no public marketplace exists yet, this should be designed as an interface with a stub implementation.

2. **apply_patch diff format**: Supporting both unified diff and search-replace formats adds complexity. Consider starting with search-replace only (simpler, deterministic) and adding unified diff support later.

3. **Backup size**: Full backups including workspace and database could be large. Consider streaming archive creation and progress reporting for the API.

4. **Process manager on Windows**: `asyncio.create_subprocess_shell` on Windows has known limitations (no `FileNotFoundError`, stderr detection for missing commands). The process manager should use the same patterns documented in the Windows Platform Notes in CLAUDE.md.

5. **Plugin install from registry**: There is no AGENT-33 plugin registry service yet. The `install_from_registry` method should be designed as a pluggable interface with a local-filesystem implementation for now and a remote HTTP implementation for later.

6. **Backup database export**: Exporting PostgreSQL state requires either `pg_dump` or a custom SQL export. The backup service should detect whether `pg_dump` is available and degrade gracefully if not (config-only backup as fallback).
