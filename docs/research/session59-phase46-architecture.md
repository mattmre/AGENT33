# Phase 46: Dynamic Tool Catalog and Semantic Skill Resolution — Architecture

Date: 2026-03-10
Session: 59
Status: Research / pre-implementation

## 1. Problem Statement

AGENT-33's current tool and skill surfaces have three structural gaps:

1. **No runtime tool catalog endpoint.** The `ToolRegistry` tracks tools and metadata entries internally, but there is no API endpoint that returns grouped, filtered, runtime-truth tool metadata. The frontend and MCP clients must either hardcode assumptions or query low-level registry internals.

2. **No semantic skill resolution.** The `SkillRegistry.search()` method performs substring matching across name, description, and tags. The `SkillMatcher` adds BM25 retrieval and LLM filtering, but this pipeline is designed for prompt injection safety, not for operator or agent discovery of skills by natural-language objective.

3. **No session-scoped tool activation.** All registered tools are visible to all agents at all times. There is no concept of a session-scoped activation set that reduces context bloat by hiding non-core tools until explicitly discovered.

Phase 46 closes these gaps by adding a dynamic tool catalog, semantic skill resolution, and session-scoped activation sets.

## 2. Existing Codebase Inventory

### Tool Framework

| File | Role | Key types |
| --- | --- | --- |
| `engine/src/agent33/tools/base.py` | Protocol definitions | `Tool`, `SchemaAwareTool`, `ToolContext`, `ToolResult` |
| `engine/src/agent33/tools/registry.py` | Central registry | `ToolRegistry` — `register()`, `list_all()`, `list_entries()`, `validated_execute()`, `discover_from_entrypoints()`, `discover_mcp_stdio_server()`, `discover_mcp_sse_server()`, `load_definitions()` |
| `engine/src/agent33/tools/registry_entry.py` | Metadata model | `ToolRegistryEntry` — `tool_id`, `name`, `version`, `description`, `owner`, `provenance`, `scope`, `approval`, `status`, `tags`, `parameters_schema`, `result_schema` |
| `engine/src/agent33/tools/schema.py` | Schema validation | `validate_params()`, `get_tool_schema()`, `generate_tool_description()` |
| `engine/src/agent33/tools/governance.py` | Pre-execution checks | `ToolGovernance` — permission, autonomy, rate limiting, allowlists, audit |

### Skill Framework

| File | Role | Key types |
| --- | --- | --- |
| `engine/src/agent33/skills/definition.py` | Skill model | `SkillDefinition` — name, version, description, instructions, allowed_tools, tags, dependencies, status |
| `engine/src/agent33/skills/registry.py` | Central registry | `SkillRegistry` — `discover()`, `register()`, `search()`, `find_by_tag()`, `find_by_tool()`, progressive disclosure (`get_metadata_only`, `get_full_instructions`, `get_resource`) |
| `engine/src/agent33/skills/matching.py` | 4-stage matcher | `SkillMatcher` — BM25 retrieval, LLM lenient filter, content loading, LLM strict filter |
| `engine/src/agent33/skills/injection.py` | Prompt injection | `SkillInjector` — L0/L1/L2 progressive disclosure, tool context resolution |

### Pack Framework

| File | Role |
| --- | --- |
| `engine/src/agent33/packs/registry.py` | `PackRegistry` — discover, install, uninstall, upgrade, enable/disable (tenant-scoped) |
| `engine/src/agent33/packs/marketplace.py` | `LocalPackMarketplace` — filesystem catalog, version resolution |
| `engine/src/agent33/packs/provenance.py` | HMAC signing, trust evaluation |

### Embedding Infrastructure

| File | Role |
| --- | --- |
| `engine/src/agent33/memory/embeddings.py` | `EmbeddingProvider` — Ollama-backed vector generation |
| `engine/src/agent33/memory/cache.py` | `EmbeddingCache` — LRU caching for embeddings |
| `engine/src/agent33/memory/hybrid.py` | `HybridSearcher` — BM25 + vector via RRF |
| `engine/src/agent33/memory/bm25.py` | `BM25Index` — in-memory BM25 |

### Existing API Routes

- `/v1/plugins` — plugin CRUD and health
- `/v1/packs` — pack install, enable, search
- No `/v1/tools/catalog` or `/v1/skills/resolve` endpoints exist today

## 3. Dynamic Tool Catalog

### 3.1 Catalog Data Model

```python
# engine/src/agent33/tools/catalog.py

class ToolCatalogEntry(BaseModel):
    """A single tool in the runtime catalog."""
    name: str
    description: str
    version: str = ""
    category: str = ""                   # e.g. "files", "runtime", "web", "messaging"
    source: str = ""                     # "core", "plugin:<id>", "pack:<id>", "mcp:<server>"
    status: ToolStatus = ToolStatus.ACTIVE
    available: bool = True               # effective availability for the requesting context
    unavailable_reason: str = ""         # why it's not available (missing config, disabled, etc.)
    parameters_schema: dict[str, Any] = {}
    result_schema: dict[str, Any] = {}
    tags: list[str] = []
    provenance: ToolProvenance | None = None
    requires_approval: bool = False
    last_used: datetime | None = None    # optional usage tracking

class ToolCatalogGroup(BaseModel):
    """Tools grouped by category."""
    category: str
    tools: list[ToolCatalogEntry]

class ToolCatalogResponse(BaseModel):
    """Full catalog response."""
    groups: list[ToolCatalogGroup]
    total_count: int
    active_count: int
    discovery_mode: str                  # "legacy" or "dynamic"
```

### 3.2 Catalog Service

```python
# engine/src/agent33/tools/catalog_service.py

class ToolCatalogService:
    """Builds runtime-truth tool catalogs from ToolRegistry + SkillRegistry + PackRegistry."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        skill_registry: SkillRegistry | None = None,
        pack_registry: PackRegistry | None = None,
    ) -> None: ...

    def build_catalog(
        self,
        *,
        tenant_id: str = "",
        agent_id: str = "",
        session_id: str = "",
        include_schemas: bool = False,
        category_filter: str = "",
    ) -> ToolCatalogResponse:
        """Build the full catalog with grouping, filtering, and availability."""
        ...

    def get_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """Return the full JSON Schema for a specific tool."""
        ...

    def search_catalog(self, query: str) -> list[ToolCatalogEntry]:
        """Text search across catalog entries."""
        ...
```

The service resolves tool source labels by checking:
1. Whether the tool was registered by a pack (check `PackRegistry` for matching skill names)
2. Whether the tool was discovered from an MCP server (check `_mcp_manager`)
3. Whether the tool came from an entrypoint (check entrypoint metadata)
4. Default to `"core"` for built-in tools

### 3.3 Tool Category Taxonomy

Initial category assignments (configurable via tool tags or a static mapping):

| Category | Tools |
| --- | --- |
| `files` | `file_ops`, `apply_patch` (future) |
| `runtime` | `shell`, `execute_code` |
| `web` | `web_fetch`, `web_search`, `browser` |
| `messaging` | `telegram`, `discord`, `slack`, `whatsapp` |
| `media` | `voice`, `image` |
| `sessions` | session management tools |
| `automation` | cron, webhook tools |
| `mcp` | MCP-proxied tools (prefixed) |

### 3.4 API Endpoints

```
GET  /v1/tools/catalog                — full grouped catalog
GET  /v1/tools/catalog/{name}         — single tool detail with schema
GET  /v1/tools/catalog/{name}/schema  — raw JSON Schema only
GET  /v1/tools/catalog/search?q=...   — text search
```

Route file: `engine/src/agent33/api/routes/tool_catalog.py`

Query parameters for the catalog endpoint:
- `category` — filter by category
- `source` — filter by source (core, plugin, pack, mcp)
- `include_schemas` — include full parameter schemas (default false for bandwidth)
- `status` — filter by status (active, deprecated, blocked)

### 3.5 TOOL_DISCOVERY_MODE

A new config setting in `engine/src/agent33/config.py`:

```python
tool_discovery_mode: str = Field(
    default="legacy",
    description="'legacy' exposes all tools; 'dynamic' hides non-core tools by default",
)
```

In `dynamic` mode:
- Only tools tagged as `core` are visible in the default tool list
- Agents can discover additional tools via the `discover_tools` meta-tool
- Exact-name execution always works regardless of visibility (governance still applies)

### 3.6 discover_tools Meta-Tool

A built-in tool that queries the catalog:

```python
# engine/src/agent33/tools/builtin/discover_tools.py

class DiscoverToolsTool:
    """Meta-tool that searches the runtime tool catalog."""

    name = "discover_tools"
    description = "Search for available tools by keyword or category"

    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "category": {"type": "string", "description": "Category filter"},
        },
        "required": ["query"],
    }
```

This tool returns catalog entries matching the query and, when in `dynamic` mode, adds matched tools to the session's activation set.

## 4. Session-Scoped Tool Activation

### 4.1 Activation Set Model

```python
# engine/src/agent33/tools/activation.py

class ToolActivationSet(BaseModel):
    """Session-scoped set of activated tools."""
    session_id: str
    tenant_id: str
    core_tools: list[str]              # always visible
    activated_tools: set[str] = set()  # discovered during session
    deactivated_tools: set[str] = set()  # explicitly hidden
    created_at: datetime
    updated_at: datetime

class ToolActivationManager:
    """Manages per-session tool activation state."""

    def __init__(self, core_tools: list[str] | None = None) -> None:
        self._sets: dict[str, ToolActivationSet] = {}
        self._core_tools = core_tools or [
            "shell", "file_ops", "web_fetch", "web_search",
            "discover_tools", "resolve_workflow",
        ]

    def get_or_create(self, session_id: str, tenant_id: str) -> ToolActivationSet:
        ...

    def activate(self, session_id: str, tool_names: list[str]) -> None:
        """Add tools to the session's activation set."""
        ...

    def deactivate(self, session_id: str, tool_names: list[str]) -> None:
        """Remove tools from the session's activation set."""
        ...

    def is_visible(self, session_id: str, tool_name: str) -> bool:
        """Check if a tool should be visible in the current session."""
        ...

    def list_visible(self, session_id: str) -> list[str]:
        """Return all tool names visible in the session."""
        ...
```

### 4.2 MCP tools/list_changed

When the activation set changes, the MCP server should emit a `tools/list_changed` notification to connected clients. This is wired through `engine/src/agent33/mcp_server/server.py`.

### 4.3 Persistence

Activation sets are stored in-memory by default. For durable sessions (Phase 44 continuity), they can be persisted to the filesystem session state service under `~/.agent33/sessions/{session_id}/activation.json`.

## 5. Semantic Skill Resolution

### 5.1 Architecture Overview

Semantic skill resolution adds an embedding-based retrieval layer that sits alongside (not replacing) the existing BM25 + LLM 4-stage matcher. The key difference:

- **SkillMatcher** (existing) is designed for *prompt injection safety* — it filters skills before injecting them into agent prompts.
- **SemanticSkillResolver** (new) is designed for *discovery* — it matches natural-language objectives to skills/tools and returns ranked results.

### 5.2 Skill Embedding Index

```python
# engine/src/agent33/skills/semantic.py

class SkillEmbeddingIndex:
    """Maintains an embedding index over skill metadata for semantic search."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        embedding_cache: EmbeddingCache | None = None,
    ) -> None:
        self._provider = embedding_provider
        self._cache = embedding_cache
        self._embeddings: dict[str, list[float]] = {}  # skill_name -> vector
        self._metadata: dict[str, dict[str, str]] = {}  # skill_name -> {name, description, category, tags}

    async def index_skill(self, skill: SkillDefinition) -> None:
        """Compute and store embedding for a single skill."""
        text = self._build_index_text(skill)
        vector = await self._embed(text)
        self._embeddings[skill.name] = vector
        self._metadata[skill.name] = {
            "name": skill.name,
            "description": skill.description,
            "tags": ", ".join(skill.tags),
        }

    async def index_all(self, skills: list[SkillDefinition]) -> int:
        """Index all skills. Returns count indexed."""
        ...

    async def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Return (skill_name, similarity_score) pairs ranked by cosine similarity."""
        query_vector = await self._embed(query)
        return self._cosine_rank(query_vector, top_k)

    def _build_index_text(self, skill: SkillDefinition) -> str:
        """Combine skill metadata into a single indexable string."""
        parts = [skill.name, skill.description]
        parts.extend(skill.tags)
        if skill.instructions:
            # Include first 500 chars of instructions for richer semantic signal
            parts.append(skill.instructions[:500])
        return " ".join(parts)

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        ...

    def _cosine_rank(self, query_vec: list[float], top_k: int) -> list[tuple[str, float]]:
        ...
```

### 5.3 Weighted Fuzzy Search

The `SkillRegistry` gets a new weighted search method that combines BM25 and embedding similarity via reciprocal rank fusion (RRF), reusing the same pattern already proven in `engine/src/agent33/memory/hybrid.py`:

```python
# Added to engine/src/agent33/skills/registry.py

async def weighted_search(
    self,
    query: str,
    *,
    embedding_index: SkillEmbeddingIndex | None = None,
    bm25_weight: float = 0.4,
    semantic_weight: float = 0.6,
    top_k: int = 10,
) -> list[tuple[SkillDefinition, float]]:
    """Hybrid BM25 + semantic search over skills."""
    ...
```

Field weighting for BM25 scoring:
- `name`: weight 3.0
- `description`: weight 2.0
- `category`: weight 1.5
- `tags`: weight 1.0
- `instructions` (first 500 chars): weight 0.5

### 5.4 resolve_workflow Tool

A built-in tool exposed to agents and via MCP:

```python
# engine/src/agent33/tools/builtin/resolve_workflow.py

class ResolveWorkflowTool:
    """Resolve a natural-language objective to matching skills and workflows."""

    name = "resolve_workflow"
    description = (
        "Given a natural-language objective, find the best matching skills "
        "and workflow templates. Returns skill instructions and metadata."
    )

    parameters_schema = {
        "type": "object",
        "properties": {
            "objective": {
                "type": "string",
                "description": "Natural-language description of what you want to accomplish",
            },
            "max_results": {
                "type": "integer",
                "default": 3,
                "description": "Maximum number of matching skills to return",
            },
        },
        "required": ["objective"],
    }
```

The tool:
1. Runs `weighted_search` against the skill registry
2. Filters out deprecated/disabled skills
3. Returns skill metadata (L0) and optionally full instructions (L1) for top matches
4. Records the resolution in the session for context tracking

### 5.5 Integration with Existing SkillMatcher

The existing 4-stage `SkillMatcher` is preserved for prompt injection. The new `SemanticSkillResolver` is used for:
- The `resolve_workflow` tool
- The skill discovery API endpoint
- Pack-provided skill search

The two systems share the same `SkillRegistry` data but serve different purposes. The `SemanticSkillResolver` prepends deterministic fuzzy retrieval for discovery, then optionally delegates to the `SkillMatcher` for injection safety when results will be injected into prompts.

### 5.6 Skill Resolution API Endpoints

```
POST /v1/skills/resolve              — semantic skill resolution
GET  /v1/skills/search?q=...         — weighted fuzzy search
GET  /v1/skills/{name}               — skill detail with instructions
GET  /v1/skills/{name}/metadata      — L0 metadata only
```

Route file: `engine/src/agent33/api/routes/skill_resolution.py`

## 6. Integration with Pack-Provided Skills

Pack-provided skills are already registered in the `SkillRegistry` with qualified names (`pack_name/skill_name`). The semantic index treats them identically:

1. When a pack is installed, its skills are indexed in the `SkillEmbeddingIndex`
2. When a pack is uninstalled, its skill embeddings are removed
3. The `ToolCatalogService` labels pack-provided tools with `source: "pack:<name>"`
4. Tenant enablement is respected: if a pack is disabled for a tenant, its skills are excluded from that tenant's search results

## 7. Wiring into main.py Lifespan

The new components slot into the existing initialization order:

```
... existing init ...
→ EmbeddingProvider → EmbeddingCache
→ SkillRegistry → SkillInjector
→ ToolRegistry

... new Phase 46 init ...
→ SkillEmbeddingIndex (uses EmbeddingProvider, indexes SkillRegistry)
→ ToolCatalogService (uses ToolRegistry, SkillRegistry, PackRegistry)
→ ToolActivationManager (configured from settings.tool_discovery_mode)
→ Register discover_tools and resolve_workflow as built-in tools
→ Wire catalog service and activation manager into MCP server
```

Stored on `app.state`:
- `app.state.tool_catalog_service`
- `app.state.tool_activation_manager`
- `app.state.skill_embedding_index`

## 8. File Layout

### New Files

```
engine/src/agent33/tools/catalog.py               — catalog data models
engine/src/agent33/tools/catalog_service.py        — catalog builder service
engine/src/agent33/tools/activation.py             — session-scoped activation sets
engine/src/agent33/tools/builtin/discover_tools.py — discover_tools meta-tool
engine/src/agent33/tools/builtin/resolve_workflow.py — resolve_workflow tool
engine/src/agent33/skills/semantic.py              — embedding index for skills
engine/src/agent33/api/routes/tool_catalog.py      — catalog API endpoints
engine/src/agent33/api/routes/skill_resolution.py  — skill resolution API endpoints
```

### Modified Files

```
engine/src/agent33/config.py                       — add tool_discovery_mode setting
engine/src/agent33/main.py                         — lifespan init for new services
engine/src/agent33/tools/registry.py               — add source tracking helpers
engine/src/agent33/skills/registry.py              — add weighted_search method
engine/src/agent33/mcp_server/server.py            — session-filtered tool lists, tools/list_changed
engine/src/agent33/agents/runtime.py               — expose resolve_workflow in agent context
```

### Test Files

```
engine/tests/test_tool_catalog.py                  — catalog model and service tests
engine/tests/test_tool_activation.py               — activation set lifecycle tests
engine/tests/test_discover_tools.py                — discover_tools tool execution tests
engine/tests/test_resolve_workflow.py              — resolve_workflow tool execution tests
engine/tests/test_skill_semantic.py                — embedding index and search tests
engine/tests/test_tool_catalog_routes.py           — API endpoint tests
engine/tests/test_skill_resolution_routes.py       — skill resolution API tests
```

## 9. Test Strategy

### Unit Tests

1. **Catalog model tests** — verify `ToolCatalogEntry`, `ToolCatalogGroup`, and `ToolCatalogResponse` serialization and grouping
2. **Catalog service tests** — mock `ToolRegistry`, `SkillRegistry`, `PackRegistry`; verify source labeling, category grouping, availability resolution, and schema lookup
3. **Activation set tests** — create, activate, deactivate, visibility checks, core tool always-visible invariant, session isolation
4. **Semantic index tests** — mock `EmbeddingProvider`; verify indexing, cosine similarity ranking, and RRF fusion with BM25
5. **discover_tools tests** — verify search delegation, activation in dynamic mode, result formatting
6. **resolve_workflow tests** — verify semantic resolution, deprecated skill exclusion, L0/L1 output modes, pack-provided skill inclusion

### Integration Tests

1. **Catalog API tests** — test with `TestClient`; verify grouping, filtering, schema inclusion, tenant scoping
2. **Skill resolution API tests** — test semantic search endpoint with mocked embeddings
3. **MCP integration tests** — verify session-filtered tool listings and `tools/list_changed` signaling
4. **Discovery mode tests** — verify legacy mode shows all tools, dynamic mode hides non-core, exact-name still works

### Behavioral Assertions (Anti-Corner-Cutting)

- Every test must assert on specific expected output, not just `status == 200`
- Catalog tests must verify actual tool names, categories, and source labels
- Activation tests must verify session isolation (activating in session A does not affect session B)
- Semantic search tests must verify ranking order, not just non-empty results
- Discovery mode tests must verify both the hidden and visible sides

## 10. Validation Gates

From the Phase 46 plan:

1. Dynamic mode hides non-core tools by default without breaking exact-name execution
2. Activation sets remain isolated by session and tenant
3. Fuzzy skill resolution returns stable top results for natural-language objectives
4. `resolve_workflow` does not inject deprecated or disabled skills

Additional gates:

5. Catalog endpoint returns runtime truth that matches `ToolRegistry.list_all()` in legacy mode
6. Pack-provided skills appear in semantic search results when the pack is enabled for the tenant
7. Schema lookup returns valid JSON Schema for all `SchemaAwareTool` implementations
8. MCP `tools/list_changed` fires when activation sets change

## 11. Convergence with OpenClaw Track Phase 2

Phase 46 directly satisfies the following OpenClaw backlog items:

| Backlog ID | Description | Phase 46 coverage |
| --- | --- | --- |
| OC-TOOL-001 | Runtime tool catalog endpoint | `GET /v1/tools/catalog` |
| OC-TOOL-002 | Grouped tool metadata | `ToolCatalogGroup` with category taxonomy |
| OC-TOOL-003 | Tool provenance labels | `source` field: core, plugin, pack, mcp |
| OC-TOOL-004 | Effective availability per agent | `available` + `unavailable_reason` fields |
| OC-TOOL-005 | Tool profiles | Covered by `TOOL_DISCOVERY_MODE` + activation sets |
| OC-TOOL-007 | Schema lookup surface | `GET /v1/tools/catalog/{name}/schema` |
| OC-TOOL-009 | Search and filtering | `GET /v1/tools/catalog/search` + query params |
| OC-TOOL-010 | Unsupported/disabled reasons | `unavailable_reason` field |

This ensures Phase 46 and OpenClaw Track Phase 2 are delivered as one coherent implementation rather than parallel efforts.

## 12. Risks and Open Questions

1. **Embedding availability**: Semantic search requires Ollama or an alternative embedding provider. When unavailable, the system must degrade gracefully to BM25-only search. The `SkillEmbeddingIndex` should handle `EmbeddingProvider` failures without blocking catalog operations.

2. **Index staleness**: When skills are added/removed at runtime (e.g., pack install/uninstall), the embedding index must be updated. The current plan uses synchronous re-indexing on pack lifecycle events; for large skill sets, background re-indexing with a stale-read window may be needed.

3. **Activation set persistence**: In-memory activation sets are lost on restart. The Phase 44 filesystem session state is the natural persistence backend, but Phase 46 should not hard-depend on Phase 44 being complete. Graceful degradation: on restart, all sessions start with core tools only.

4. **Category assignment**: The initial category taxonomy is hardcoded. A future improvement is to let tools self-declare their category via tags or schema metadata, or to use the embedding index to auto-classify.
