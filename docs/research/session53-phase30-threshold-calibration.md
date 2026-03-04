# Session 53 Research: Phase 30 Threshold Calibration (Priority #2)

Date: 2026-03-04
Scope: adaptive effort-routing refinement

## Context

Phase 30 routing heuristics were deterministic but used hardcoded thresholds for:

- payload size bands
- input-field count
- iteration budget
- low/high effort score cutoffs

This made calibration difficult and forced code changes for each tuning pass.

## Design Decision

Promote heuristic thresholds to typed configuration so calibration can be done through settings and validated centrally.

### Added settings

- `agent_effort_heuristic_low_score_threshold`
- `agent_effort_heuristic_high_score_threshold`
- `agent_effort_heuristic_medium_payload_chars`
- `agent_effort_heuristic_large_payload_chars`
- `agent_effort_heuristic_many_input_fields_threshold`
- `agent_effort_heuristic_high_iteration_threshold`

### Validation rules

- all heuristic thresholds must be non-negative
- high score threshold must be strictly greater than low score threshold
- large payload threshold must be strictly greater than medium payload threshold

## Runtime observability additions

Routing decisions now emit calibration metadata:

- `heuristic_score`
- `heuristic_low_threshold`
- `heuristic_high_threshold`

This enables evidence-driven tuning from observed production/request traces.

## Test strategy

- router unit tests for configurable score thresholds
- router unit tests for configurable payload bands
- runtime test ensuring calibration metadata appears in invoke routing payload
- settings validation tests enforcing threshold ordering
