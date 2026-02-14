# Next Session Briefing

Last updated: 2026-02-14T14:00

## Current State
- **Branch**: `main`
- **Main**: 337 tests passing, 0 lint errors
- **Open PRs**: 0
- **Merged PRs**: #2 (Trivy), #3 (Performance), #4 (Governance), #5 (IDOR)
- **Phases 1-14, 21**: Complete
- **Phases 15-20**: Planned
- **Research**: 29 dossiers + 5 strategy docs complete

## What Was Done This Session (2026-02-14, Session 8)

### Phase 14 Complete — 12 Security Hardening Items Implemented

All 12 Phase 14 items implemented with 59 new tests:

| # | Item | Files Changed |
|---|------|---------------|
| 1 | Multi-segment command validation (blocks `|`, `&&`, `||`, `;`, `$()`, backticks) | `shell.py`, `governance.py` |
| 2 | Autonomy levels (ReadOnly/Supervised/Full) per-agent | `definition.py`, `governance.py`, `runtime.py` |
| 3 | Rate limiting with sliding-window + burst control | `governance.py`, `config.py` |
| 4 | Path traversal hardening (null bytes, `..`, symlinks, `relative_to()`) | `file_ops.py` |
| 5 | `tenant_id` in TokenPayload for multi-tenant isolation | `auth.py` |
| 6 | Session ownership model (observations filtered by authenticated user) | `memory_search.py` |
| 7 | `run_command.py` merges env with `os.environ` (preserves PATH on Windows) | `run_command.py` |
| 8 | API key expiration support (time-based TTL) | `auth.py` |
| 9 | Deny-first permission evaluation (deny rules checked before allow) | `permissions.py` |
| 10 | Pairing brute-force lockout (5 failures = 15min lockout) | `pairing.py` |
| 11 | Request size limit middleware (configurable, default 10MB) | `main.py`, `config.py` |
| 12 | `SecretStr` for all sensitive config fields | `config.py`, `auth.py`, `agents.py`, `reader.py`, `jina_embeddings.py` |

## Priority 1: Next Phase (Phase 15 — Review Automation)

Phase dependency chain: ~~14 (Security)~~ → **15 (Review Automation)** → 16 (Observability) → 17 (Evaluation Gates) → 18 (Autonomy Enforcement) → 19 (Release Automation) → 20 (Continuous Improvement)

## Priority 2: ZeroClaw Feature Parity (Post-Phase 14)

Remaining ZeroClaw parity items to integrate into Phases 15-20:

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
python -m pytest tests/ -q               # full suite (~13 min, 337 tests)
python -m pytest tests/ -x -q            # stop on first failure
python -m pytest tests/test_phase14_security.py -x -q  # Phase 14 tests (59 tests)
python -m pytest tests/test_execution_*.py -x -q  # Phase 13 tests only (54 tests)
python -m ruff check src/ tests/         # lint (0 errors)
```
