# EVOKORE-Informed Integration Roadmap (Phases 44-48)

## Background

`AGENT33_IMPROVEMENT_INSTRUCTIONS.md` identifies a set of operating-system-level capabilities proven in EVOKORE-MCP that AGENT-33 should absorb next. Most of the requested features are not greenfield work: AGENT-33 already has partial implementations in the hook framework, MCP server, tool governance, pack registry, session memory, and multimodal subsystems. The right execution strategy is to extend those existing systems rather than introduce parallel frameworks.

This roadmap defines the next five phases after Phase 43. It treats the EVOKORE patterns as a convergence wave across four existing AGENT-33 foundations:

1. Phase 32 connector boundary, hooks, and plugin/pack extensibility
2. Phase 33 skill packs and ecosystem distribution
3. Phase 35 multimodal and voice lifecycle scaffolding
4. Phase 43 MCP server interoperability

## Design Principles

- Extend existing runtime contracts before adding new top-level services.
- Keep tenant isolation, governance, and auditability intact for every imported capability.
- Prefer pack/workflow integration for imported skills instead of hardcoding one-off behavior.
- Treat Claude Code hooks and cross-CLI sync as first-class operator surfaces, not local scripts with no lifecycle ownership.
- Preserve fail-open behavior for local hook scripts, but keep fail-closed behavior for governed tool execution and approval validation.

## Integration Map

| EVOKORE capability | Existing AGENT-33 surface to extend | Target phase |
| --- | --- | --- |
| Multi-server MCP aggregation | `engine/src/agent33/mcp_server/`, `engine/src/agent33/tools/registry.py`, connector boundary from Phase 32 | 45 |
| Cryptographic HITL approval tokens | `engine/src/agent33/tools/governance.py`, `engine/src/agent33/tools/approvals.py`, `engine/src/agent33/api/routes/tool_approvals.py` | 45 |
| Dynamic tool discovery | `engine/src/agent33/tools/registry.py`, `engine/src/agent33/mcp_server/server.py`, session storage | 46 |
| Semantic skill resolution | `engine/src/agent33/skills/registry.py`, `engine/src/agent33/skills/matching.py`, `engine/src/agent33/agents/runtime.py` | 46 |
| Claude Code hook lifecycle | `engine/src/agent33/hooks/`, `engine/src/agent33/observability/`, repo `.claude/settings.json` | 44 |
| Cross-CLI MCP registration sync | `engine/src/agent33/mcp_server/`, `scripts/`, release/distribution docs | 45 |
| Live status line | hook/session cache layer, tool/skill registries, git metadata | 48 |
| Voice sidecar | `engine/src/agent33/multimodal/voice_daemon.py`, new `engine/src/agent33/voice/`, ElevenLabs connector wiring | 48 |
| Comprehensive skill library | `engine/src/agent33/skills/`, `engine/src/agent33/packs/`, `core/workflows/skills/`, SkillsBench adapter | 47 |
| Fail-safe design + session continuity | `engine/src/agent33/hooks/`, `engine/src/agent33/memory/session.py`, `engine/src/agent33/observability/`, CLAUDE/memory docs | 44 |

## Dependency Chain

```text
Phase 44 -> Phase 45 -> Phase 46 -> Phase 47 -> Phase 48
     |          |           |           |
     |          |           |           +-> pack/workflow adoption depends on discovery + activation
     |          |           +-> dynamic discovery depends on durable session state + hook-safe metadata flow
     |          +-> secure MCP fabric depends on session continuity + fail-safe execution contracts
     +-> establishes local operator state, hook safety, replay logging, and continuity contracts
```

## Phase 44: Session Safety, Hook Operating Layer, and Continuity

**Category:** Operator runtime / safety  
**Primary goal:** Turn AGENT-33's existing hook framework into a durable operator operating layer for Claude Code sessions.

### Why this phase comes first

Several requested features depend on durable per-session state and safe local hook execution. AGENT-33 already has request/agent/tool/workflow hooks, but it does not yet own the Claude Code lifecycle surfaces, persistent local session state, or fail-safe hook conventions described in the EVOKORE brief.

### Core deliverables

1. Add a local session state service for CLI sessions under `~/.agent33/`:
   - Purpose metadata
   - task state
   - replay logs
   - cache entries for status surfaces
2. Add repo-level Claude hook scripts under `scripts/hooks/`:
   - `damage-control`
   - `purpose-gate`
   - `session-replay`
   - `tilldone`
3. Add repo `.claude/settings.json` wiring for those hooks.
4. Extend the current in-memory `SessionManager` pattern into a filesystem-backed operator session layer without breaking existing encrypted runtime session usage.
5. Add fail-safe hook conventions:
   - exit `0` on unexpected errors
   - quiet config loading
   - log rotation for replay/audit files
   - sanitized session IDs
6. Seed repo memory surfaces:
   - `memory/MEMORY.md`
   - update `CLAUDE.md` with continuity and memory rules

### Wiring points

| Area | Change |
| --- | --- |
| `engine/src/agent33/memory/session.py` | Split runtime session storage from local operator continuity storage; add durable filesystem backend |
| `engine/src/agent33/hooks/` | Add hook execution helpers for local CLI lifecycle metadata and fail-safe wrappers |
| `engine/src/agent33/observability/` | Route replay and damage-control events into structured audit logs |
| `.claude/settings.json` | Register Claude Code lifecycle hooks |
| `docs/self-improvement/` and `CLAUDE.md` | Document continuity, replay, and memory operating rules |

### Improvement opportunities to weave in

- Reuse the existing hook registry models rather than inventing separate hook metadata schemas.
- Expose replay logs and task state as operator resources later via the MCP server instead of leaving them script-only.
- Align `tilldone` state with existing review/release checklist concepts so completion gates become reusable across workflows.

### Validation gates

- Hook crash simulation still exits `0`
- Replay log rotation works on Windows
- Session purpose survives multiple CLI prompts
- Existing agent/runtime hooks continue to behave unchanged

## Phase 45: Secure MCP Fabric, Tokenized Approvals, and Cross-CLI Distribution

**Category:** Integration / security  
**Primary goal:** Evolve Phase 43 from a single AGENT-33 MCP endpoint into a governed MCP fabric that can proxy child servers safely and register itself across operator CLIs.

### Core deliverables

1. Add `ProxyManager` support in `engine/src/agent33/mcp_server/`:
   - config-driven child server spawn
   - tool prefixing
   - environment interpolation
   - child health/state tracking
   - cooldown protection for repeated failure loops
2. Extend the existing approval model into MCP-safe, stateless approvals:
   - crypto token issuance
   - args hashing with canonical normalization
   - one-time consume semantics
   - expiry windows
3. Inject approval token schema fields into governed tool schemas automatically.
4. Add cross-CLI sync tooling for Claude Code, Claude Desktop, Cursor, and Gemini guidance.
5. Add `mcp.config.json` and engine settings for proxy children, cooldowns, and sync behavior.

### Wiring points

| Area | Change |
| --- | --- |
| `engine/src/agent33/mcp_server/bridge.py` | Expand from service bridge to proxy-aware fabric coordinator |
| `engine/src/agent33/mcp_server/server.py` | Surface aggregated tools/resources and approval-token-aware schemas |
| `engine/src/agent33/tools/governance.py` | Keep current approval flow for REST/runtime, add token consumption path for stateless MCP invocations |
| `engine/src/agent33/tools/approvals.py` | Extend approval records to store normalized arg hashes, expiry, consumption status |
| `engine/src/agent33/security/` | Add HITL token manager primitives and hash normalization utilities |
| `scripts/` | Add config sync command for multi-CLI registration |
| `engine/src/agent33/main.py` | Initialize proxy manager and bind it into MCP + tool registry lifecycle |

### Improvement opportunities to weave in

- Treat proxied MCP servers as connector-boundary participants so they inherit Phase 32 governance, retry, and circuit-breaker behavior.
- Feed child server state into observability and health APIs so the UI and operators can see degraded downstream MCP services.
- Reuse existing `ToolApprovalService` and `/v1/approvals/tools` endpoints instead of building a second approval subsystem.

### Validation gates

- Windows child process spawn works for `npx`, `uvx`, and native executables
- prefixed proxy tools do not collide with native tools
- expired or mismatched approval tokens fail deterministically
- sync tool preserves existing user config unless `--force` is provided

## Phase 46: Dynamic Tool Catalog and Semantic Skill Resolution

**Category:** Tooling / skills / context efficiency  
**Primary goal:** Reduce tool-context bloat and upgrade skill selection from basic search to session-aware activation plus fuzzy objective resolution.

### Core deliverables

1. Add `TOOL_DISCOVERY_MODE` with `legacy` and `dynamic` modes.
2. Introduce a `discover_tools` meta-tool backed by weighted search over tool metadata.
3. Add session-scoped tool activation sets and MCP `tools/list_changed` signaling where supported.
4. Extend `SkillRegistry` with weighted fuzzy search over:
   - name
   - description
   - category
   - full content
5. Add a `resolve_workflow` tool to the runtime/MCP surface that returns the top matching skill bodies for a natural-language objective.
6. Make pack-provided skills and imported workflow skills searchable through the same resolution path.

### Wiring points

| Area | Change |
| --- | --- |
| `engine/src/agent33/tools/registry.py` | Add activation-state tracking and filtered listing APIs |
| `engine/src/agent33/mcp_server/server.py` | Return session-filtered tool listings and support discovery notifications |
| `engine/src/agent33/skills/registry.py` | Add weighted fuzzy indexing and hierarchical scanning |
| `engine/src/agent33/skills/matching.py` | Keep the 4-stage SkillsBench matcher for injection safety, but prepend deterministic fuzzy retrieval for discovery and `resolve_workflow` |
| `engine/src/agent33/agents/runtime.py` | Add workflow-resolution tool exposure and context injection rules |
| `engine/src/agent33/memory/session.py` or new continuity state service | Persist activation sets per session/tenant |

### Improvement opportunities to weave in

- Reuse the existing SkillsBench-oriented matcher as the strict filtering stage after fuzzy retrieval instead of replacing it.
- Expose activation state through the frontend tool catalog planned in the OpenClaw parity track.
- Carry activation state into plugins and tenant capability grants so hidden tools are still policy-scoped correctly.

### Validation gates

- dynamic mode hides non-core tools by default without breaking exact-name execution
- activation sets remain isolated by session and tenant
- fuzzy skill resolution returns stable top results for natural-language objectives
- `resolve_workflow` does not inject deprecated or disabled skills

## Phase 47: Capability Pack Expansion and Workflow Skill Weaving

**Category:** Ecosystem / workflows / distribution  
**Primary goal:** Import the highest-value EVOKORE skills into AGENT-33 as first-class, governable capability packs and wire them into core workflows rather than treating them as loose markdown artifacts.

### Core deliverables

1. Expand the skill format to support the EVOKORE-style frontmatter and hierarchical category layout.
2. Import the highest-value skills as bundled packs:
   - HIVE family
   - `repo-ingestor`
   - `mcp-builder`
   - `planning-with-files`
   - `docs-architect`
   - `pr-manager`
   - `webapp-testing`
3. Add workflow templates or orchestration shortcuts that actually invoke those skills in AGENT-33 flows:
   - implementation session
   - repo ingestion / benchmark intake
   - PR review orchestration
   - doc overhaul
   - Playwright lifecycle testing
4. Wire the new skills into:
   - pack registry and tenant enablement
   - benchmark adapter coverage
   - distribution/marketplace surfaces from Phase 33
5. Add skill provenance and category metadata so the imported library is manageable in the UI and via API.

### Wiring points

| Area | Change |
| --- | --- |
| `core/workflows/skills/` | Add canonical bundled skill layout and imported skill families |
| `engine/src/agent33/skills/loader.py` and `skills/registry.py` | Support EVOKORE frontmatter and recursive discovery |
| `engine/src/agent33/packs/registry.py` | Package imported skills as enableable packs rather than global loose skills |
| `engine/src/agent33/benchmarks/skillsbench/adapter.py` | Validate imported skills against benchmark workflows |
| `engine/src/agent33/api/routes/packs.py` and marketplace surfaces | Surface categories, provenance, enablement, and resolution metadata |
| `workflow-definitions/` and agent definitions | Add templates that explicitly route through the new capability packs |

### Improvement opportunities to weave in

- Use the pack system as the ownership boundary for imported skills so future sync/marketplace work does not need a second distribution model.
- Promote `planning-with-files`, `pr-manager`, and `docs-architect` into AGENT-33-native orchestration patterns, not just skill text.
- Add tenant enablement matrices so enterprise deployments can expose only approved imported capability families.

### Validation gates

- imported skills load through pack discovery with provenance intact
- workflow templates actually invoke the imported capabilities end-to-end
- no imported skill bypasses existing governance/tool permission layers
- benchmark smoke coverage confirms the new skills improve real capability surfaces

## Phase 48: Voice Sidecar, Operator UX, and Production Hardening

**Category:** Multimodal / operator UX / rollout hardening  
**Primary goal:** Finish the operator-facing uplift by turning the current voice scaffold into a real sidecar, adding a live status line, and closing the loop with rollout-grade validation.

### Core deliverables

1. Replace the current voice scaffold with a real standalone sidecar:
   - WebSocket server
   - persona-configured `voices.json`
   - playback abstraction per platform
   - artifact persistence
   - graceful shutdown
2. Wire ElevenLabs as a proxied MCP child where appropriate, but keep the voice sidecar process standalone from the main API runtime.
3. Add a status-line hook using the Phase 44 continuity cache plus live tool/skill/git counts.
4. Expose voice sidecar and status-line health through observability and health APIs.
5. Add rollout hardening:
   - end-to-end operator flows
   - approval + proxy + discovery + voice integration tests
   - release checklist updates

### Wiring points

| Area | Change |
| --- | --- |
| `engine/src/agent33/multimodal/voice_daemon.py` | Deprecate scaffold role in favor of sidecar adapter or compatibility shim |
| `engine/src/agent33/voice/` | New standalone sidecar package and config loader |
| `engine/src/agent33/observability/` and `api/routes/health.py` | Add sidecar status, degraded-state reporting, and operator telemetry |
| `scripts/hooks/` | Add status-line hook backed by cached session/tool/skill/git data |
| `docs/next-session.md`, `CLAUDE.md`, and setup docs | Add operator setup, rollout, and troubleshooting guidance |
| evaluation/release surfaces | Add production confidence gates for voice and operator UX flows |

### Improvement opportunities to weave in

- Reuse the MCP proxy infrastructure from Phase 45 for ElevenLabs tool exposure, but keep real-time audio transport outside the synchronous tool-execution path.
- Surface the status line and voice health in the frontend operations hub later so CLI and web operators see the same state model.
- Use this phase to cleanly retire any remaining placeholder `TODO` voice paths that survived Phase 35.

### Validation gates

- sidecar survives disconnect/reconnect and config hot reload
- status-line hook degrades cleanly when weather/location/network data is unavailable
- no operator hook failure can terminate the session
- multimodal and MCP regression suites remain green

## Execution Strategy

### Recommended PR slicing

| PR wave | Scope |
| --- | --- |
| Wave A | Phase 44 foundations: local session state, hook scripts, `.claude/settings.json`, memory docs |
| Wave B | Phase 45 secure MCP fabric and approval-token extension |
| Wave C | Phase 46 dynamic discovery and `resolve_workflow` |
| Wave D | Phase 47 imported packs and workflow weaving |
| Wave E | Phase 48 voice sidecar, status line, and release hardening |

### Suggested review order

1. Security and governance review for Phases 44-45
2. Runtime/context budget review for Phase 46
3. Ecosystem and workflow review for Phase 47
4. Multimodal and operator UX review for Phase 48

## Success Metrics

- AGENT-33 can expose native and proxied MCP tools through one governed fabric.
- Tool approvals work consistently for REST, iterative runtime execution, and stateless MCP clients.
- Default tool visibility is reduced without losing exact-name execution capability.
- Imported EVOKORE skills are governable, pack-managed, tenant-aware, and workflow-reachable.
- Claude Code sessions gain durable purpose, replay, completion gating, and status feedback.
- Voice support moves from scaffold to deployable sidecar without regressing the main runtime.
