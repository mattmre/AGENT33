# Next Session Briefing

Last updated: 2026-02-24T23:00Z

## Current State

- **Branch status**: Phase 30 hardening and Phase 31 persistence/quality work completed; Phase 32 connector-boundary kickoff completed; regression suite green in-session.
- **Latest session**: Session 38 (`docs/sessions/session-38-2026-02-24.md`)
- **Prior milestone context**: Session 37 (`docs/sessions/session-37-2026-02-24.md`)

## What Was Completed (Session 38)

### PR-1 — Phase 30 Hardening
- Added deterministic effort classifier flow with explicit precedence (request > policy > heuristic > default).
- Added tenant/domain and tenant|domain routing policy handling.
- Added routing cost/tokens telemetry fields in effort decisions and runtime decision payloads.

### PR-2 — Phase 31 Persistence + Signal Quality
- Added durable learning persistence backends (memory/file) and route-level backend wiring.
- Added deterministic learning-signal enrichment/quality scoring.
- Added tenant/window-aware learning summary signals and quality-aware auto-intake ordering.

### PR-3 — Phase 32 Kickoff
- Introduced connector boundary middleware-chain executor primitives.
- Added governance policy middleware and blocklist policy.
- Added circuit-breaker primitives and MCP boundary integration.

## Immediate Next Priorities

### Priority 1: Phase 32 Adoption
- Expand connector-boundary middleware coverage beyond MCP and document default policy packs.
- Add route/service integration points for consistent governance enforcement across connectors.

### Priority 2: Persistence Hardening + Migration Path
- Define migration path from file-backed learning persistence to database-backed storage.
- Add backup/restore and corruption-recovery behavior for persisted learning state.

### Priority 3: Observability Integration
- Wire effort-routing telemetry into observability dashboards/metrics exports.
- Add alerting thresholds for high-cost/high-effort routing patterns.

### Priority 4: PR Review and Merge Flow
- Use finalized review packets:
  - `docs/review-packets/pr-1-phase32-adoption.md`
  - `docs/review-packets/pr-2-persistence-hardening.md`
  - `docs/review-packets/pr-3-observability-integration.md`
  - `docs/review-packets/validation-snapshots.md`
  - `docs/review-packets/merge-sequencing.md`
- Execute post-merge smoke plan after each merge step:
  - PR-1 merge smoke: connector tests (**11**) + connector regression group (**92**) + baseline targeted (**187**).
  - PR-2 merge smoke: persistence tests (**14**) + baseline targeted (**187**).
  - PR-3 merge smoke: observability set (**38**) + phase30 suite (**15**) + baseline targeted (**187**).

## Startup Checklist (Next Session)

```bash
git checkout main
git pull --ff-only
cd engine
python -m pytest tests/test_phase30_effort_routing.py tests/test_phase31_learning_signals.py tests/test_phase32_connector_boundary.py -q
python -m pytest tests/test_reasoning.py tests/test_stuck_detector.py tests/test_chat.py tests/test_health.py -q
python -m pytest tests/ -q
```

## Key Paths

| Purpose | Path |
|---|---|
| Effort routing hardening | `engine/src/agent33/agents/effort.py` |
| Runtime routing decision plumbing | `engine/src/agent33/agents/runtime.py` |
| Learning persistence + quality | `engine/src/agent33/improvement/{persistence.py,quality.py,service.py}` |
| Learning signal API wiring | `engine/src/agent33/api/routes/improvements.py` |
| Connector boundary primitives | `engine/src/agent33/connectors/{executor.py,middleware.py,governance.py,circuit_breaker.py}` |
| MCP boundary integration | `engine/src/agent33/tools/mcp_bridge.py` |
| Phase 30/31/32 tests | `engine/tests/{test_phase30_effort_routing.py,test_phase31_learning_signals.py,test_phase32_connector_boundary.py}` |
| Session 38 log | `docs/sessions/session-38-2026-02-24.md` |
