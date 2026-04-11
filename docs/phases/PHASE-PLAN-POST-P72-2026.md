# POST-P72 Phase Plan (2026)

**Status**: Approved in Session 122, restored to `main` in Session 124  
**Scope**: POST-1 through POST-4 plus post-cluster distribution work

## Purpose

This plan captures the post-P72 roadmap after UX clusters A-D landed on `main`. The work focuses on benchmark competitiveness, pack distribution/security, interruption/self-improvement, and the final distribution wave. It is the canonical roadmap file referenced by the Fresh Context Protocol.

## Current Status Snapshot

| Cluster | Status | Notes |
| --- | --- | --- |
| POST-1 — Foundation & Baseline | Complete | PRs #384-#387 |
| POST-2 — SkillsBench Competitiveness | Complete | PRs #388-#392 |
| POST-3 — Pack Ecosystem | In progress | POST-3.1 and POST-3.2 are complete; POST-3.3 is next |
| POST-4 — Interruption & Self-Improvement | Not started | Depends on POST-3; P-PACK v3 also depends on 30-day P68-Lite gate |
| POST-CLUSTER — Distribution & Ecosystem Growth | Not started | Follows POST-4 and registry maturity |

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

### POST-3 — Pack Ecosystem (Active Cluster)

- POST-3.1 — Pack sandbox + injection test suite (complete in PR `#394`)
- POST-3.2 — Pack registry v1 (complete in PR `#395`)
- POST-3.3 — CLI DX improvements (`--json`, `--plain`, pack-aware `diagnose`)
- POST-3.4 — 5 seed packs (web-research, code-review, meeting-notes, document-summarizer, developer-assistant)
- Exit gate: `agent33 pack search` works against the live registry; 5 seed packs installable; pack signing enforced

### POST-4 — Interruption & Self-Improvement

- POST-4.1 — P69b UX spec + API contract document
- POST-4.2 — SSE event schema versioning (strict rejection model)
- POST-4.3 — P69b implementation (`PausedInvocation`, HMAC nonce, feature flag)
- POST-4.4 — P-PACK v3 A/B harness (30-day calendar gate + statistical significance)
- POST-4.5 — P-PACK v3 behavior modifications (feature flag, A/B regression gate)
- Exit gate: P69b end-to-end tested; P-PACK v3 behavioral A/B tests passing; both behind feature flags

### POST-CLUSTER — Distribution & Ecosystem Growth

- Public launch preparation (README as product page)
- P-ENV v2 auto-install + automated model download
- Pack marketplace web UI
- Community submissions (only after pack signing + approval queue proven)

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
                                      [calendar gate: 30 days P68-Lite data]
                                      └──→ POST-4.5 — P-PACK v3 behavior modifications
```

## Locked Architectural Decisions (Session 122)

These decisions are final and must not be reopened without explicit user approval:

1. **SkillsBench framing**: Two-tier — smoke (every PR, mocked, <=15 tasks) + full (weekly, live, `benchmarks` branch)
2. **P69b pause state**: `PausedInvocation` state record in the state machine — not a mutable in-memory flag
3. **Pack registry v1**: GitHub JSON index — no custom hosted API
4. **Pack signing**: Sigstore cosign (keyless) — SHA-256 remains integrity only
5. **Pack sandbox**: Reuse `CLIAdapter` subprocess isolation — injection scanner is the correct defense layer
6. **P-PACK v3 gate**: 30-day calendar gate and a purpose-built A/B harness with statistical significance
7. **Headless P69b**: `AGENT33_HEADLESS_TOOL_APPROVAL=approve|deny`, default `deny`
8. **SHA-256 timing oracle**: Replace direct digest comparisons with `hmac.compare_digest()`
9. **P69b replay protection**: HMAC nonce = `HMAC-SHA256(run_id + tool_name + floor(timestamp/30), tenant_secret)`
10. **SSE version enforcement**: Strict rejection — v1 clients reject v2 streams entirely
11. **A/B harness statistics**: 95% confidence, n>=30, -5% threshold, Bonferroni correction
12. **Benchmark results**: `benchmarks` branch (not `main`) — bot commits, signed
13. **Feature flag lifecycle**: Every flag ships with lifecycle metadata and a file-based kill switch
14. **Pack revocation**: Registry JSON includes `revoked`; install checks revocation
15. **P68-Lite monitoring**: Alert if outcomes table stays empty for >24h during the gate
16. **SkillsBench regression alert**: Auto-open a GitHub issue if a weekly run shows >5% drop

## Execution Rules

1. Use one fresh worktree per slice from updated `origin/main`.
2. Use one fresh agent/research pass per slice and dispose of it after merge.
3. Open one PR per slice.
4. Do not start a later slice before the current one is merged and verified from fresh `origin/main`.
5. If research changes roadmap assumptions, write a memo under `docs/research/` before implementation.
6. Always update `docs/next-session.md`, `task_plan.md`, `progress.md`, and `findings.md` after major milestones so recovery does not depend on chat history.
