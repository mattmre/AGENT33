# Session 70 Remaining Roadmap Execution Plan

**Date:** 2026-03-12  
**Scope:** Remaining roadmap execution after the merged PR remediation wave (`#174`-`#176`)  
**Status:** Research / execution planning

## 1. Current Baseline

- There are no open PRs in GitHub right now.
- The recent merged baseline already includes:
  - PR `#162` — Phase 33 marketplace integration
  - PR `#165` — Phase 35 voice runtime control plane
  - PR `#172` — Phase 46 discovery primitives
  - PR `#173` — Phase 46 session activation / dynamic visibility
  - PR `#174`-`#176` — post-merge remediation follow-up stack
- The repo root checkout is dirty and behind `origin/main`; future implementation should continue from fresh worktrees only.

## 2. Reality Check by Priority Area

## 2.1 Phase 46 is partially complete, not untouched

The current handoff documents still list Phase 46 as a top pending item, but recent merged PRs changed the actual baseline:

- PR `#172` delivered:
  - `DiscoveryService`
  - `/v1/discovery/*` routes
  - MCP `discover_tools`, `discover_skills`, and `resolve_workflow`
- PR `#173` delivered:
  - session-scoped tool activation
  - dynamic tool visibility
  - runtime/MCP session propagation

That means the next Phase 46 slice should be a **closeout audit** focused on what remains from the roadmap:

- ranking quality and fuzzy/semantic resolution gaps
- pack/workflow-sourced skill reach
- frontend/operator visibility of activation state
- docs/status reconciliation so the roadmap reflects what is already on `main`

## 2.2 OpenClaw Track 3 is still largely open

The plugin surface can be discovered and toggled, but the research still describes missing operator lifecycle capabilities:

- install/update/link flows
- persisted config store
- doctor diagnostics
- permission visibility
- lifecycle events and auditability

This remains a valid next implementation target.

## 2.3 OpenClaw Track 4 should extend existing pack work, not restart it

Phase 33 already delivered:

- local marketplace catalog
- marketplace-backed install paths
- provenance signing and trust evaluation primitives

The remaining Track 4 delta is the higher-level operator platform:

- remote marketplace/index sources
- trust-policy visibility and management surfaces
- rollback and preserved enablement behavior
- tenant enablement matrix and conflict inspection UX

## 2.4 OpenClaw Track 5 is still greenfield enough to justify split PRs

Research and code search still show two clear missing surfaces:

- a first-class runtime `apply_patch` tool
- an operator-visible process manager for background command sessions

These should be split into:

1. Track 5A: `apply_patch` contract, containment, governance, preview, audit
2. Track 5B: process manager service, routes, logs, and UI

That keeps the diff size and test surface manageable.

## 2.5 OpenClaw Track 6 is still only partially covered by Phase 31 work

Current backup capability is limited to improvement learning state. Track 6 still needs:

- a versioned platform backup manifest
- create/verify flows for broader runtime state
- restore planning / preview before execution
- destructive-flow guidance that points operators to backup posture first

This is another case where two PRs are safer than one:

1. Track 6A: manifest + create/verify
2. Track 6B: restore planning + operator guidance

## 2.6 Phase 25 is a hardening wave, not a first implementation

The SSE fallback already exists and is validated. The remaining work is refinement:

- reconnect/backoff on dropped streams
- `Last-Event-ID` replay support
- optional server-side close on terminal events

The later architecture note recommends deferring a WebSocket-first fallback retry path unless product requirements change, because the current SSE-only path already supports both JWT and API-key auth cleanly.

## 2.7 Phase 38 Stage 3 is also a hardening wave

Docker-backed kernels already exist in the execution layer. The remaining work is:

- direct tests for `DockerKernelSession`
- container-level resource limits from `SandboxConfig`
- startup health verification
- additional container hardening flags and metadata

This should be treated as execution-layer hardening rather than a new subsystem.

## 2.8 Phase 35 must be sequenced carefully against Phase 48

Phase 35 intentionally left the `livekit` transport as an explicit dependency gap.

Phase 48, however, is designed to replace the current voice scaffold with a standalone sidecar and treat the existing daemon as a compatibility shim. That creates a planning risk:

- a large direct `livekit` implementation in the current scaffold could be partially invalidated by the later sidecar work

Recommended posture:

- keep Phase 35 to the minimum work needed for transport compatibility or dependency proofing
- avoid large architectural investment in the soon-to-be-retired scaffold
- treat Phase 48 as the real long-term operator voice target

## 3. Recommended Sequential Execution Order

1. Phase 46 closeout audit and finish
2. OpenClaw Track 3: plugin lifecycle platform
3. OpenClaw Track 4: pack distribution deltas
4. OpenClaw Track 5A: `apply_patch` runtime foundation
5. OpenClaw Track 5B: process manager
6. OpenClaw Track 6A: backup manifest/create/verify
7. OpenClaw Track 6B: restore planning / preview
8. Phase 25 SSE hardening plus targeted frontend test expansion
9. Phase 38 Stage 3 Docker kernel hardening
10. Phase 30 Stage 3 production trace tuning
11. Phase 47 capability pack expansion and workflow weaving
12. Phase 35 / 48 voice convergence decision and minimal compatibility slice
13. Phase 48 sidecar, status line, and production hardening
14. OpenClaw Track 7: web research and trust
15. OpenClaw Track 8: sessions and context engine UX
16. OpenClaw Track 9: operations, config, and doctor
17. OpenClaw Track 10: provenance, FE hardening, and closeout

## 4. PR and Merge Discipline

Each slice should follow the same operating pattern:

1. Create a fresh worktree from updated `origin/main`.
2. Re-read the current planning files and relevant research docs.
3. Confirm the delta between the roadmap and the already-merged baseline.
4. Implement one slice only.
5. Run targeted tests plus repo quality gates for touched areas.
6. Open one PR for that slice.
7. Watch CI, merge, and verify from a fresh baseline before starting the next slice.

## 5. Verification Defaults

For backend-heavy slices:

- targeted `pytest`
- `ruff check`
- `ruff format --check`
- `mypy`

For frontend-touching slices:

- targeted `npm test`
- `npm run lint`
- `npm run build` when the change affects routing or packaging

For merge-wave checkpoints:

- create a fresh verification worktree from the merged `origin/main`
- rerun the targeted regression set that spans all slices in the wave

## 6. Context-Retention Protocol

Because this remaining backlog spans many slices, context retention should stay explicit:

- `task_plan.md` tracks slice order and current status
- `findings.md` records what is already implemented versus still missing
- `progress.md` records commands, verification, and merge outcomes
- each meaningful architecture adjustment gets a research note under `docs/research/`

Treat each fresh worktree as the practical "fresh agent" boundary for this environment:

- one slice per worktree
- no long-lived mixed-purpose implementation branches
- dispose of the worktree after merge and verification
