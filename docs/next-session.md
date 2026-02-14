# Next Session Briefing

Last updated: 2026-02-14T11:00

## Current State
- **Branch**: `main`, clean working tree
- **Main**: 278 tests passing, 0 lint errors
- **Open PRs**: 0
- **Merged PRs**: #2 (Trivy), #3 (Performance), #4 (Governance), #5 (IDOR)
- **Phases 1-13, 21**: Complete
- **Phase 14**: Partially complete (core security items merged, remaining items below)
- **Phases 15-20**: Planned
- **Research**: 29 dossiers + 5 strategy docs complete

## What Was Done This Session (2026-02-14, Session 7)

### Research Artifacts Regenerated
All research artifacts lost in Session 6's `git clean` have been regenerated:

**29 Research Dossiers** (committed as `409b14b` + `135c69b`):
- 28 original repos from the research sprint
- 1 new repo: `theonlyhennygod/zeroclaw` (added per user request)

**5 Strategy Documents** (committed as `135c69b`):
1. `docs/research/zeroclaw-feature-parity-analysis.md` (54KB) — Complete AGENT-33 vs ZeroClaw feature comparison across 15 categories with gap analysis and 20-item adaptation roadmap
2. `docs/research/zeroclaw-libraries-analysis.md` (60KB) — Deep dive on all ZeroClaw Rust dependencies, LLM providers, channels, security algorithms, tunnel providers
3. `docs/research/paradigm-analysis.md` (23KB) — 7 paradigms across 29 repos with convergence map and adoption order
4. `docs/research/adaptive-evolution-strategy.md` (23KB) — 4-cycle strategic roadmap (Phases 14-20)
5. `docs/research/integration-report-2026-02-13.md` (22KB) — Cross-cutting synthesis of all research sprint findings

## Priority 1: Implement ZeroClaw Feature Parity (from Feature Parity Analysis)

The comprehensive analysis identified **10 gaps** where ZeroClaw has features AGENT-33 lacks. Adaptation roadmap in `docs/research/zeroclaw-feature-parity-analysis.md`.

### Phase 14 Items (Security — from both ZeroClaw analysis and original Phase 14 scope)

| # | Item | Source | Severity | Effort | Files |
|---|------|--------|----------|--------|-------|
| 1 | Multi-segment command validation | ZeroClaw `security/policy.rs` | HIGH | 1 day | `tools/builtin/shell.py`, `tools/governance.py` |
| 2 | Autonomy levels (ReadOnly/Supervised/Full) | ZeroClaw `security/policy.rs` | HIGH | 2 days | `agents/definition.py`, `tools/governance.py`, `runtime.py` |
| 3 | Rate limiting on tool execution | ZeroClaw `ActionTracker` | HIGH | 1 day | `tools/governance.py`, `config.py` |
| 4 | Path traversal hardening | ZeroClaw path validation | HIGH | 1 day | `tools/builtin/file_ops.py` |
| 5 | `tenant_id` in TokenPayload | Original Phase 14 | HIGH | 1 day | `security/auth.py` |
| 6 | Session ownership model | Original Phase 14 | HIGH | 1 day | `api/routes/memory_search.py` |
| 7 | `run_command.py` env drops PATH on Windows | Original Phase 14 | MEDIUM | 0.5 day | `workflows/actions/run_command.py` |
| 8 | API key expiration support | Original Phase 14 | MEDIUM | 1 day | `security/auth.py` |
| 9 | Deny-first permission evaluation | Original Phase 14 | MEDIUM | 1 day | `security/permissions.py` |
| 10 | Pairing brute-force lockout | ZeroClaw `security/pairing.rs` | MEDIUM | 0.5 day | `messaging/pairing.py` |
| 11 | Request size limits | ZeroClaw gateway | MEDIUM | 0.5 day | `main.py`, `config.py` |
| 12 | `SecretStr` for sensitive config | Original Phase 14 | LOW | 0.5 day | `config.py` |

### Post-Phase 14 Items (from ZeroClaw parity)

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

### Already Addressed by PRs #2-#5
- [x] `require_scope()` wired into all routes (PR #5)
- [x] SHA-256 → PBKDF2-HMAC-SHA256 password hashing (PR #5)
- [x] Default secrets enforcement in production mode (PR #5)
- [x] NATS port bound to localhost (PR #2)
- [x] CORS methods/headers restricted (PR #2)
- [x] `/docs` auth bypass prefix fixed (PR #2)
- [x] Ownership-aware API key revocation (PR #5)
- [x] Governance constraints injected into prompts (PR #4)
- [x] Safety guardrails in every agent prompt (PR #4)

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
| Phase plans | `docs/phases/` |
| Session logs | `docs/sessions/` |
| Research dossiers | `docs/research/repo_dossiers/` |

## Test Commands
```bash
cd engine
python -m pytest tests/ -q               # full suite (~9 min, 278 tests on main)
python -m pytest tests/ -x -q            # stop on first failure
python -m pytest tests/test_execution_*.py -x -q  # Phase 13 tests only (54 tests)
python -m ruff check src/ tests/         # lint (0 errors)
```
