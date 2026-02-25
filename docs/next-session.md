# Next Session Briefing

Last updated: 2026-02-24T00:00Z

## Current State

- **Branch status**: Phase 29.3 and 29.4 implemented; Phase 30 MVP and Phase 31 MVP implemented on the working branch, pending PR splitting/review.
- **Latest session**: Session 37 (`docs/sessions/session-37-2026-02-24.md`)
- **Research summary**: `docs/research/phase29_3-31-mvp-implementation-summary-2026-02-24.md`

## What Was Completed (Session 37)

### Phase 29.3 — Reasoning Error Recovery
- Added bounded retry and graceful degradation in reasoning phase dispatch.
- Added degradation artifact capture and fail-closed VERIFY handling.

### Phase 29.4 — Stuck Detector Integration
- Added OpenHands-style heuristic detector module and protocol contract.
- Integrated stuck detection into reasoning loop termination path.

### Phase 30 MVP — Effort Routing
- Added effort-based model/token routing primitives.
- Integrated effort routing into agent runtime and invoke APIs.
- Added settings flags for runtime control.

### Phase 31 MVP — Learning Signals
- Added learning signal models/service flow and API endpoints.
- Added feature-gated behavior and optional auto-intake generation settings.

### Pre-existing Test Fixes
- Chat/health tests updated for current route behavior and resilient service-state assertions.

## Immediate Next Priorities

### Priority 1: Phase 30 Follow-on Hardening
- Add heuristic effort classifier for automatic effort selection.
- Add per-tenant/per-domain routing policy support.
- Add explicit cost-awareness telemetry in routing decisions.

### Priority 2: Phase 31 Persistence + Signal Quality
- Persist learning signals and generated intakes to durable storage.
- Add enrichment/scoring pipeline for higher-quality automated intake generation.
- Extend summary reporting for trend windows and tenant-scoped analytics.

### Priority 3: Phase 32 Kickoff
- Begin middleware-chain framework and connector governance base.
- Introduce circuit-breaker primitives for external tool/service boundaries.

### Priority 4: Regression + Documentation Hygiene
- Run full backend regression suite once branch/merge state is finalized.
- Update phase progress logs (`phase-29`, `phase-30`) with MVP milestone entries.

## Startup Checklist (Next Session)

```bash
git checkout main
git pull --ff-only
cd engine
python -m pytest tests/test_reasoning.py tests/test_stuck_detector.py -q
python -m pytest tests/test_phase30_effort_routing.py tests/test_phase31_learning_signals.py -q
python -m pytest tests/test_chat.py tests/test_health.py -q
python -m pytest tests/ -q
```

## Key Paths

| Purpose | Path |
|---|---|
| Reasoning protocol (29.x) | `engine/src/agent33/agents/reasoning.py` |
| Stuck detector (29.4) | `engine/src/agent33/agents/stuck_detector.py` |
| Effort routing (30 MVP) | `engine/src/agent33/agents/effort.py` |
| Runtime effort integration | `engine/src/agent33/agents/runtime.py` |
| Learning signals models/service (31 MVP) | `engine/src/agent33/improvement/{models.py,service.py}` |
| Learning signal API routes | `engine/src/agent33/api/routes/improvements.py` |
| Chat/health test fixes | `engine/tests/{test_chat.py,test_health.py}` |
| Session 37 log | `docs/sessions/session-37-2026-02-24.md` |
| Session 37 research summary | `docs/research/phase29_3-31-mvp-implementation-summary-2026-02-24.md` |
