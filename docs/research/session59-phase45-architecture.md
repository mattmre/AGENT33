# Phase 45: Secure MCP Fabric, Tokenized Approvals, and Cross-CLI Distribution

## Architecture Document

**Date:** 2026-03-10
**Phase:** 45 of EVOKORE Integration Roadmap (Phases 44-48)
**Depends on:** Phase 44 (Session Safety, Hook Operating Layer, Continuity)
**Category:** Integration / Security

---

## 1. Executive Summary

Phase 45 evolves the existing AGENT-33 MCP server (Phase 43) from a single-server endpoint into a governed MCP fabric. Three capabilities are introduced:

1. **Multi-Server MCP Proxy Manager** — aggregate upstream MCP servers behind the AGENT-33 MCP endpoint with health monitoring, tool namespace deconfliction, and circuit-breaker protection.
2. **Stateless HITL Approval Tokens** — extend the existing `ToolApprovalService` with JWT-based, short-lived, arg-scoped approval tokens that MCP clients can present without maintaining server-side session state.
3. **Cross-CLI MCP Sync** — tooling to register AGENT-33 as an MCP server across Claude Code, Claude Desktop, Cursor, and Gemini CLI environments with config normalization and conflict-safe merging.

---

## 2. Existing Surfaces Being Extended

### 2.1 MCP Server (`engine/src/agent33/mcp_server/`)

| File | Current Role | Phase 45 Extension |
|---|---|---|
| `server.py` | Creates `mcp.server.Server("agent33-core")`, registers 7 tool handlers and resource handlers with scope enforcement | Surface aggregated proxy tools alongside native tools; inject approval-token schema fields into governed tool schemas |
| `bridge.py` | `MCPServiceBridge` connects MCP handlers to `AgentRegistry`, `ToolRegistry`, `ModelRouter`, `RAGPipeline`, `SkillRegistry`, `WorkflowRegistry` | Add `ProxyManager` reference; route proxy tool calls through the bridge |
| `tools.py` | Handler implementations for `list_agents`, `invoke_agent`, `search_memory`, `list_tools`, `execute_tool`, `list_skills`, `get_system_status` | Add proxy tool execution handler; add `manage_proxy_servers` admin tool |
| `auth.py` | Scope-based enforcement (`TOOL_SCOPES`, `RESOURCE_SCOPES`), request context extraction, registry tool access checks | Extend `TOOL_SCOPES` for proxy tools; add approval-token validation path alongside JWT/API-key auth |
| `resources.py` | Static and template resources for agent registry, tool catalog, policy pack, schema index | Add `agent33://proxy-servers` resource for proxy fleet status |

### 2.2 Tool Governance (`engine/src/agent33/tools/governance.py`)

The `ToolGovernance` class performs pre-execution checks: tool policies (allow/deny/ask), rate limiting, autonomy enforcement, scope checks, shell command validation, path allowlists, and domain allowlists. It already integrates with `ToolApprovalService` via `_try_consume_approval()` using an `__approval_id` parameter.

Phase 45 adds a second consumption path: stateless JWT-based approval tokens that carry the approval scope, tool name, normalized argument hash, and expiry inside the token itself (no server-side lookup required for validation).

### 2.3 Approvals (`engine/src/agent33/tools/approvals.py`)

The `ToolApprovalService` implements request/approve/reject/consume/expire lifecycle with optional durable state via `OrchestrationStateStore`. The REST API (`/v1/approvals/tools`) provides list/get/decide endpoints.

Phase 45 extends this with a token issuance endpoint that converts an approved `ToolApprovalRequest` into a signed JWT that can be presented to the MCP server directly.

### 2.4 Security (`engine/src/agent33/security/`)

- `auth.py` — JWT creation/verification, API key generation/validation
- `encryption.py` — AES-256-GCM encrypt/decrypt utilities
- `middleware.py` — `AuthMiddleware` (Bearer JWT and X-API-Key)
- `permissions.py` — Scope-based permission system with deny-first evaluation
- `vault.py` — In-memory credential vault with encryption at rest

### 2.5 Connectors (`engine/src/agent33/connectors/`)

- `circuit_breaker.py` — `CircuitBreaker` with CLOSED/OPEN/HALF_OPEN states, configurable failure threshold and recovery timeout
- `models.py` — `ConnectorRequest` envelope
- `middleware.py`, `executor.py`, `boundary.py`, `governance.py` — Middleware chain, execution, policy packs, governance

Phase 45 treats proxied MCP servers as connector-boundary participants, inheriting circuit-breaker, governance, and retry behavior.

---

## 3. Multi-Server MCP Proxy Manager

### 3.1 Architecture Overview

```
                    +--------------------------+
   MCP Client       |   AGENT-33 MCP Server    |
   (Claude, etc.)-->|   server.py              |
                    |                          |
                    |  Native tools (7)        |
                    |  + Proxy tools (N)       |
                    |                          |
                    |  ProxyManager            |
                    |    |-- ChildServer[0]    |--> upstream MCP server A
                    |    |-- ChildServer[1]    |--> upstream MCP server B
                    |    +-- ChildServer[N]    |--> upstream MCP server N
                    +--------------------------+
```

### 3.2 Configuration Model

A new `mcp.config.json` file (or `MCP_PROXY_CONFIG` env var path) defines the proxy fleet:

```json
{
  "proxy_servers": [
    {
      "id": "elevenlabs",
      "name": "ElevenLabs MCP",
      "command": "npx",
      "args": ["-y", "@anthropic/elevenlabs-mcp-server"],
      "env": {
        "ELEVENLABS_API_KEY": "${ELEVENLABS_API_KEY}"
      },
      "transport": "stdio",
      "tool_prefix": "elevenlabs",
      "enabled": true,
      "health_check_interval_seconds": 60,
      "max_consecutive_failures": 5,
      "cooldown_seconds": 300,
      "auth": {
        "type": "env_bearer",
        "env_var": "ELEVENLABS_API_KEY"
      },
      "governance": {
        "policy": "ask",
        "allowed_tools": ["*"],
        "blocked_tools": []
      }
    },
    {
      "id": "filesystem",
      "name": "Filesystem MCP",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      "transport": "stdio",
      "tool_prefix": "fs",
      "enabled": true,
      "governance": {
        "policy": "allow",
        "allowed_tools": ["read_file", "list_directory"],
        "blocked_tools": ["write_file"]
      }
    }
  ],
  "defaults": {
    "transport": "stdio",
    "health_check_interval_seconds": 60,
    "max_consecutive_failures": 3,
    "cooldown_seconds": 120
  }
}
```

### 3.3 Pydantic Models

New file: `engine/src/agent33/mcp_server/proxy_models.py`

```python
class ProxyServerAuth(BaseModel):
    type: Literal["none", "env_bearer", "api_key", "vault"] = "none"
    env_var: str = ""
    vault_key: str = ""

class ProxyServerGovernance(BaseModel):
    policy: Literal["allow", "ask", "deny"] = "allow"
    allowed_tools: list[str] = Field(default_factory=lambda: ["*"])
    blocked_tools: list[str] = Field(default_factory=list)

class ProxyServerConfig(BaseModel):
    id: str  # unique identifier
    name: str = ""
    command: str  # executable to spawn (npx, uvx, python, etc.)
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)  # supports ${VAR} interpolation
    transport: Literal["stdio", "sse"] = "stdio"
    url: str = ""  # for SSE transport
    tool_prefix: str = ""  # prefix added to all tools from this server
    enabled: bool = True
    health_check_interval_seconds: float = 60.0
    max_consecutive_failures: int = 3
    cooldown_seconds: float = 120.0
    auth: ProxyServerAuth = Field(default_factory=ProxyServerAuth)
    governance: ProxyServerGovernance = Field(default_factory=ProxyServerGovernance)

class ProxyFleetConfig(BaseModel):
    proxy_servers: list[ProxyServerConfig] = Field(default_factory=list)
    defaults: dict[str, Any] = Field(default_factory=dict)
```

### 3.4 Child Server Lifecycle

New file: `engine/src/agent33/mcp_server/proxy_child.py`

Each child server is managed through a `ChildServerHandle` that wraps:

1. **Process spawn** — `asyncio.create_subprocess_exec()` with:
   - Environment interpolation (resolve `${VAR}` references from `os.environ` and vault)
   - Merged env inheriting `os.environ` (required on Windows for PATH resolution)
   - Platform-aware command resolution (detect missing commands via stderr on Windows)

2. **MCP client session** — Uses `mcp.client` SDK to connect to the child's stdio/SSE transport and discover its tools.

3. **Health monitoring** — Periodic ping on a configurable interval. The health state machine mirrors the existing `CircuitBreaker`:
   - HEALTHY (circuit closed) — tool calls forwarded normally
   - DEGRADED (circuit half-open) — probe calls allowed, bulk forwarding suspended
   - UNHEALTHY (circuit open) — all calls rejected, cooldown timer active
   - STOPPED — process not running or disabled

4. **Cooldown protection** — After `max_consecutive_failures` failures, the child enters cooldown for `cooldown_seconds`. During cooldown, all calls to that child return an error immediately rather than spawning retry storms.

5. **Graceful shutdown** — On AGENT-33 shutdown, children are terminated in reverse-registration order. SIGTERM with a 5-second grace period, then SIGKILL.

```python
class ChildServerState(StrEnum):
    STARTING = "starting"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    COOLDOWN = "cooldown"
    STOPPED = "stopped"

class ChildServerHandle:
    config: ProxyServerConfig
    state: ChildServerState
    circuit_breaker: CircuitBreaker
    process: asyncio.subprocess.Process | None
    client_session: Any  # mcp.client.ClientSession
    discovered_tools: dict[str, ToolDefinition]
    last_health_check: float
    consecutive_failures: int

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def health_check(self) -> bool: ...
    async def call_tool(self, tool_name: str, arguments: dict) -> Any: ...
    async def list_tools(self) -> list[ToolDefinition]: ...
```

### 3.5 ProxyManager

New file: `engine/src/agent33/mcp_server/proxy_manager.py`

The `ProxyManager` is the central coordinator. It owns the fleet of `ChildServerHandle` instances and provides the aggregation surface.

```python
class ProxyManager:
    def __init__(
        self,
        config: ProxyFleetConfig,
        vault: CredentialVault | None = None,
        governance: ToolGovernance | None = None,
    ) -> None: ...

    async def start_all(self) -> None:
        """Start all enabled child servers."""

    async def stop_all(self) -> None:
        """Stop all child servers in reverse order."""

    async def add_server(self, config: ProxyServerConfig) -> ChildServerHandle:
        """Add and start a new child server at runtime."""

    async def remove_server(self, server_id: str) -> bool:
        """Stop and remove a child server."""

    def list_servers(self) -> list[dict[str, Any]]:
        """Return status summary of all child servers."""

    def get_server(self, server_id: str) -> ChildServerHandle | None:
        """Return a specific child server handle."""

    def list_aggregated_tools(self) -> list[dict[str, Any]]:
        """Return all tools from all healthy children, with prefixes applied."""

    async def call_proxy_tool(
        self,
        prefixed_tool_name: str,
        arguments: dict[str, Any],
        context: ToolContext | None = None,
    ) -> Any:
        """Route a tool call to the correct child server."""

    def resolve_server_for_tool(self, prefixed_tool_name: str) -> tuple[ChildServerHandle, str] | None:
        """Map a prefixed tool name to (child, unprefixed_name)."""
```

### 3.6 Tool Namespace Deconfliction

Every tool from a proxied server is exposed with a configurable prefix:

- Config: `"tool_prefix": "elevenlabs"` on the `ProxyServerConfig`
- Effect: a child tool named `text_to_speech` becomes `elevenlabs__text_to_speech` in the aggregated listing
- The double-underscore separator (`__`) is chosen to avoid collisions with tool names that use single underscores (e.g., `file_ops`)
- If no prefix is set, the server `id` is used as the prefix
- Collision detection: on startup and on `add_server`, the `ProxyManager` checks for name collisions across all children and native tools. Collisions raise a `ValueError` with details about which tools conflict.

Native AGENT-33 tools (the 7 defined in `server.py`) are never prefixed. They always take priority over proxy tools in case of ambiguity.

### 3.7 Wiring into Existing MCP Server

Changes to `server.py`:

1. The `create_mcp_server()` function accepts an optional `ProxyManager` (via the bridge or directly).
2. The `list_tools` handler merges native `_MCP_TOOL_DEFINITIONS` with `proxy_manager.list_aggregated_tools()`, applying scope filtering to both.
3. The `call_tool` handler adds a proxy dispatch branch: if the tool name matches a proxy tool (resolved via `resolve_server_for_tool`), it delegates to `proxy_manager.call_proxy_tool()`. Governance checks (tool policies, approval tokens) are applied before delegation.
4. New admin tools are added:
   - `proxy_list_servers` — returns fleet status
   - `proxy_add_server` — adds a server at runtime (requires `admin` scope)
   - `proxy_remove_server` — removes a server at runtime (requires `admin` scope)

Changes to `bridge.py`:

```python
class MCPServiceBridge:
    def __init__(
        self,
        ...existing params...,
        proxy_manager: ProxyManager | None = None,
    ) -> None:
        ...
        self.proxy_manager = proxy_manager
```

Changes to `auth.py`:

- Add proxy admin tool scopes to `TOOL_SCOPES`
- Add `agent33://proxy-servers` to `RESOURCE_SCOPES`

Changes to `main.py` (lifespan):

- After MCP server creation, load `ProxyFleetConfig` from `mcp.config.json` (path from `settings.mcp_proxy_config_path`)
- Create `ProxyManager` and bind to bridge
- Call `proxy_manager.start_all()` during startup
- Call `proxy_manager.stop_all()` during shutdown (before MCP server shutdown)

### 3.8 Health Monitoring and Observability

Each `ChildServerHandle` maintains:
- `state: ChildServerState` — current lifecycle state
- `circuit_breaker: CircuitBreaker` — reuses the existing `connectors.circuit_breaker.CircuitBreaker`
- `last_health_check: float` — monotonic timestamp of last check
- `last_error: str` — last error message for diagnostics

The `ProxyManager` runs a background `asyncio.Task` that periodically health-checks each child on its configured interval. Health check results feed into the circuit breaker. When a child transitions to UNHEALTHY, an observability event is emitted for structured logging.

The `agent33://proxy-servers` MCP resource and `proxy_list_servers` tool expose fleet health to MCP clients and operators.

---

## 4. Stateless HITL Approval Tokens

### 4.1 Problem Statement

The existing `ToolApprovalService` uses server-side state: a `ToolApprovalRequest` is created, stored in memory (optionally persisted via `OrchestrationStateStore`), and consumed by matching `approval_id`. This works for REST API clients that can poll the approval status, but MCP clients operate in a stateless request-response model. They need a self-contained token they can present on the next tool call.

### 4.2 Token Design

Approval tokens are short-lived JWTs signed with the same `jwt_secret` used for auth tokens, but with a distinct `typ` claim to prevent cross-use.

**Token claims:**

```json
{
  "typ": "a33_approval",
  "sub": "operator@example.com",
  "iss": "agent33",
  "iat": 1741612800,
  "exp": 1741613100,
  "jti": "APR-abc123def456",
  "tool": "shell",
  "op": "execute",
  "arg_hash": "sha256:a1b2c3d4...",
  "tenant_id": "tenant-001",
  "scope": "tools:execute",
  "one_time": true
}
```

| Claim | Purpose |
|---|---|
| `typ` | Always `"a33_approval"` — prevents use as a regular auth token |
| `sub` | The operator who approved the action |
| `jti` | Maps back to the `ToolApprovalRequest.approval_id` for audit trail |
| `tool` | Tool name the approval is scoped to |
| `op` | Operation (empty string if not operation-scoped) |
| `arg_hash` | SHA-256 of canonically normalized arguments (prevents argument tampering) |
| `tenant_id` | Tenant scope |
| `scope` | Required permission scope |
| `one_time` | If `true`, the token is consumed on first use (added to a consumed-set) |
| `exp` | Short expiry window (default: 5 minutes, configurable via `settings.approval_token_ttl_seconds`) |

### 4.3 Argument Canonicalization

To prevent argument tampering between approval and execution, the arguments are canonically normalized before hashing:

New utility: `engine/src/agent33/security/arg_hash.py`

```python
def canonical_arg_hash(tool_name: str, arguments: dict[str, Any]) -> str:
    """Produce a deterministic SHA-256 hash of tool arguments.

    Normalization rules:
    1. Sort keys recursively
    2. Serialize with json.dumps(separators=(',', ':'), sort_keys=True)
    3. Prepend tool_name as namespace
    4. SHA-256 the UTF-8 bytes
    """
    normalized = json.dumps(arguments, separators=(",", ":"), sort_keys=True)
    payload = f"{tool_name}:{normalized}"
    return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
```

### 4.4 Approval Flow

```
                 MCP Client                    AGENT-33 MCP Server
                    |                                 |
  1. call_tool      |----tool_name, args----------->  |
                    |                                 |
                    |   governance check -> "ask"      |
                    |                                 |
  2. error response |<---approval_required,           |
                    |    approval_id: APR-xxx,         |
                    |    approval_url: /v1/approvals   |
                    |    /tools/APR-xxx/decision       |
                    |                                 |
            (operator reviews and approves via REST API or UI)
                    |                                 |
  3. POST decision  |----approve APR-xxx----------->  |
                    |                                 |
  4. token issued   |<---approval_token: eyJ...       |
                    |                                 |
  5. call_tool      |----tool_name, args,             |
                    |    __approval_token: eyJ...----> |
                    |                                 |
                    |   validate token:                |
                    |   - verify signature             |
                    |   - check typ == a33_approval    |
                    |   - check exp                    |
                    |   - check tool matches           |
                    |   - check arg_hash matches       |
                    |   - check one_time not consumed  |
                    |   - mark consumed                |
                    |                                 |
  6. tool result    |<---result--------------------- |
```

### 4.5 Token Issuance

The approval decision endpoint (`POST /v1/approvals/tools/{approval_id}/decision`) is extended. When an approval is granted, the response includes an `approval_token` field containing the signed JWT.

New module: `engine/src/agent33/security/approval_tokens.py`

```python
class ApprovalTokenManager:
    """Issue and validate stateless HITL approval tokens."""

    def __init__(
        self,
        secret: str,
        algorithm: str = "HS256",
        default_ttl_seconds: int = 300,
    ) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._default_ttl_seconds = default_ttl_seconds
        # Track consumed one-time tokens (jti -> consumed_at)
        # Bounded: entries older than max_ttl are pruned
        self._consumed: dict[str, float] = {}

    def issue(
        self,
        approval: ToolApprovalRequest,
        arguments: dict[str, Any] | None = None,
        ttl_seconds: int | None = None,
    ) -> str:
        """Issue a signed approval token for an approved request."""
        ...

    def validate(
        self,
        token: str,
        tool_name: str,
        arguments: dict[str, Any],
        tenant_id: str = "",
    ) -> ApprovalTokenPayload:
        """Validate and optionally consume an approval token.

        Raises ApprovalTokenError on any validation failure.
        """
        ...

    def _prune_consumed(self) -> None:
        """Remove consumed entries older than 2x default TTL."""
        ...
```

### 4.6 Integration with Tool Governance

The `ToolGovernance.pre_execute_check()` method gains a new check early in the chain, before the existing `_try_consume_approval()`:

```python
# In pre_execute_check, after tool policy returns "ask":
approval_token = params.get("__approval_token")
if approval_token and self._approval_token_manager:
    try:
        self._approval_token_manager.validate(
            approval_token, tool_name, params, tenant_id=context.tenant_id
        )
        return True  # token valid, proceed
    except ApprovalTokenError:
        pass  # fall through to existing approval flow
```

This preserves backward compatibility: the existing `__approval_id` path continues to work for REST API clients, while `__approval_token` provides the stateless MCP path.

### 4.7 Token Revocation

Two revocation mechanisms:

1. **Expiry** — tokens have a short TTL (default 5 minutes). Most tokens expire naturally.
2. **Consumed set** — one-time tokens are added to an in-memory consumed set keyed by `jti`. The set is pruned periodically (entries older than 2x TTL are removed).
3. **Emergency revocation** — a new endpoint `POST /v1/approvals/tokens/revoke` accepts a `jti` and adds it to a revocation set. Tokens with `jti` in the revocation set fail validation even if not yet expired.

The revocation set is bounded: entries are pruned when their `exp` time has passed (the token would have expired anyway).

### 4.8 Schema Injection for Governed Tools

When a proxied or native tool has a governance policy of `"ask"`, the MCP server automatically injects an `__approval_token` field into the tool's `inputSchema`:

```json
{
  "name": "elevenlabs__text_to_speech",
  "inputSchema": {
    "type": "object",
    "properties": {
      "text": { "type": "string" },
      "voice_id": { "type": "string" },
      "__approval_token": {
        "type": "string",
        "description": "Approval token from /v1/approvals/tools/{id}/decision (required for governed tools)"
      }
    },
    "required": ["text"]
  }
}
```

This allows MCP clients to discover that a tool requires approval by inspecting its schema, without needing out-of-band knowledge.

---

## 5. Cross-CLI MCP Sync

### 5.1 Target CLIs and Config Locations

| CLI | Config File | Format |
|---|---|---|
| Claude Code | `~/.claude.json` or project `.mcp.json` | `{ "mcpServers": { "name": { "command": ..., "args": [...] } } }` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) / `%APPDATA%\Claude\claude_desktop_config.json` (Windows) | Same as Claude Code |
| Cursor | `.cursor/mcp.json` in project or `~/.cursor/mcp.json` global | `{ "mcpServers": { ... } }` |
| Gemini CLI | Via `--mcp-server` flag or `~/.gemini/settings.json` | TBD — follow Gemini CLI docs |

### 5.2 Config Normalization Model

New module: `engine/src/agent33/mcp_server/sync.py`

```python
class NormalizedMCPEntry(BaseModel):
    """CLI-agnostic MCP server registration."""
    name: str
    command: str
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    transport: Literal["stdio", "sse"] = "stdio"
    url: str = ""  # for SSE transport

class CLITarget(StrEnum):
    CLAUDE_CODE = "claude_code"
    CLAUDE_DESKTOP = "claude_desktop"
    CURSOR = "cursor"
    GEMINI = "gemini"

class SyncConfig(BaseModel):
    entry: NormalizedMCPEntry
    targets: list[CLITarget] = Field(default_factory=lambda: [CLITarget.CLAUDE_CODE])
    force: bool = False  # overwrite existing entries
```

### 5.3 Sync Operations

Three operations:

1. **Push** — Write the AGENT-33 MCP server registration to one or more CLI configs.
   - Reads the target config file
   - Checks for existing `mcpServers.agent33` entry
   - If exists and `--force` not set, reports conflict and skips
   - If exists and `--force` set, overwrites
   - If not exists, adds entry
   - Writes back with minimal formatting changes (preserve user's JSON style where possible)

2. **Pull** — Read MCP server registrations from a CLI config and import as proxy children.
   - Reads the target config file
   - For each `mcpServers` entry (excluding `agent33` itself), generates a `ProxyServerConfig`
   - Returns the list for review; does not auto-add without confirmation

3. **Diff** — Compare the AGENT-33 registration across all target CLIs.
   - Reads all target configs
   - Reports: present/absent/divergent per target
   - Useful for operator diagnostics

### 5.4 Conflict Resolution Strategy

- **Name collision**: If a target CLI already has an MCP server named `agent33`, sync reports the conflict. With `--force`, the existing entry is overwritten. Without `--force`, sync skips and logs a warning.
- **Env var divergence**: Sync preserves env vars from the target config if they differ from the source. The operator is warned about divergences.
- **Path normalization**: On Windows, paths use forward slashes in JSON config. The sync tool normalizes `\` to `/` for cross-platform compatibility.
- **Config backup**: Before any write, the sync tool creates a `.bak` copy of the target config file.

### 5.5 AGENT-33 Self-Registration Entry

The canonical MCP server entry that sync pushes to CLI configs:

```json
{
  "agent33": {
    "command": "uvx",
    "args": ["agent33", "mcp", "serve"],
    "env": {
      "AGENT33_JWT_SECRET": "${AGENT33_JWT_SECRET}",
      "AGENT33_MCP_AUTH": "api_key"
    }
  }
}
```

For SSE transport (connecting to a running AGENT-33 instance):

```json
{
  "agent33": {
    "transport": "sse",
    "url": "http://localhost:8000/mcp/sse"
  }
}
```

### 5.6 CLI Tooling

New CLI command group under the `agent33` CLI:

```bash
# Push AGENT-33 registration to Claude Code
agent33 mcp sync push --target claude_code

# Push to all supported CLIs
agent33 mcp sync push --target all

# Force overwrite existing entries
agent33 mcp sync push --target claude_code --force

# Show diff across all CLIs
agent33 mcp sync diff

# Pull MCP servers from Claude Code as proxy candidates
agent33 mcp sync pull --target claude_code

# List current proxy fleet status
agent33 mcp proxy list

# Add a proxy server from config
agent33 mcp proxy add --config server.json
```

---

## 6. API Endpoints

### 6.1 MCP Proxy Management

New router: `engine/src/agent33/api/routes/mcp_proxy.py`

| Method | Path | Scope | Description |
|---|---|---|---|
| `GET` | `/v1/mcp/proxy/servers` | `agents:read` | List all proxy servers with status |
| `GET` | `/v1/mcp/proxy/servers/{server_id}` | `agents:read` | Get a specific server's details and health |
| `POST` | `/v1/mcp/proxy/servers` | `admin` | Add a new proxy server |
| `DELETE` | `/v1/mcp/proxy/servers/{server_id}` | `admin` | Remove a proxy server |
| `POST` | `/v1/mcp/proxy/servers/{server_id}/restart` | `admin` | Restart a specific proxy server |
| `GET` | `/v1/mcp/proxy/tools` | `agents:read` | List all aggregated proxy tools |
| `GET` | `/v1/mcp/proxy/health` | (public) | Fleet health summary |

**Response shape for `GET /v1/mcp/proxy/servers`:**

```json
{
  "servers": [
    {
      "id": "elevenlabs",
      "name": "ElevenLabs MCP",
      "state": "healthy",
      "transport": "stdio",
      "tool_count": 4,
      "uptime_seconds": 3600,
      "consecutive_failures": 0,
      "circuit_state": "closed",
      "last_health_check": "2026-03-10T12:00:00Z",
      "last_error": null
    }
  ],
  "total": 1,
  "healthy": 1,
  "degraded": 0,
  "unhealthy": 0
}
```

### 6.2 Approval Token Management

Extensions to existing router: `engine/src/agent33/api/routes/tool_approvals.py`

| Method | Path | Scope | Description |
|---|---|---|---|
| `POST` | `/v1/approvals/tools/{approval_id}/token` | `tools:execute` | Issue an approval token for an approved request |
| `POST` | `/v1/approvals/tokens/validate` | `tools:execute` | Validate a token without consuming it |
| `POST` | `/v1/approvals/tokens/revoke` | `admin` | Revoke a token by JTI |

The existing `POST /v1/approvals/tools/{approval_id}/decision` response is extended to include `approval_token` when the decision is `approve` and arguments are provided:

```json
{
  "approval_id": "APR-abc123def456",
  "status": "approved",
  "approval_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_expires_at": "2026-03-10T12:05:00Z"
}
```

**Token issuance request body for `POST /v1/approvals/tools/{approval_id}/token`:**

```json
{
  "arguments": { "command": "rm -rf /tmp/old" },
  "ttl_seconds": 300
}
```

### 6.3 Sync Operations

New router: `engine/src/agent33/api/routes/mcp_sync.py`

| Method | Path | Scope | Description |
|---|---|---|---|
| `POST` | `/v1/mcp/sync/push` | `admin` | Push AGENT-33 registration to CLI configs |
| `POST` | `/v1/mcp/sync/pull` | `admin` | Pull MCP servers from a CLI config |
| `GET` | `/v1/mcp/sync/diff` | `agents:read` | Diff AGENT-33 registration across CLIs |
| `GET` | `/v1/mcp/sync/targets` | `agents:read` | List supported CLI targets and their config paths |

---

## 7. Settings Extensions

New settings in `engine/src/agent33/config.py`:

```python
# MCP Proxy
mcp_proxy_config_path: str = ""  # path to mcp.config.json
mcp_proxy_enabled: bool = False
mcp_proxy_tool_separator: str = "__"  # separator between prefix and tool name
mcp_proxy_health_check_enabled: bool = True

# Approval Tokens
approval_token_ttl_seconds: int = 300  # 5 minutes
approval_token_enabled: bool = True
approval_token_one_time_default: bool = True

# MCP Sync
mcp_sync_backup_enabled: bool = True  # create .bak before writing CLI configs
```

---

## 8. Lifespan Integration

Updated initialization order in `main.py` lifespan:

```
...existing init through SkillRegistry...
→ Load ProxyFleetConfig from mcp_proxy_config_path
→ Create ProxyManager(config, vault, governance)
→ Create ApprovalTokenManager(jwt_secret, algorithm, approval_token_ttl_seconds)
→ Create MCPServiceBridge(..., proxy_manager=proxy_manager)
→ Create MCP Server (with proxy-aware tool listing)
→ proxy_manager.start_all()
→ Set approval_token_manager on ToolGovernance and tool_approvals router
...rest of existing init...
```

Shutdown (reverse order):

```
→ proxy_manager.stop_all()
→ ...existing shutdown...
```

---

## 9. Test Strategy

### 9.1 Unit Tests

| Test File | Scope | Key Assertions |
|---|---|---|
| `tests/test_proxy_models.py` | Config model validation | Valid/invalid configs, env interpolation patterns, prefix validation |
| `tests/test_proxy_child.py` | `ChildServerHandle` lifecycle | Start/stop, health state transitions, circuit breaker integration, cooldown behavior |
| `tests/test_proxy_manager.py` | `ProxyManager` aggregation | Tool listing, namespace deconfliction, collision detection, server add/remove, routing |
| `tests/test_approval_tokens.py` | `ApprovalTokenManager` | Issuance, validation, expiry, arg hash mismatch rejection, one-time consumption, revocation |
| `tests/test_arg_hash.py` | Canonical argument hashing | Determinism, key order independence, nested object handling, type stability |
| `tests/test_mcp_sync.py` | Config sync | Push/pull/diff, conflict detection, backup creation, path normalization |
| `tests/test_mcp_proxy_routes.py` | REST API endpoints | CRUD operations, auth enforcement, response shapes |
| `tests/test_approval_token_routes.py` | Token endpoints | Issuance, validation, revocation, error cases |

### 9.2 Integration Tests

| Test File | Scope |
|---|---|
| `tests/test_mcp_proxy_integration.py` | End-to-end: spawn mock child server, discover tools, call through proxy, verify governance |
| `tests/test_approval_token_governance.py` | End-to-end: create approval, issue token, present to MCP tool call, verify consumption |
| `tests/test_proxy_health_monitoring.py` | Health check cycle, circuit breaker transitions, cooldown recovery |

### 9.3 Test Infrastructure

- **Mock MCP Server**: A lightweight `asyncio` server that speaks the MCP stdio protocol and exposes configurable tools. Used by proxy integration tests to avoid spawning real external processes.
- **Frozen time**: Approval token tests use `freezegun` or manual clock injection to test expiry without real delays.
- **Circuit breaker injection**: `ChildServerHandle` accepts clock and circuit-breaker factory parameters for deterministic testing.

### 9.4 Validation Gates (from Roadmap)

- [ ] Windows child process spawn works for `npx`, `uvx`, and native executables
- [ ] Prefixed proxy tools do not collide with native tools
- [ ] Expired or mismatched approval tokens fail deterministically
- [ ] Sync tool preserves existing user config unless `--force` is provided
- [ ] Existing MCP server tests remain green (no regression)
- [ ] Existing approval/governance tests remain green

---

## 10. File Layout

### New Files

```
engine/src/agent33/mcp_server/
    proxy_models.py          # ProxyServerConfig, ProxyFleetConfig, ProxyServerAuth, ProxyServerGovernance
    proxy_child.py           # ChildServerHandle, ChildServerState
    proxy_manager.py         # ProxyManager
    sync.py                  # NormalizedMCPEntry, CLITarget, SyncConfig, sync operations

engine/src/agent33/security/
    approval_tokens.py       # ApprovalTokenManager, ApprovalTokenPayload, ApprovalTokenError
    arg_hash.py              # canonical_arg_hash()

engine/src/agent33/api/routes/
    mcp_proxy.py             # Proxy management REST endpoints
    mcp_sync.py              # Sync operation REST endpoints

engine/mcp.config.json       # Default proxy fleet configuration (empty fleet)

tests/
    test_proxy_models.py
    test_proxy_child.py
    test_proxy_manager.py
    test_approval_tokens.py
    test_arg_hash.py
    test_mcp_sync.py
    test_mcp_proxy_routes.py
    test_approval_token_routes.py
    test_mcp_proxy_integration.py
    test_approval_token_governance.py
    test_proxy_health_monitoring.py
```

### Modified Files

```
engine/src/agent33/mcp_server/server.py     # Proxy-aware tool listing and call dispatch
engine/src/agent33/mcp_server/bridge.py     # Add proxy_manager field
engine/src/agent33/mcp_server/auth.py       # Add proxy tool scopes and resource scopes
engine/src/agent33/mcp_server/resources.py  # Add proxy-servers resource
engine/src/agent33/tools/governance.py      # Add approval token validation path
engine/src/agent33/tools/approvals.py       # (no model changes, but service gains token issuance hook)
engine/src/agent33/api/routes/tool_approvals.py  # Extended decision response with token, new token endpoints
engine/src/agent33/config.py                # New settings for proxy, tokens, sync
engine/src/agent33/main.py                  # Lifespan: init ProxyManager, ApprovalTokenManager
```

---

## 11. Security Considerations

### 11.1 Token Security

- Approval tokens use the same signing key as auth JWTs (`jwt_secret`). If a separate key is desired for defense-in-depth, a `approval_token_secret` setting can be added.
- The `typ: "a33_approval"` claim prevents approval tokens from being used as auth tokens (the auth middleware checks for standard JWT claims, not the approval type).
- Argument hashing prevents an attacker from obtaining an approval for `rm /tmp/safe` and using the token to execute `rm /`.
- One-time consumption prevents replay attacks.
- Short TTL (5 minutes default) limits the window of opportunity.

### 11.2 Proxy Security

- Child server credentials are resolved from env vars or the `CredentialVault`, never stored in `mcp.config.json` in plaintext.
- Each proxy server has its own governance policy. A proxy tool inherits the combined governance of its own server policy and the AGENT-33 tool governance layer.
- Proxy tools run through the same `ToolGovernance.pre_execute_check()` as native tools, ensuring rate limiting, autonomy enforcement, and scope checks apply uniformly.
- Proxy server processes are spawned with the minimum required environment. Sensitive env vars are injected only for the specific child that needs them.

### 11.3 Sync Security

- The sync tool only writes MCP server registrations. It does not modify other CLI configuration.
- Backup files are created before any write.
- Env var references in sync entries use `${VAR}` syntax (resolved by the CLI at runtime), not plaintext values.

---

## 12. Migration and Backward Compatibility

- **No breaking changes**: All existing MCP tools, resources, and auth flows continue to work. Proxy and approval token features are additive.
- **Feature flags**: `mcp_proxy_enabled` and `approval_token_enabled` settings default to `False` / `True` respectively, allowing incremental rollout.
- **Existing approval flow preserved**: The `__approval_id` consumption path in `ToolGovernance` remains functional. The new `__approval_token` path is an alternative, not a replacement.
- **MCP SDK optional**: The `mcp` package remains an optional dependency. If not installed, proxy features are disabled gracefully (same pattern as existing `_HAS_MCP` guard).

---

## 13. Open Questions for Implementation

1. **Separate signing key for approval tokens?** Using the same `jwt_secret` is simpler but means a compromised auth key compromises approvals too. A separate `approval_token_secret` adds defense-in-depth at the cost of one more secret to manage.

2. **Consumed token storage durability.** The in-memory consumed set is lost on restart. For short TTLs (5 min), this is acceptable (expired tokens cannot be replayed anyway). For longer TTLs, consider Redis-backed consumed set.

3. **Proxy child restart policy.** Should unhealthy children auto-restart after cooldown, or require manual intervention? The architecture supports both; the `auto_restart` config flag can control this.

4. **SSE transport for proxy children.** The initial implementation focuses on stdio transport (most common for MCP servers). SSE support is architecturally planned but may be deferred to a follow-up PR if the MCP client SDK's SSE support needs additional work.

5. **Gemini CLI config format.** The Gemini CLI MCP integration is newer and its config format may not be fully stabilized. The sync module should treat Gemini as a best-effort target with a clear warning if the config format is not recognized.
