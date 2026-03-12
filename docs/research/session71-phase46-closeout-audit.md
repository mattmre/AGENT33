# Session 71 Phase 46 Closeout Audit

**Date:** 2026-03-12  
**Scope:** Closeout audit for the already-merged Phase 46 discovery and session-activation work from PRs `#172` and `#173`

## Goal

Reconcile the Phase 46 roadmap against what actually landed on `main`, then close the highest-value remaining gap without destabilizing the newly merged discovery surface.

## Baseline Audit

Before this slice, `main` already had:

- `DiscoveryService` for tool, skill, and workflow/template discovery
- `/v1/discovery/*` routes
- MCP `discover_tools`, `discover_skills`, and `resolve_workflow`
- session-scoped dynamic tool visibility via `ToolActivationManager`

However, two meaningful gaps remained relative to the intent of the Phase 46 roadmap:

1. **Skill discovery was still shallow.**
   - ranking only considered `name`, `description`, tags, and allowed tools
   - instructions content and path/pack metadata were ignored
   - this undercut natural-language matching for workflow-oriented skills

2. **`resolve_workflow` was workflow-only in practice.**
   - it returned runtime workflows and templates
   - it did not surface workflow-like skills for natural-language objectives
   - it also did not consistently carry tenant filtering into the workflow-resolution path

## Delivered in This Slice

### 1. Weighted lexical skill ranking

`DiscoveryService.discover_skills()` now ranks skills using richer signals:

- canonical skill name
- description
- tags and allowed tools
- instruction excerpt
- pack/path metadata terms derived from the skill source path

This keeps the implementation deterministic and low-risk while improving relevance for natural-language queries.

### 2. Skill-aware `resolve_workflow`

`DiscoveryService.resolve_workflow()` now includes ranked `source="skill"` matches alongside:

- `source="runtime"`
- `source="template"`

This preserves the existing workflow/template behavior while making workflow resolution useful for objective-style skill discovery.

### 3. Tenant-aware workflow resolution

The workflow-resolution path now carries tenant context through:

- FastAPI discovery routes
- MCP `resolve_workflow`

That ensures pack-provided skills only appear for tenants that actually have the pack enabled, while admin callers still bypass tenant filtering.

## Why This Scope

This slice intentionally avoided larger redesigns such as:

- embedding-based semantic indexing
- persistent activation-set storage
- frontend activation-state UX
- Phase 47 imported capability-pack work

Those are valid follow-ons, but they were not required to close the highest-value Phase 46 mismatch on `main`.

## Validation

- `PYTHONPATH=D:\GITHUB\AGENT33\worktrees\session71-s1-phase46-closeout\engine\src python -m pytest engine/tests/test_discovery_service.py engine/tests/test_discovery_routes.py engine/tests/test_mcp_server.py -q --no-cov`
- `python -m ruff format engine/src/agent33/discovery/service.py engine/src/agent33/api/routes/discovery.py engine/src/agent33/mcp_server/tools.py engine/src/agent33/mcp_server/server.py engine/tests/test_discovery_service.py engine/tests/test_discovery_routes.py engine/tests/test_mcp_server.py`
- `python -m ruff check engine/src/agent33/discovery/service.py engine/src/agent33/api/routes/discovery.py engine/src/agent33/mcp_server/tools.py engine/src/agent33/mcp_server/server.py engine/tests/test_discovery_service.py engine/tests/test_discovery_routes.py engine/tests/test_mcp_server.py`
- `PYTHONPATH=D:\GITHUB\AGENT33\worktrees\session71-s1-phase46-closeout\engine\src python -m mypy engine/src/agent33/discovery/service.py engine/src/agent33/api/routes/discovery.py engine/src/agent33/mcp_server/tools.py engine/src/agent33/mcp_server/server.py --config-file engine/pyproject.toml`

## Remaining Phase 46 Follow-ons

If a later slice wants to push Phase 46 further, the next candidates are:

- activation-state visibility in operator UI
- richer source metadata for discovery results
- optional semantic/embedding ranking if lexical ranking proves insufficient
- doc refresh to mark Phase 46 as effectively in-progress/near-closeout rather than untouched
