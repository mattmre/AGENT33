# Session 84 S11 Scope Lock: Phase 47 Capability Pack Expansion

Date: 2026-03-14
Slice: `S11 / Phase 47`
Worktree: `worktrees/session84-s11-phase47`
Branch: `codex/session84-s11-phase47`

## Baseline Audit

- The runtime already supports:
  - `SKILL.md` YAML frontmatter parsing in `engine/src/agent33/skills/loader.py`
  - pack manifests, install/enable/upgrade/rollback, and pack marketplace APIs in `engine/src/agent33/packs/`
  - skill-aware workflow discovery in `engine/src/agent33/discovery/service.py`
  - explicit `active_skills` injection in agent routes and `AgentRuntime`
- The repo does not yet ship actual imported capability packs:
  - there are no real `PACK.yaml` or `SKILL.md` assets checked into the runtime content paths
  - `core/workflows/skills/` still contains only legacy markdown guidance, not importable packaged skills
- Workflow weaving has a real bridge gap:
  - the workflow `invoke_agent` bridge in `engine/src/agent33/main.py` creates `AgentRuntime`
    instances without passing `active_skills`
  - this means workflow templates cannot actually activate imported pack skills end to end today

## Scope Decision

This slice will implement the smallest complete Phase 47 increment that turns the current
runtime scaffolding into real shipped capability packs without inventing a second distribution
model.

## Included Work

1. Extend skill discovery to support hierarchical category layouts and recursive scanning.
2. Add imported capability packs under the existing local marketplace path:
   - `hive-family`
   - `workflow-ops`
   - `platform-builder`
3. Import the following high-value skills from the local Codex skill library into those packs:
   - `hive`
   - `hive-concepts`
   - `hive-create`
   - `hive-patterns`
   - `hive-test`
   - `planning-with-files`
   - `docs-architect`
   - `pr-manager`
   - `webapp-testing`
   - `mcp-builder`
   - `repo-ingestor`
4. Add pack/skill metadata needed to make the imported library manageable in API responses:
   - skill category
   - skill provenance label
5. Add workflow templates in `core/workflows/` that explicitly declare and pass the imported
   skills through the workflow agent bridge.
6. Update the workflow agent bridge so `invoke_agent` steps can pass `active_skills` to
   `AgentRuntime`.
7. Add targeted tests for:
   - recursive skill discovery
   - imported marketplace pack visibility and metadata
   - workflow bridge propagation of `active_skills`

## Explicit Non-Goals

- No broad Phase 48 voice or operator UX work.
- No new remote marketplace source format.
- No frontend pack browser overhaul in this slice.
- No attempt to import the entire external skill library; only the Phase 47 high-value set.
- No new standalone workflow engine concept for skills; the existing pack + agent runtime model
  remains the only shipped path.

## Validation Plan

- `python -m pytest` on touched pack/skills/workflow tests
- `python -m ruff check` on touched engine files and tests
- `python -m ruff format --check` on touched engine files and tests
- `python -m mypy` on touched engine modules

## Merge Intent

- One PR for `S11` only.
- No later slice starts until the imported-pack PR is green, reviewed, merged, and verified from
  fresh `origin/main`.
