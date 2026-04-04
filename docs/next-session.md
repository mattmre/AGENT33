# Next Session Briefing

Last updated: 2026-04-04 (Session 120 wrap — UX-A cluster complete)

## Current State

- **Branch posture**: root checkout is intentionally dirty and lags `origin/main`. Always use fresh worktrees.
- **Open PRs**: 0
- **Latest merged PR**: #371 (P64 — first-run wizard + ARCH-AEP Loop 4)
- **Latest commit on main**: `acf662b`
- **Cumulative PRs merged**: 371
- **All Phases 01-59**: complete
- **Cluster UX-A (P60a, P-ENV, P63, P60b, P62, P61, P64)**: **complete**
- **ARCH-AEP Loop 4**: complete — 0C/1H/3M/2L, H1 closed in PR #371
- **Active roadmap**: `docs/phases/PHASE-PLAN-UX-AUTONOMY-2026.md`
- **CVE scan**: pre-existing failures on Dependency CVE Scan + Container Image Scan — not blocking

## What Session 120 Delivered

7 PRs merged, ~138 new tests, full UX-A cluster implemented:

| PR | Phase | Description |
|----|-------|-------------|
| #365 | P60a | Protocol definitions + lifespan fallbacks + lite mode config |
| #366 | P-ENV | Environment detection, hardware profiling, model selection CLI |
| #367 | P63 | `agent33 diagnose` traffic-light subsystem health checks |
| #368 | P60b | SQLite long-term memory adapter for lite mode |
| #369 | P62 | `agent33 bootstrap` — secure .env.local generation |
| #370 | P61 | Named config profiles (AGENT33_PROFILE env var + `agent33 start --profile`) |
| #371 | P64 | `agent33 wizard` — 5-step first-run setup wizard + ARCH-AEP Loop 4 |

Key new capabilities:
- `AGENT33_MODE=lite` boots with zero external services (SQLite + in-process cache/bus)
- `agent33 env show` — detect hardware, suggest model, recommend profile
- `agent33 diagnose [--fix]` — traffic-light health checks
- `agent33 bootstrap` — generate random secrets
- `agent33 start --profile <name>` — activate named config preset
- `agent33 wizard` — interactive 5-step first-run setup

## Next Session: Cluster UX-B

### Goal
Non-technical operator deploys a production workflow from a template in <15 minutes.

### UX-B Sequence

```
P65  Operator quick-start templates (8 ready-to-invoke templates)
P66  Agent Builder UI (no-code agent creation in web frontend)
P67  Autonomy Level System (0-3 levels)
→ ARCH-AEP Loop 5
```

### UX-B Exit Gate
All 8 templates run with zero configuration beyond LLM provider. Agent builder produces runnable agents. Autonomy levels enforce correctly. Panel review before UX-C.

### ARCH-AEP Loop 4 Open Items (carry to UX-B)
Low priority — fix if touching relevant code, not worth dedicated PRs:
- M2: `InProcessMessageBus` — log DEBUG warning on publish to unknown channel
- M3: Wizard — warn if env cache is >7 days old
- L1: Template label matching in wizard — use dict lookup instead of `startswith()`
- L2: `ProfileSettingsSource.get_field_value` — return `field_name` not `""` for unknowns

### Fresh Context Protocol
1. Create fresh worktree from `origin/main`
2. Read `task_plan.md`, `findings.md`, and `progress.md`
3. Read `docs/phases/PHASE-PLAN-UX-AUTONOMY-2026.md` for P65-P67 spec
4. Research before implementing — each slice needs a scope doc first

### P65 Quick-Start Templates — Key Spec Points
- 8 templates in `core/templates/`
- Each needs a "try with sample data" mode requiring zero user data
- Templates: Personal Assistant, Research Assistant, Document Summarizer, Meeting Notes, Writing Helper, Code Review, Ticket Triage, Data Extractor
- Acceptance: all 8 run with zero config beyond LLM provider

### P66 Agent Builder UI — Key Spec Points
- No-code agent creation in existing web frontend
- Capability picker redesigned as user-action toggles (not P/I/V/R/X categories)
- Live system prompt preview endpoint
- Export to JSON compatible with `agent-definitions/`
- Acceptance: non-technical user creates working custom agent in <10 minutes

### P67 Autonomy Levels — Key Spec Points
- 4 levels: 0=fully supervised, 1=autonomous read/analyze (default), 2=autonomous except destructive, 3=fully autonomous
- `autonomy_level_to_budget()` maps level → `AutonomyBudget`
- Wired into `AgentRuntime.invoke_iterative()`
- Wizard step asks preference in plain language
