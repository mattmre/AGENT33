# Next Session Briefing

Last updated: 2026-02-14T16:00

## Current State
- **Branch**: `main`
- **Main**: 402 tests passing, 0 lint errors
- **Open PRs**: 0
- **Merged PRs**: #2 (Trivy), #3 (Performance), #4 (Governance), #5 (IDOR)
- **Phases 1-15, 21**: Complete
- **Phases 16-20**: Planned
- **Research**: 29 dossiers + 5 strategy docs complete

## What Was Done This Session (2026-02-14, Session 9)

### Phase 15 Complete — Review Automation & Two-Layer Review (65 new tests)

Built the `engine/src/agent33/review/` module implementing the two-layer review workflow:

| # | Component | Module | Description |
|---|-----------|--------|-------------|
| 1 | Review models | `review/models.py` | ReviewRecord, RiskLevel (5 levels), RiskTrigger (14 categories), SignoffState (10 states), ReviewDecision, L1/L2 checklists |
| 2 | Risk assessor | `review/risk.py` | Maps triggers to risk levels; determines L1/L2 requirements |
| 3 | Reviewer assignment | `review/assignment.py` | 14-entry assignment matrix matching change types to agent/human reviewers |
| 4 | Signoff state machine | `review/state_machine.py` | Enforces valid state transitions; terminal MERGED state |
| 5 | Review service | `review/service.py` | Full lifecycle: create, assess, assign L1/L2, submit, approve, merge |
| 6 | Review API | `api/routes/reviews.py` | 12 REST endpoints under `/v1/reviews` with scope-based auth |
| 7 | Router registration | `main.py` | Reviews router added to FastAPI app |

Key design decisions:
- **Risk levels**: none → L1 off; low → L1 only; medium → L1 + L2 agent; high → L1 + L2 human; critical → L1 + designated human
- **State machine**: DRAFT → READY → L1_REVIEW → L1_APPROVED → [L2_REVIEW → L2_APPROVED →] APPROVED → MERGED
- **Escalation**: L1 reviewer can escalate (forces L2 requirement even if originally not needed)
- **Tenant isolation**: Reviews filtered by `tenant_id` from authenticated user

## Priority 1: Next Phase (Phase 16 — Observability & Trace Pipeline)

Phase dependency chain: ~~14 (Security)~~ → ~~15 (Review Automation)~~ → **16 (Observability)** → 17 (Evaluation Gates) → 18 (Autonomy Enforcement) → 19 (Release Automation) → 20 (Continuous Improvement)

## Priority 2: ZeroClaw Feature Parity

Remaining ZeroClaw parity items to integrate into Phases 16-20:

| # | Item | Source | Priority | Effort |
|---|------|--------|----------|--------|
| 13 | Hybrid search (BM25 + vector) | ZeroClaw `memory/vector.rs` | P0 | 3 days |
| 14 | Embedding cache with LRU | ZeroClaw `memory/sqlite.rs` | P1 | 1.5 days |
| 15 | Tokenizer-aware chunking | ZeroClaw `memory/chunker.rs` | P1 | 1 day |
| 16 | JSON Schema on Tool protocol | ZeroClaw `tools/traits.rs` | P1 | 2 days |
| 17 | Provider registry expansion (22+) | ZeroClaw providers | P1 | 2 days |
| 18 | Skills/plugin system | ZeroClaw `skills/mod.rs` | P2 | 4 days |
| 19 | Channel health checks | ZeroClaw `channels/mod.rs` | P2 | 1.5 days |
| 20 | Matrix channel adapter | ZeroClaw `channels/matrix.rs` | P3 | 2 days |

## Identity Preservation Principles

When absorbing ZeroClaw features, preserve AGENT-33's unique capabilities:
1. **Multi-Agent Orchestration** — autonomy levels per-agent, rate limits per-agent, skills declare agent-role compatibility
2. **Governance Layer** — command validation as governance check, rate limits governance-enforced
3. **Training/Self-Improvement** — evaluate absorbed feature effectiveness via training loop
4. **Evidence Capture** — all absorbed features must produce audit evidence

Formula: **ZeroClaw's breadth + AGENT-33's depth = superior system**

## Key Research Documents
| Document | Path | Size |
|----------|------|------|
| Feature parity analysis | `docs/research/zeroclaw-feature-parity-analysis.md` | 54KB |
| Libraries deep dive | `docs/research/zeroclaw-libraries-analysis.md` | 60KB |
| Paradigm analysis | `docs/research/paradigm-analysis.md` | 23KB |
| Evolution strategy | `docs/research/adaptive-evolution-strategy.md` | 23KB |
| Integration report | `docs/research/integration-report-2026-02-13.md` | 22KB |

## Key Files to Know
| Purpose | Path |
| --- | --- |
| Entry point | `engine/src/agent33/main.py` |
| Config | `engine/src/agent33/config.py` |
| Agent runtime | `engine/src/agent33/agents/runtime.py` |
| Agent registry | `engine/src/agent33/agents/registry.py` |
| Agent definitions | `engine/agent-definitions/*.json` |
| Tool registry | `engine/src/agent33/tools/registry.py` |
| Execution layer | `engine/src/agent33/execution/` |
| Review automation | `engine/src/agent33/review/` |
| Security: middleware | `engine/src/agent33/security/middleware.py` |
| Security: permissions | `engine/src/agent33/security/permissions.py` |
| Security: auth | `engine/src/agent33/security/auth.py` |
| Security: injection | `engine/src/agent33/security/injection.py` |
| Tool governance | `engine/src/agent33/tools/governance.py` |
| Phase plans | `docs/phases/` |
| Session logs | `docs/sessions/` |
| Research dossiers | `docs/research/repo_dossiers/` |

## Test Commands
```bash
cd engine
python -m pytest tests/ -q               # full suite (~13 min, 402 tests)
python -m pytest tests/ -x -q            # stop on first failure
python -m pytest tests/test_phase15_review.py -x -q  # Phase 15 tests (65 tests)
python -m pytest tests/test_phase14_security.py -x -q  # Phase 14 tests (59 tests)
python -m pytest tests/test_execution_*.py -x -q  # Phase 13 tests only (54 tests)
python -m ruff check src/ tests/         # lint (0 errors)
```
