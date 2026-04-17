# Session 126 — Master Task Plan (POST-P72 Execution)

**Created**: 2026-04-11
**Owner**: Session 126
**Scope**: POST-3.3 fix → POST-3.4 → POST-4.1 through POST-4.5

---

## Current State (synced 2026-04-17)

- All Phases P01-P72: COMPLETE (404 PRs merged)
- POST-1 (Foundation & Baseline): COMPLETE
- POST-2 (SkillsBench Competitiveness): COMPLETE
- POST-3.1 (Pack sandbox + injection tests): COMPLETE
- POST-3.2 (Pack registry v1): COMPLETE
- POST-3.3 (CLI DX improvements): COMPLETE — PR `#397`
- POST-3.4 (5 seed packs): COMPLETE — PR `#398`
- POST-4.1 (P69b UX spec + API contract): COMPLETE — PR `#399`
- POST-4.2 (SSE event schema versioning): COMPLETE — PR `#400`
- POST-4.3 (P69b implementation): COMPLETE — PR `#401`
- POST-4.4: COMPLETE — merged as PR `#405`
- POST-4.5: COMPLETE — merged as PR `#406`
- POST-CLUSTER (public launch preparation): ACTIVE — Session 127 worktree `session127-s8-public-launch`
- Session wrap/docs sync: COMPLETE — PR `#402`

## Session 126 Execution Queue

| # | Task | Cluster | Branch/PR | Depends On | Status |
|---|------|---------|-----------|-----------|--------|
| S0 | Fix PR #397 CI + merge | POST-3.3 | #397 | — | ✅ MERGED `b09873b` |
| S1 | POST-3.4 — 5 seed packs | POST-3 | #398 | #397 merged | ✅ MERGED `4195694` |
| S2 | POST-4.1 — P69b UX spec + API contract | POST-4 | #399 | S1 merged | ✅ MERGED `fca50ab` |
| S3 | POST-4.2 — SSE event schema versioning | POST-4 | #400 | S2 merged | ✅ MERGED `899e7b4` |
| S4 | POST-4.3 — P69b implementation | POST-4 | #401 | S3 merged | ✅ MERGED `fd092f3` |
| S5 | POST-4.4 — P-PACK v3 A/B harness | POST-4 | `session127-s5-ab-harness` | S4 merged | ✅ MERGED `b591454` |
| S6 | POST-4.5 — P-PACK v3 behavior mods | POST-4 | `session127-s6-post45` | S5 merged | ✅ MERGED `f7ad606` |
| S7 | POST-CLUSTER — Public launch preparation | POST-CLUSTER | `session127-s8-public-launch` | S6 merged | ACTIVE |
| SX | Docs refresh + session wrap | docs | #402 | all | ✅ COMPLETE |

---

## Resume Protocol

If execution stops mid-slice:
1. Read this file (`docs/sessions/session126-task-plan.md`)
2. Read `task_plan.md` (root), `findings.md`, `progress.md`
3. Check the "Status" column above
4. Inspect the referenced branch (`git status`) in its worktree
5. Determine phase (research/scope_lock/implementation/validation/pr_open/ci_wait/merged/verified)
6. Continue from first incomplete step

---

## S0 — Fix PR #397 and Merge

**Branch**: `codex/session125-post33-cli-dx`
**PR**: mattmre/AGENT33#397

### CI Failures Found and Fixed

| Fix | Root Cause | Commit |
|-----|-----------|--------|
| `test_diagnose_cli_rejects_conflicting_output_flags` | `typer.BadParameter` wraps message in ANSI box → not verbatim in `result.output` | `47c40e4` |
| 6 ruff errors in `test_pack_registry_v1.py` | I001×2, TC003, F401, N817, E501 | `47c40e4` |
| mypy 1.20 `unused-ignore` in `provenance.py:200-201` | Error code changed from `import-untyped` → `import-not-found` | `375829a` |

### Merge Procedure (once CI green)
```bash
gh api -X PUT repos/mattmre/AGENT33/pulls/397/merge -f merge_method=squash
```
(Use API to avoid worktree branch collision with local `main`)

### Post-merge: create fresh verification worktree
```bash
git fetch origin main
git worktree add ../worktrees/session126-s0-postmerge-verify origin/main
cd ../worktrees/session126-s0-postmerge-verify/engine
PYTHONPATH=../worktrees/session126-s0-postmerge-verify/engine/src python -m pytest tests/test_diagnose.py tests/test_ppack_v1.py tests/test_ppack_v2.py tests/test_pack_registry_v1.py -q --no-cov
```

---

## S1 — POST-3.4: 5 Seed Packs

**Goal**: Ship 5 installable packs for the pack ecosystem.

**Packs to create**:
1. `web-research` — web search + summarize workflows
2. `code-review` — automated code review skill chains
3. `meeting-notes` — transcript extraction + action item generation
4. `document-summarizer` — multi-document summarization
5. `developer-assistant` — dev workflow automation (git, lint, test helpers)

**Pack structure** (each pack needs):
```
engine/packs/{pack-name}/
  PACK.yaml          # metadata, version, skills list, prompt_addenda, tool_config
  skills/
    {skill-name}.md  # skill definitions with frontmatter
  README.md          # human-readable description
```

**Architectural constraints (locked)**:
- Pack sandbox: Reuse CLIAdapter subprocess isolation
- Pack signing: Sigstore cosign (keyless) — SHA-256 is integrity only
- Pack revocation: Registry JSON includes `revoked` field; install checks it
- Pack registry v1: GitHub JSON index (no custom hosted API)

**Exit gate**:
- All 5 packs validate via `agent33 packs validate <path>` (local dry-run)
- Tests: `pytest tests/test_seed_packs.py -q --no-cov`
- ruff + mypy clean on any new Python code

**Worktree**: `worktrees/session126-s1-seed-packs` from fresh `origin/main`
**Branch**: `session126-s1-seed-packs`

**Agent instructions** (when spawning):
> Read `docs/research/session125-post33-cli-dx-scope.md` for context on pack structure.
> Read `engine/src/agent33/packs/` for the hub/registry models.
> Read `engine/packs/workflow-ops/` as an example existing pack.
> Create 5 seed packs under `engine/packs/` with PACK.yaml, skills/, README.md.
> Write `engine/tests/test_seed_packs.py` with validation tests for each pack.
> Run `python -m ruff check` and `python -m mypy src` clean.
> Open a PR titled `feat(packs): POST-3.4 five seed packs`.

---

## S2 — POST-4.1: P69b UX Spec + API Contract

**Goal**: Write formal spec + API contract for P69b (human-in-the-loop tool approval pause/resume).

**Deliverables** (docs-only PR):
- `docs/research/session126-p69b-ux-spec.md`
- `docs/research/session126-p69b-api-contract.md`

**UX spec must cover**:
- Pause trigger conditions (which tool calls require approval)
- User-facing pause state display
- Approval UI flows (approve / deny / timeout)
- Headless mode: `AGENT33_HEADLESS_TOOL_APPROVAL=approve|deny`, default `deny`
- Error states and timeout behavior

**API contract must define**:
- `POST /v1/invocations/{id}/pause` — pause a running invocation for approval
- `POST /v1/invocations/{id}/resume` — resume with `approved: bool`
- `GET /v1/invocations/{id}/pending-approvals` — list tools awaiting approval
- Request/response schemas (JSON)
- State machine: RUNNING → PAUSED_FOR_APPROVAL → RUNNING|FAILED

**Architectural constraints (locked)**:
- Pause state: `PausedInvocation` state record in DB — NOT mutable in-memory flag
- Replay protection: HMAC nonce — `HMAC-SHA256(run_id + tool_name + floor(timestamp/30), tenant_secret)`
- Feature flag: ships with lifecycle metadata + file-based kill switch

**Research required**:
- Read `engine/src/agent33/autonomy/` for existing autonomy budget patterns
- Read `engine/src/agent33/workflows/state_machine.py` for state patterns
- Read existing escalation paths in `core/orchestrator/handoff/ESCALATION_PATHS.md`

**Worktree**: `worktrees/session126-s2-p69b-spec` from fresh `origin/main`
**Branch**: `session126-s2-p69b-spec`

---

## S3 — POST-4.2: SSE Event Schema Versioning

**Goal**: Add strict version enforcement to SSE event stream — v1 clients reject v2 streams.

**Scope**:
- Add `schema_version: int` field to every SSE event model
- Server: emit version in all SSE events
- Client-side transport (`frontend/src/`): check version on first event; if mismatch, close with error
- Strict rejection model: no graceful downgrade

**Architectural constraint (locked)**:
- SSE version enforcement: Strict rejection — v1 clients reject v2 streams entirely

**Research required**:
- Read `engine/src/agent33/workflows/live.py` — SSE event model and live manager
- Read `frontend/src/` SSE transport code
- Read `docs/research/session78-s8-sse-hardening-scope.md` for SSE context

**Tests needed**:
- Version match: stream proceeds normally
- Version mismatch: client closes connection with `schema_version_mismatch` error
- Server emits `schema_version` on all event types

**Worktree**: `worktrees/session126-s3-sse-versioning` from fresh `origin/main`
**Branch**: `session126-s3-sse-versioning`

---

## S4 — POST-4.3: P69b Implementation

**Goal**: Implement the P69b pause/resume feature behind a feature flag.

**Scope**:
- `PausedInvocation` model in `engine/src/agent33/autonomy/models.py`
- Pause trigger in `ToolLoop.run()` / `AgentRuntime.invoke_iterative()` — before executing a tool, check if approval required
- HMAC nonce generation + validation utility
- API routes: `POST /v1/invocations/{id}/pause`, `POST /v1/invocations/{id}/resume`, `GET /v1/invocations/{id}/pending-approvals`
- Headless env var: `AGENT33_HEADLESS_TOOL_APPROVAL` (default `deny`)
- Feature flag: `p69b_tool_approval_enabled` with file-based kill switch at `/tmp/agent33_disable_p69b`

**Architectural constraints (locked)**:
- PausedInvocation is a DB state record — not in-memory
- HMAC nonce formula: `HMAC-SHA256(run_id + tool_name + floor(timestamp/30), tenant_secret)`
- Feature flag ships with lifecycle metadata

**Research required** (agent must read S2's API contract before implementing):
- `docs/research/session126-p69b-ux-spec.md`
- `docs/research/session126-p69b-api-contract.md`
- `engine/src/agent33/autonomy/` for existing autonomy models
- `engine/src/agent33/execution/models.py` for ExecutionContract patterns

**Tests needed**:
- `test_p69b_pause_resume.py`:
  - Pause stores PausedInvocation in DB
  - Resume with `approved=True` continues
  - Resume with `approved=False` fails with `ToolApprovalDenied`
  - HMAC nonce prevents replay
  - Headless `deny` mode auto-denies without DB lookup
  - Feature flag disables all P69b behavior

**Worktree**: `worktrees/session126-s4-p69b-impl` from fresh `origin/main`
**Branch**: `session126-s4-p69b-impl`

---

## S5 — POST-4.4: P-PACK v3 A/B Harness

**Execution policy**: The prior calendar/data gate is removed. Implement immediately and use the harness itself for validation plus post-implementation monitoring.
**P68-Lite monitoring**: Alert if outcomes table empties during rollout.

**Goal**: Purpose-built A/B harness for P-PACK v3 behavioral testing.

**Statistical requirements (locked)**:
- 95% confidence
- n≥30 per variant
- −5% regression threshold
- Bonferroni correction for multiple comparisons

**Scope**:
- A/B assignment logic (deterministic by user/session hash)
- Assignment persistence + outcome collection records in DB
- Statistical test runner (scipy.stats)
- Report generation (JSON + markdown)
- Alert hook: auto-open GitHub issue if weekly run shows >5% drop

**Worktree**: `worktrees/session127-s5-ab-harness` from fresh `origin/main`
**Branch**: `session127-s5-ab-harness`

---

## S6 — POST-4.5: P-PACK v3 Behavior Modifications

**Goal**: Apply P-PACK v3 behavior changes behind a rollout feature flag and validate them with the POST-4.4 harness.

**Execution order**: Starts immediately after the POST-4.4 slice is implemented and validated in sequence.

**Scope**:
- Behavior changes to pack application/selection logic (per P-PACK v3 spec)
- Gated behind `ppack_v3_enabled` feature flag
- CI validation includes `pytest tests/test_ppack_v3_ab.py`

**Worktree**: `worktrees/session127-s6-ab-behavior` from fresh `origin/main`
**Branch**: `session127-s6-ab-behavior`

---

## Slice Execution Protocol (all slices)

Every slice moves through these phases in order:

| Phase | Required Output |
|-------|----------------|
| 1. Research refresh | Read relevant docs; note deltas vs `main` in `findings.md` or new `docs/research/` memo |
| 2. Scope lock | Exact included work, explicit non-goals, dependency check, branch/worktree name |
| 3. Implementation | Code/docs changes only for current slice |
| 4. Validation | Targeted tests + `ruff check` + `mypy src` for touched areas |
| 5. PR prep | PR summary/body; note unresolved risks; open PR |
| 6. CI / review loop | Watch checks; address comments; rerun validation if amended |
| 7. Merge | Only after green CI + final review |
| 8. Post-merge verify | Re-test from fresh `origin/main` worktree |
| 9. Handoff update | Update `task_plan.md`, `findings.md`, `progress.md`, this file |

---

## Agent Orchestration Rules

- **One fresh worktree per slice** from updated `origin/main`
- **One fresh agent per slice** — disposed after merge confirmed
- **One PR per slice** — no batch PRs
- **No next slice before merge + post-merge verification**
- **Research before code** — every agent reads relevant docs first
- **Document research** — findings go to `docs/research/session126-*.md`
- **Session log** — update `progress.md` after each merge

---

## Merge Plan

| Order | PR | Strategy | Blocking Checks |
|-------|----|----------|-----------------|
| 1 | #397 (POST-3.3 CLI DX) | Squash via API | lint + test green |
| 2 | S1 POST-3.4 seed packs | Squash via API | lint + test green |
| 3 | S2 POST-4.1 P69b spec | Squash via API | lint green (docs-only) |
| 4 | S3 POST-4.2 SSE versioning | Squash via API | lint + test green |
| 5 | S4 POST-4.3 P69b impl | Squash via API | lint + test green |
| 6 | S5 POST-4.4 A/B harness | Squash via API | lint + test green |
| 7 | S6 POST-4.5 behavior mods | Squash via API | lint + test + `test_ppack_v3_ab.py` green |

**Merge command** (avoids worktree collision):
```bash
gh api -X PUT repos/mattmre/AGENT33/pulls/{PR_NUM}/merge -f merge_method=squash
```

---

## Key References

- `docs/phases/PHASE-PLAN-POST-P72-2026.md` — Approved POST-P72 phase plan
- `docs/next-session.md` — operator handoff synced to the merged baseline through `#403`
- `docs/research/session125-post33-cli-dx-scope.md` — POST-3.3 scope (context for S1)
- `docs/research/skillsbench-analysis.md` — SkillsBench analysis
- `engine/src/agent33/autonomy/` — Autonomy enforcement (context for S2-S4)
- `engine/src/agent33/workflows/live.py` — SSE streaming (context for S3)
- `engine/packs/workflow-ops/` — Example existing pack (context for S1)
