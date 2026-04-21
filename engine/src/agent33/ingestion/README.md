# agent33.ingestion

Governed candidate lifecycle for external and community assets.

## Purpose

This module manages assets that originate outside the AGENT33 first-party pack
tree — community submissions, externally sourced skills, workflows, and tools.
It implements the lifecycle defined in architectural decision #18:

```
candidate -> validated -> published -> revoked
```

External assets enter at `CANDIDATE` status with `LOW` confidence and cannot
be executed until an operator explicitly promotes them through validation and
publication gates.

## Clean-Room Restriction

No code in this module may originate from the EvoMap/Evolver project. See the
design contract for the full legal and architectural rationale:

- `docs/research/evolver-clean-room-guardrails.md`

## Governing Decisions

- Decision #17 — Evolver ingestion boundary (concept-only clean-room adaptation)
- Decision #18 — Imported-asset lifecycle with confidence/trust labels

Both decisions are in `docs/phases/PHASE-PLAN-POST-P72-2026.md`.

## Module Contents

| Module     | Status    | Sprint | Description                          |
|------------|-----------|--------|--------------------------------------|
| `models.py`| Stub      | 0      | `CandidateAsset` Pydantic type model |
| (future)   | Planned   | 1–5    | Intake, validation, and promotion    |
