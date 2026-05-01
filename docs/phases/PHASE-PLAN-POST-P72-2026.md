# POST-P72 Phase Plan (2026)

**Status**: Approved in Session 122, restored in Session 124, synced to merged baseline through `#447` on 2026-04-27, with the tracked post-merge follow-up and Operator UX expansion waves closed after CI verification
**Scope**: POST-1 through POST-4 plus post-cluster distribution work

## Purpose

This file is the canonical roadmap for the post-P72 wave. It captures what is already merged on `main`, what remains queued, and which slices should resume next from fresh `origin/main` worktrees.

## Current Status Snapshot

| Cluster | Status | Notes |
| --- | --- | --- |
| POST-1 — Foundation & Baseline | Complete | PRs `#384`-`#387` |
| POST-2 — SkillsBench Competitiveness | Complete | PRs `#388`-`#392` |
| POST-3 — Pack Ecosystem | Complete | PRs `#394`, `#395`, `#397`, `#398` (`#393` / `#396` were docs reconciliation and wrap) |
| POST-4 — Interruption & Self-Improvement | Complete | `POST-4.1`-`POST-4.5` complete in PRs `#399`-`#406` |
| POST-CLUSTER — Distribution & Ecosystem Growth | Complete | Public launch preparation, P-ENV v2, remediation, marketplace/community submissions, tracked follow-up work, Operator UX expansion, Agent OS, MCP operator actions, and research launchers are merged through `#447`; no queued slices remain in this plan |

## Current Execution Queue

| Order | Slice | Status | Notes |
| --- | --- | --- | --- |
| 1 | Post-merge review remediation (`#406`-`#412`) | Complete | Lifecycle cleanup, P-ENV/docs reliability, P-PACK hardening, and operator/docs queue sync are merged on `main` |
| 2 | POST-CLUSTER — Marketplace + community submissions (`#413`-`#414`) | Complete | UI browse/install flow plus community submission/resubmission are merged and no longer the active queue |
| 3 | Sessions 131-132 merge wave (`#415`-`#427`) | Complete | P68-Lite monitoring, P69b persistence, SSE v2 migration prep, security scan hardening, ingestion sprints 0-5, research preservation, OpenRouter integration, and mailbox persistence are merged on `main` |
| 4 | Ingestion hardening follow-up (`#429`) | Complete | Journal retention/expiry plus persistent task metrics are merged on `main` |
| 5 | Operator UX depth (`#430`) | Complete | Review-history UI and notification hooks are merged on `main` |
| 6 | SSE schema v2 backend foundation (`#431`) | Complete | Version gating, kill switch, and pinned schema scaffolding are merged on `main` |
| 7 | Skills-system integration (`#432`) | Complete | Published ingestion skills register into the shared runtime registry on promote/hydration |
| 8 | SkillsBench smoke regression reporting (`#433`) | Complete | CTRF comparison/reporting is merged into CI and benchmark workflows |
| 9 | Operator UX rescue foundation (`#435`-`#440`) | Complete | Start Here, Review Queue, Safety Center, Skill Wizard, Workflow Starter, and Tool Fabric are merged on `main` |
| 10 | Agent OS / improvement / MCP foundation (`#441`-`#444`) | Complete | Agent OS runtime, Improvement Loops, MCP Health Center, and grouped navigation are merged on `main` |
| 11 | Operator actions and recurring research (`#445`-`#447`) | Complete | MCP sync/validate/reload actions, named Agent OS sessions, and one-click scheduled research launchers are merged on `main` |
| 12 | Final wrap-up verification | Complete | CI verification confirms the sequential roadmap and Operator UX expansion waves landed cleanly on `main` |

## Post-Wave Posture

- ingestion hardening follow-up is complete in `#429`
- deeper operator UX work is complete in `#430`
- SSE schema v2 backend foundation is complete in `#431`
- skills-system integration is complete in `#432`
- SkillsBench smoke regression reporting is complete in `#433`
- Operator UX rescue surfaces are complete in `#435`-`#440`
- Agent OS, Improvement Loops, MCP Health, and navigation foundations are complete in `#441`-`#444`
- MCP operator actions, Agent OS sessions, and scheduled research launchers are complete in `#445`-`#447`
- no remaining queued slices exist in this tracked post-merge / Operator UX expansion wave; any new work should begin from a fresh planning refresh

## Cluster Plans

### POST-1 — Foundation & Baseline (Complete)

- POST-1.1 — ARCH-AEP Loop 7 review + triage
- POST-1.2 — Planning/docs refresh
- POST-1.3 — Frontend bundling decision
- POST-1.4 — SHA-256 timing oracle fix using `hmac.compare_digest()`
- POST-1.5 — SkillsBench baseline CLI/reporting
- Exit gate: Loop 7 remediations merged; planning docs current; SkillsBench baseline committed to `benchmarks`
- Delivered by PRs `#384`-`#387`

### POST-2 — SkillsBench Competitiveness (Complete)

- POST-2.1a — SkillsBench smoke suite CI (every PR, mocked LLM, <=15 tasks)
- POST-2.1b — SkillsBench full run (weekly, live LLM, `benchmarks` branch)
- POST-2.2 — Context window management for evaluation harness
- POST-2.3 — Iterative tool-use loop + 4-stage skill matching
- ARCH-AEP Loop 8 review + remediations
- Exit gate: code complete; confirm first weekly benchmark data against baseline
- Delivered by PRs `#388`-`#392`

### POST-3 — Pack Ecosystem (Complete)

- POST-3.1 — Pack sandbox + injection tests (PR `#394`)
- POST-3.2 — Pack registry v1 revocation + Sigstore verification (PR `#395`)
- POST-3.3 — CLI DX improvements (`--json`, `--plain`, pack-aware `diagnose`) (PR `#397`)
- POST-3.4 — 5 seed packs (PR `#398`)
- Exit gate: live registry support, installable seed packs, and pack-signing enforcement landed on `main`

### POST-4 — Interruption & Self-Improvement (Complete)

- POST-4.1 — P69b UX spec + API contract document (**complete** in PR `#399`)
- POST-4.2 — SSE event schema versioning, strict rejection model (**complete** in PR `#400`)
- POST-4.3 — P69b implementation (**complete** in PR `#401`)
- POST-4.4 — P-PACK v3 A/B harness (**complete** in PR `#405`)
- POST-4.5 — P-PACK v3 behavior modifications (**complete** in PR `#406`)
- Completion criteria: P69b end-to-end tested; P-PACK v3 behavioral A/B tests passing; both behind feature flags

### POST-CLUSTER — Distribution & Ecosystem Growth (Active)

- Public launch preparation (README as product page, onboarding/getting-started/release-checklist docs) (**complete** in PR `#407`)
- P-ENV v2 auto-install + automated model download (**complete** in PR `#408`)
- Lifecycle cleanup follow-up (**complete** in PR `#409`)
- P-ENV/docs reliability follow-up (**complete** in PR `#410`)
- P-PACK review-debt hardening (**complete** in PR `#411`)
- Remaining operator/docs remediation (**complete** in PR `#412`)
- Pack marketplace web UI (**complete** in PR `#413`)
- Community submissions (**complete** in PR `#414`)
- P68-Lite outcomes monitoring verification (**complete** in PR `#415`)
- P69b persistence hardening (**complete** in PR `#416`)
- SSE schema-v2 migration contract (**complete** in PR `#417`)
- Security scan/admin-override remediation (**complete** in PR `#418`)
- Evolver ingestion sprints 0-5 (**complete** in PRs `#419`-`#424`)
- Research corpus preservation (**complete** in PR `#425`)
- OpenRouter runtime/config/operator/frontend integration (**complete** in PR `#426`)
- Persisted ingestion mailbox inbox events (**complete** in PR `#427`)
- Handoff/queue refresh after the Sessions 130-132 merge wave (**complete** in PR `#428`)
- Ingestion hardening follow-up: journal retention/expiry plus persistent task metrics durability/query support (**complete** in PR `#429`)
- Operator ingestion UX depth: review history/details and notification hooks (**complete** in PR `#430`)
- SSE schema v2 backend foundation (**complete** in PR `#431`)
- Published-ingestion skills runtime registration (**complete** in PR `#432`)
- SkillsBench smoke regression reporting in CLI/CI (**complete** in PR `#433`)
- Tracked queue status: complete through `#433`; open a new roadmap slice before additional implementation

## Dependency Graph

```text
POST-3.1 — Pack sandbox + injection tests
  └──→ POST-3.2 — Pack registry v1
        ├──→ POST-3.3 — CLI DX improvements
        └──→ POST-3.4 — 5 seed packs
              └──→ POST-4.1 — P69b UX spec + API contract
                    └──→ POST-4.2 — SSE event schema versioning
                          └──→ POST-4.3 — P69b implementation
                                └──→ POST-4.4 — P-PACK v3 A/B harness
                                      └──→ POST-4.5 — P-PACK v3 behavior modifications
                                            └──→ POST-CLUSTER work
```

## Locked Architectural Decisions (Session 122)

These decisions are final and must not be reopened without explicit user approval:

1. **SkillsBench framing**: Two-tier — smoke (every PR, mocked, <=15 tasks) + full (weekly, live, `benchmarks` branch)
2. **P69b pause state**: `PausedInvocation` state record in the state machine — not a mutable in-memory flag
3. **Pack registry v1**: GitHub JSON index — no custom hosted API
4. **Pack signing**: Sigstore cosign (keyless) — SHA-256 remains integrity only
5. **Pack sandbox**: Reuse `CLIAdapter` subprocess isolation — injection scanner is the correct defense layer
6. **P-PACK v3 rollout policy**: no calendar/data gate; implement the purpose-built A/B harness now, then use it for validation and monitoring
7. **Headless P69b**: `AGENT33_HEADLESS_TOOL_APPROVAL=approve|deny`, default `deny`
8. **SHA-256 timing oracle**: Replace direct digest comparisons with `hmac.compare_digest()`
9. **P69b replay protection**: HMAC nonce = `HMAC-SHA256(run_id + tool_name + floor(timestamp/30), tenant_secret)`
10. **SSE version enforcement**: Strict rejection — v1 clients reject v2 streams entirely
11. **A/B harness statistics**: 95% confidence, n>=30, -5% threshold, Bonferroni correction
12. **Benchmark results**: `benchmarks` branch (not `main`) — bot commits, signed
13. **Feature flag lifecycle**: Every flag ships with lifecycle metadata and a file-based kill switch
14. **Pack revocation**: Registry JSON includes `revoked`; install checks revocation
15. **P68-Lite monitoring**: Alert if outcomes table stays empty for >24h during rollout
16. **SkillsBench regression alert**: Auto-open a GitHub issue if a weekly run shows >5% drop
17. *(reserved)*
18. *(reserved)*
19. **SSE v2 migration contract**: See `docs/research/sse-schema-v2-migration-path.md` — v2 is not started until that document is published and reviewed.

## Execution Rules

1. Use one fresh worktree per slice from updated `origin/main`.
2. Use one fresh research pass per slice and dispose of it after merge.
3. Open one PR per slice.
4. Do not start a later slice before the current one is merged and verified from fresh `origin/main`.
5. If research changes roadmap assumptions, write a memo under `docs/research/` before implementation.
6. Always refresh `docs/next-session.md`, this file, `task_plan.md`, `progress.md`, and any active queue docs after major milestones.
