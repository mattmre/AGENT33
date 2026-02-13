# Research: Tool Registry State Analysis — 2026-02-12

## Current Implementation

### Registry Core (`engine/src/agent33/tools/registry.py`, 53 lines)
- `ToolRegistry` class with simple `dict[str, Tool]` storage
- Methods: `register()`, `get()`, `list_all()`, `discover_from_entrypoints()`
- No versioning, ownership, provenance, or approval tracking

### Tool Protocol (`engine/src/agent33/tools/base.py`, 55 lines)
- `ToolContext`: user_scopes, command_allowlist, path_allowlist, domain_allowlist, working_dir
- `ToolResult`: success, output, error
- `Tool` Protocol: name, description, execute()

### Tool Governance (`engine/src/agent33/tools/governance.py`, 107 lines)
- `ToolGovernance` class with scope/allowlist enforcement
- Pre-execute checks for shell commands, file paths, domains
- Audit logging with structured output

### Built-in Tools (6 total)
| Tool | File | Lines | Key Features |
|------|------|-------|-------------|
| browser | `tools/builtin/browser.py` | 257 | Playwright automation, session mgmt |
| file_ops | `tools/builtin/file_ops.py` | 110 | Read/write/list with path allowlist |
| reader | `tools/builtin/reader.py` | 151 | Jina Reader + trafilatura fallback |
| search | `tools/builtin/search.py` | 83 | SearXNG integration |
| shell | `tools/builtin/shell.py` | 83 | Command allowlist, timeout control |
| web_fetch | `tools/builtin/web_fetch.py` | 89 | HTTP GET/POST, domain allowlist |

### Tool Definitions (`engine/tool-definitions/`)
- Only `shell.yml` exists (65 lines) — includes version, parameters, governance
- Missing: browser.yml, file_ops.yml, reader.yml, search.yml, web_fetch.yml

### Existing Governance Docs
- `core/orchestrator/TOOL_REGISTRY_CHANGE_CONTROL.md` (303 lines) — full schema, CCC-01–04, PRV-01–12
- `core/orchestrator/TOOL_GOVERNANCE.md` (53 lines) — allowlist policy
- `core/orchestrator/TOOL_DEPRECATION_ROLLBACK.md` (274 lines) — 4-phase deprecation, RB-01–03
- `core/orchestrator/TOOLS_AS_CODE.md` (51 lines) — progressive disclosure

## Gap Analysis (Phase 12 Spec vs Current)

| Field | Spec | Implemented | Status |
|-------|------|-------------|--------|
| tool_id | ✅ | ❌ | Missing |
| name | ✅ | ✅ | Exists |
| version | ✅ | ❌ | Missing |
| owner | ✅ | ❌ | Missing |
| provenance (repo, commit, checksum, license) | ✅ | ❌ | Missing |
| scope (commands, endpoints, data_access, network, filesystem) | ✅ | ⚠️ | Partial (runtime only) |
| approval (approver, date, evidence) | ✅ | ❌ | Missing |
| status (active/deprecated/blocked) | ✅ | ❌ | Missing |
| last_review / next_review | ✅ | ❌ | Missing |
| description | ✅ | ✅ | Exists |

**Summary**: 2/20 fields exist (10%), 4/20 partial (20%), 14/20 missing (70%)

## Implementation Priorities
1. Create `ToolRegistryEntry` data model with all Phase 12 fields
2. Create missing tool definition YAML files (5 tools)
3. Add provenance/version/owner to existing shell.yml
4. Implement registration validation against governance checklists
5. Add status management and deprecation tracking
