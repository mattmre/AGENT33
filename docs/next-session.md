# Next Session Briefing

Last updated: 2026-04-10 (Session 124 POST-3.2 wrap)

## Current State

- **Branch posture**: treat the root checkout as disposable; always use fresh worktrees from `origin/main` for implementation.
- **Open PRs**: 0
- **Latest merged PR**: #395 (POST-3.2 — pack registry v1)
- **Latest commit on main**: `3dafe21`
- **Cumulative PRs merged**: 395
- **All Phases 01-72**: COMPLETE
- **Cluster UX-A/B/C/D**: COMPLETE
- **ARCH-AEP Loops 1-8**: COMPLETE
- **POST-1 — Foundation & Baseline**: COMPLETE (#384-#387)
- **POST-2 — SkillsBench Competitiveness**: COMPLETE (#388-#392)
- **POST-3.1 — Pack sandbox + injection tests**: COMPLETE (#394)
- **POST-3.2 — Pack registry v1**: COMPLETE (#395)
- **Next live slice**: POST-3.3 — CLI DX improvements
- **Active roadmap**: `docs/phases/PHASE-PLAN-POST-P72-2026.md`
- **CVE scan**: pre-existing failures on Dependency CVE Scan + Container Image Scan — not blocking

## What Session 124 Delivered

- `#393` — planning/docs reconciliation after POST-2
- `#394` — POST-3.1 sandbox hardening + injection regression coverage
- `#395` — POST-3.2 revocation + Sigstore-aware provenance verification
- recovery docs refreshed so the next fresh slice starts from POST-3.3 instead of stale pre-POST-3 state

## Session 124 Priority Queue

### Immediate: POST-3 (Pack Ecosystem continuation)

| Priority | Task | Status |
|---|---|---|
| T1 | POST-3.3 — CLI DX improvements (`--json`, `--plain`, pack-aware `diagnose`) | next_up |
| T2 | POST-3.4 — 5 seed packs (web-research, code-review, meeting-notes, document-summarizer, developer-assistant) | pending |
| T3 | POST-4.1 — P69b UX spec + API contract document | pending (blocked on T2) |
| T4 | POST-4.2 — SSE event schema versioning | pending (blocked on T3) |
| T5 | POST-4.3 — P69b implementation | pending (blocked on T4) |

POST-3 exit gate: CLI registry UX stabilized; seed packs landed; pack signing and revocation flows proven against live registry assumptions.

### Follow-on: POST-4 (Interruption & Self-Improvement)

- POST-4.1 — P69b UX spec + API contract document
- POST-4.2 — SSE event schema versioning (strict rejection model)
- POST-4.3 — P69b implementation (PausedInvocation state, HMAC nonce, feature flag)
- POST-4.4 — P-PACK v3 A/B harness (30-day calendar gate + statistical significance)
- POST-4.5 — P-PACK v3 behavior modifications (feature flag, A/B regression gate)
- Exit gate: P69b end-to-end tested; P-PACK v3 behavioral A/B tests passing; both behind feature flags

### Post-Cluster: Distribution & Ecosystem Growth

- Public launch preparation (README as product page)
- P-ENV v2 auto-install + automated model download
- Pack marketplace web UI
- Community submissions (only after pack signing + approval queue proven)

### Dependency Graph

```text
POST-3.1
  └──→ POST-3.2
        ├──→ POST-3.3
        └──→ POST-3.4
              └──→ POST-4.1
                    └──→ POST-4.2
                          └──→ POST-4.3
                                └──→ POST-4.4 / POST-4.5
                                      [calendar gate: 30 days P68-Lite data]
```

## Locked Architectural Decisions (Session 122)

These decisions are final and must not be reopened without explicit user approval:

1. **SkillsBench framing**: Two-tier — smoke (every PR, mocked, <=15 tasks) + full (weekly, live, `benchmarks` branch)
2. **P69b pause state**: `PausedInvocation` state record in state machine — NOT mutable in-memory flag
3. **Pack registry v1**: GitHub JSON index — no custom hosted API
4. **Pack signing**: Sigstore cosign (keyless) — SHA-256 is integrity only
5. **Pack sandbox**: Reuse CLIAdapter subprocess isolation — injection scanner is correct defense layer
6. **P-PACK v3 gate**: 30-day calendar gate AND purpose-built A/B harness with statistical significance
7. **Headless P69b**: `AGENT33_HEADLESS_TOOL_APPROVAL=approve|deny` env var, default `deny`
8. **SHA-256 timing oracle**: Replace `==` with `hmac.compare_digest()` in `sha256_verify()`
9. **P69b replay protection**: HMAC nonce — `HMAC-SHA256(run_id + tool_name + floor(timestamp/30), tenant_secret)`
10. **SSE version enforcement**: Strict rejection — v1 clients reject v2 streams entirely
11. **A/B harness statistics**: 95% confidence, n>=30, -5% threshold, Bonferroni correction
12. **Benchmark results**: `benchmarks` branch (not `main`) — bot commits, signed
13. **Feature flag lifecycle**: Every flag ships with lifecycle metadata + file-based kill switch
14. **Pack revocation**: Registry JSON includes `revoked`; install checks revocation
15. **P68-Lite monitoring**: Alert if outcomes table empty >24h during gate
16. **SkillsBench regression alert**: Auto-open GitHub issue if weekly run shows >5% drop

## Environmental Notes

- Do not implement from the root checkout; use fresh worktrees from `origin/main`
- One fresh worktree per slice; dispose after merge
- One fresh agent or research pass per slice; dispose after merge
- Loop 7 report: `docs/research/session121-arch-aep-loop7.md`
- Loop 8 report: `docs/research/session123-arch-aep-post2.md`

## Key References

- `docs/phases/PHASE-PLAN-POST-P72-2026.md` — Approved POST-P72 phase plan
- `docs/phases/README.md` — Canonical phase index
- `docs/research/skillsbench-analysis.md` — SkillsBench analysis
- `docs/research/session121-arch-aep-loop7.md` — Loop 7 findings
- `docs/research/session123-arch-aep-post2.md` — Loop 8 findings
- `docs/research/session124-post31-pack-sandbox-scope.md` — POST-3.1 scope memo
- `docs/research/session124-post32-pack-registry-v1-scope.md` — POST-3.2 scope memo
- `task_plan.md` — Active execution queue
- `progress.md` — Session-by-session progress log
- `findings.md` — Technical findings and investigation notes

## Fresh Context Protocol

1. Create fresh worktree from `origin/main`
2. Read `task_plan.md`, `findings.md`, and `progress.md`
3. Read `docs/phases/PHASE-PLAN-POST-P72-2026.md` for current roadmap
4. Start from POST-3.3 unless a newer merged PR has already advanced the queue
5. Check whether any PR comments or review findings exist before starting a new slice
6. Research before implementing — each slice needs a scope doc first
