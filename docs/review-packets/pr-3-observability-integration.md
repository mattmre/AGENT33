# PR-3 Review Packet — Observability Integration (Priority 14)

## Scope
- Integrate routing/effort telemetry into operational observability paths.
- Validate signal continuity from routing decisions through integration surfaces.

## Review Focus
- Metrics/log fields for effort routing are emitted consistently.
- Integration wiring preserves telemetry fidelity.
- Existing routing behavior remains backward compatible.

## Validation Evidence (Session)
- Observability set (phase30 + integration): **38 passed**
- Phase30 routing suite: **15 passed**
- Baseline targeted regression: **187 passed**

## Merge Gate
- Require all observability and phase30 counts above to pass on PR head.
- If integration count drops, hold merge and capture root-cause notes in review.

## Primary Code Areas
- `engine/src/agent33/agents/effort.py`
- `engine/src/agent33/agents/runtime.py`
- `engine/tests/test_phase30_effort_routing.py`
- `engine/tests/test_integration_wiring.py`
