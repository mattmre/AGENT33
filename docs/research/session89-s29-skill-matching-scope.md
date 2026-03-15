# S29: Hybrid Skill Matching Calibration

**Session**: 89
**Slice**: S29
**Status**: Implemented
**Date**: 2026-03-15

## Summary

Implements a non-LLM, calibration-focused 4-stage hybrid skill matching
pipeline that complements the existing LLM-based `SkillMatcher` in
`skills/matching.py`.

The pipeline stages are:

1. **Exact** -- Case-insensitive name match (score = 1.0). Short-circuits
   when a match is found.
2. **Fuzzy** -- `difflib.SequenceMatcher` similarity against skill names
   and descriptions.
3. **Semantic** -- Jaccard overlap between query tokens and skill tags /
   category tokens (hyphenated tags are split).
4. **Contextual** -- Scores based on a provided context dict containing
   agent capabilities, task type, and tool overlap.

## Files

| File | Change |
|------|--------|
| `engine/src/agent33/skills/calibration.py` | New: `HybridSkillMatcher`, models, calibration/diagnostics |
| `engine/src/agent33/api/routes/skill_matching.py` | New: 6 API endpoints |
| `engine/src/agent33/config.py` | Added 4 config fields |
| `engine/src/agent33/main.py` | Router registration + lifespan wiring |
| `engine/tests/test_skill_calibration.py` | New: comprehensive test suite |
| `docs/research/session89-s29-skill-matching-scope.md` | This scope doc |

## API Endpoints

| Method | Path | Scope | Description |
|--------|------|-------|-------------|
| POST | `/v1/skills/match` | agents:read | Match a query to skills |
| GET | `/v1/skills/match/thresholds` | agents:read | Get current thresholds |
| PUT | `/v1/skills/match/thresholds` | admin | Update thresholds |
| POST | `/v1/skills/match/diagnostics` | agents:read | Per-stage diagnostics |
| POST | `/v1/skills/match/calibrate` | admin | Calibrate with test queries |
| POST | `/v1/skills/match/compare` | admin | A/B threshold comparison |

## Config Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `skill_match_fuzzy_threshold` | 0.7 | Minimum fuzzy similarity score |
| `skill_match_semantic_threshold` | 0.5 | Minimum semantic overlap score |
| `skill_match_contextual_threshold` | 0.4 | Minimum contextual match score |
| `skill_match_max_candidates` | 10 | Maximum candidates returned |

## Design Decisions

- **Separate from `matching.py`**: The existing `SkillMatcher` uses BM25 +
  LLM filtering.  The new `HybridSkillMatcher` is a lightweight, non-LLM
  alternative designed for calibration and threshold tuning. Keeping them
  separate avoids coupling and preserves the existing matcher's API.
- **Synchronous API**: The hybrid matcher is CPU-only (no LLM calls), so
  `match()`, `calibrate()`, and `get_diagnostics()` are synchronous methods.
  The async route handlers simply call them directly.
- **Deduplication**: When a skill appears in multiple stages, only the
  highest-scoring entry is kept.
- **Short-circuit**: An exact name match immediately returns without running
  fuzzy/semantic/contextual stages.
