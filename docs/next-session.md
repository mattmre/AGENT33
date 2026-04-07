# Next Session Briefing

Last updated: 2026-04-07 (Session 123 start)

## Current State

- **Branch posture**: root checkout is intentionally dirty and lags `origin/main`. Always use fresh worktrees.
- **Open PRs**: 0
- **Latest merged PR**: #383 (P72 — Impact Dashboard)
- **Latest commit on main**: `729d68f`
- **Cumulative PRs merged**: 383+
- **All Phases 01-72**: COMPLETE
- **Cluster UX-A (P60a, P-ENV, P63, P60b, P62, P61, P64)**: COMPLETE
- **Cluster UX-B (P65, P66, P67)**: COMPLETE
- **Cluster UX-C (P68-Lite, P69a, P-PACK v1)**: COMPLETE (with Loop 6 remediations)
- **Cluster UX-D (P70, P71, P-PACK v2, P72)**: COMPLETE
- **ARCH-AEP Loops 1-6**: COMPLETE
- **ARCH-AEP Loop 7**: IN PROGRESS (background agent review running; results pending in `docs/research/session121-arch-aep-loop7.md`)
- **Active roadmap**: `docs/phases/PHASE-PLAN-POST-P72-2026.md` (approved Session 122, 6-panel cascade review)
- **CVE scan**: pre-existing failures on Dependency CVE Scan + Container Image Scan — not blocking

## What Session 122 Delivered

- 6-panel cascade review of POST-P72 phase plan (two full review cycles):
  - Cycle 1: Architecture & Planning (Mode C), Product Requirements, Developer Experience
  - Cycle 2: Security Audit, Testing & Quality, DevOps & Deployment
- Phase plan APPROVED: `docs/phases/PHASE-PLAN-POST-P72-2026.md` — Clusters POST-1 through POST-4
- 18 locked architectural decisions (see phase plan for details)
- Refreshed `next-session.md`, `task_plan.md`, `docs/phases/README.md`

## Session 123 Priority Queue

### Immediate: POST-1 (Foundation & Baseline)

| Priority | Task | Status |
|---|---|---|
| T1 | POST-1.1 — ARCH-AEP Loop 7 review + triage | in_progress |
| T2 | POST-1.2 — Docs refresh (this PR) | in_progress |
| T3 | POST-1.4 — SHA-256 timing oracle fix (`hmac.compare_digest()` in `sha256_verify()`) | pending |
| T4 | POST-1.3 — Frontend bundling decision | pending |
| T5 | POST-1.5 — SkillsBench baseline run | pending (blocked on T1) |

POST-1 exit gate: Loop 7 remediations merged; next-session.md current; SkillsBench CTRF baseline committed to `benchmarks` branch.

### Subsequent Clusters

**POST-2: SkillsBench Competitiveness**
- POST-2.1a — SkillsBench smoke suite CI (every PR, mocked LLM, ≤15 tasks)
- POST-2.1b — SkillsBench full run (weekly, live LLM, `benchmarks` branch)
- POST-2.2 — Context window management for evaluation harness
- POST-2.3 — Iterative tool-use loop + 4-stage skill matching
- Exit gate: SkillsBench score improves in ≥2 targeted categories vs. baseline

**POST-3: Pack Ecosystem**
- POST-3.1 — Pack sandbox + injection test suite (6 attack categories)
- POST-3.2 — Pack registry v1 (GitHub JSON index, Sigstore signing, revocation)
- POST-3.3 — CLI DX improvements (`--json`, `--plain`, pack-aware `diagnose`)
- POST-3.4 — 5 seed packs (web-research, code-review, meeting-notes, document-summarizer, developer-assistant)
- Exit gate: `agent33 pack search` works against live registry; 5 seed packs installable; pack signing enforced

**POST-4: Interruption & Self-Improvement**
- POST-4.1 — P69b UX spec + API contract document
- POST-4.2 — SSE event schema versioning (strict rejection model)
- POST-4.3 — P69b implementation (PausedInvocation state, HMAC nonce, feature flag)
- POST-4.4 — P-PACK v3 A/B harness (30-day calendar gate + statistical significance)
- POST-4.5 — P-PACK v3 behavior modifications (feature flag, A/B regression gate)
- Exit gate: P69b end-to-end tested; P-PACK v3 behavioral A/B tests passing; both behind feature flags

**POST-CLUSTER: Distribution & Ecosystem Growth**
- Public launch preparation (README as product page)
- P-ENV v2 auto-install + automated model download
- Pack marketplace web UI
- Community submissions (only after pack signing + approval queue proven)

### Dependency Graph

```
ARCH-AEP Loop 7
  └──→ POST-1 (Foundation & Baseline) ──→ POST-2 (SkillsBench)
        │                                        │
        │                                   ARCH-AEP (POST-2)
        │                                        │
        └──→ POST-3 (Pack Ecosystem) ◄───────────┘
               │
          ARCH-AEP (POST-3 supply chain)
               │
               └──→ POST-4 (Interruption & Self-Improvement)
                          │
                    [calendar gate: 30 days P68-Lite data]
                          │
                     POST-4.4 / 4.5 (P-PACK v3)
```

## Locked Architectural Decisions (Session 122)

These decisions are final and must not be reopened without explicit user approval:

1. **SkillsBench framing**: Two-tier — smoke (every PR, mocked, ≤15 tasks) + full (weekly, live, `benchmarks` branch)
2. **P69b pause state**: `PausedInvocation` state record in state machine — NOT mutable in-memory flag
3. **Pack registry v1**: GitHub JSON index — no custom hosted API
4. **Pack signing**: Sigstore cosign (keyless) — SHA-256 is integrity only
5. **Pack sandbox**: Reuse CLIAdapter subprocess isolation — injection scanner is correct defense layer
6. **P-PACK v3 gate**: 30-day calendar gate AND purpose-built A/B harness with statistical significance
7. **Headless P69b**: `AGENT33_HEADLESS_TOOL_APPROVAL=approve|deny` env var, default `deny`
8. **SHA-256 timing oracle**: Replace `==` with `hmac.compare_digest()` in `sha256_verify()`
9. **P69b replay protection**: HMAC nonce — `HMAC-SHA256(run_id + tool_name + floor(timestamp/30), tenant_secret)`
10. **SSE version enforcement**: Strict rejection — v1 clients reject v2 streams entirely
11. **A/B harness statistics**: 95% confidence, n≥30, −5% threshold, Bonferroni correction
12. **Benchmark results**: `benchmarks` branch (not `main`) — bot commits, signed
13. **Feature flag lifecycle**: Every flag ships with lifecycle metadata + file-based kill switch
14. **Pack revocation**: Registry JSON includes `revoked` field; install checks revocation
15. **P68-Lite monitoring**: Alert if outcomes table empty >24h during gate
16. **SkillsBench regression alert**: Auto-open GitHub issue if weekly run shows >5% drop

## Environmental Notes

- Root checkout is intentionally dirty — do not implement from root
- Use fresh worktrees from `origin/main` for all implementation work
- One fresh worktree per slice; dispose after merge
- One fresh agent per slice; dispose after merge
- Post-P72 phase plan (`docs/phases/PHASE-PLAN-POST-P72-2026.md`) exists in root checkout but is not yet committed to `origin/main` — include in next code PR or dedicated docs PR

## Key References

- `docs/phases/PHASE-PLAN-POST-P72-2026.md` — Approved POST-P72 phase plan (4 clusters + post-cluster)
- `docs/phases/PHASE-PLAN-UX-AUTONOMY-2026.md` — Prior plan (fully executed)
- `docs/phases/README.md` — Canonical phase index
- `docs/research/skillsbench-analysis.md` — SkillsBench analysis (2,000+ lines)
- `task_plan.md` — Active execution queue
- `progress.md` — Session-by-session progress log
- `findings.md` — Technical findings and investigation notes

## Fresh Context Protocol

1. Create fresh worktree from `origin/main`
2. Read `task_plan.md`, `findings.md`, and `progress.md`
3. Read `docs/phases/PHASE-PLAN-POST-P72-2026.md` for current roadmap
4. Check for ARCH-AEP Loop 7 results in `docs/research/session121-arch-aep-loop7.md`
5. Research before implementing — each slice needs a scope doc first
