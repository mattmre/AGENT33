# Session 111 PR Manager Queue Plan

Date: 2026-03-26

## Goal

Execute the Session 111 follow-up wave sequentially from fresh `origin/main` baselines, with one PR per slice and enough on-disk planning detail to resume safely after interruption.

## Queue History

### Initial Session 111 queue

At the start of Session 111, the recommended execution order was:

1. `B1` — ArtifactFilter closure bug
2. `B2A` — `run_stream()` parity: retry, budget enforcement, consecutive-error reset
3. `B2B` — `run_stream()` parity: handoff interceptor, double-confirmation, observation recording
4. `R1` — OpenClaw Track 7: web research and trust
5. `R2` — OpenClaw Track 8: sessions and context UX
6. `R3` — OpenClaw Track 9: operations, config, and doctor
7. `R4` — OpenClaw Track 10: provenance, FE hardening, and closeout
8. `R5` — Phase 31 residuals: analytics and signal tuning
9. `R6` — Phase 32 residuals: middleware operational hardening
10. `R7` — Phase 35: voice sidecar finalization

### Current state after PRs #300 and #301

- `B1` is complete on `main` via PR `#300` / commit `970f1fa`
- `B2A` is complete on `main` via PR `#301` / commit `33406e5`
- The next implementation slice is `B2B`

## Current Baseline

- Branch: `main`
- Latest merged commit on `main`: `33406e5` (`fix(agents): add run_stream retry and budget parity`)
- Active queue sources:
  - `docs/next-session.md`
  - `docs/research/session110-task-plan.md`
  - `docs/sessions/session-111-2026-03-26.md`

## Remaining Execution Order

1. `B2B` — `run_stream()` parity: handoff interceptor, double-confirmation, observation recording
2. `R1` — OpenClaw Track 7: web research and trust
3. `R2` — OpenClaw Track 8: sessions and context UX
4. `R3` — OpenClaw Track 9: operations, config, and doctor
5. `R4` — OpenClaw Track 10: provenance, FE hardening, and closeout
6. `R5` — Phase 31 residuals: analytics and signal tuning
7. `R6` — Phase 32 residuals: middleware operational hardening
8. `R7` — Phase 35: voice sidecar finalization

## Rationale

### Why B1 and B2A came first

- `B1` was a confirmed correctness defect on `main` with small, isolated scope.
- `B2A` addressed the lowest-risk streaming parity subset first:
  - retry behavior for transient LLM-call failures
  - end-of-iteration budget enforcement
  - consecutive-error reset after successful tool-call iterations
- The final `completed` event payload fallback for `max_iterations` termination was also fixed before merging `#301`.

### Why B2B remains separate

- The remaining parity work mutates streamed conversation state and emitted behavior:
  - handoff interception / context wipe parity
  - double-confirmation parity
  - observation recording parity
- Keeping that work in its own PR preserves a clean regression boundary after the B2A merge.

### Why the remaining roadmap stays in documented order

- After the streaming bugfixes, the rest of the queue should continue in the order already published in `docs/next-session.md`.
- That keeps the repo handoff, planning docs, and PR sequence aligned.

## B2B Scope Lock

### Included work

- Bring `run_stream()` into parity with `run()` for:
  - handoff interceptor behavior
  - double-confirmation flow
  - observation recording
- Add targeted streaming regression coverage for each parity surface touched

### Non-goals

- No broader tool-loop refactor beyond the remaining parity gaps
- No OpenClaw or late-phase roadmap work in the same PR
- No changes to the already-merged B2A retry / budget / error-reset contract unless a regression is found

## Validation Plan

Run, at minimum, from the B2B worktree:

- targeted pytest for streaming and non-streaming tool-loop parity coverage
- `ruff check` on touched engine source/tests
- `ruff format --check` on touched engine source/tests
- `mypy` on touched engine runtime modules
