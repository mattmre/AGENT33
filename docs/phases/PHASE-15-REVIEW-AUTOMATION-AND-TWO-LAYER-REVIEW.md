# Phase 15: Review Automation & Two-Layer Review

## Overview
- **Phase**: 15 of 20
- **Category**: Quality
- **Status**: Complete
- **Tests**: 65 new tests (402 total)

## Objectives
- Formalize two-layer review for high-risk work.
- Standardize reviewer roles and assignment rules.
- Improve review capture and signoff workflows.

## Implemented Items

| # | Component | Module | Description |
|---|-----------|--------|-------------|
| 1 | Review models | `review/models.py` | ReviewRecord, RiskLevel, RiskTrigger, SignoffState, ReviewDecision, checklists |
| 2 | Risk assessor | `review/risk.py` | Trigger-to-risk-level mapping, L1/L2 requirement determination |
| 3 | Reviewer assignment | `review/assignment.py` | Change-type to reviewer-role matrix, human-required flag |
| 4 | Signoff state machine | `review/state_machine.py` | 10-state lifecycle with validated transitions |
| 5 | Review service | `review/service.py` | Full lifecycle: create, assess, assign, submit, approve, merge |
| 6 | Review API routes | `api/routes/reviews.py` | 11 REST endpoints under `/v1/reviews` |
| 7 | Router registration | `main.py` | Reviews router added to FastAPI app |

## Previously Completed (Documentation Layer)
- [x] `core/orchestrator/TWO_LAYER_REVIEW.md` — Two-layer review workflow, signoff flow
- [x] `core/orchestrator/handoff/REVIEW_CHECKLIST.md` — Updated with L1/L2 checklists
- [x] `core/orchestrator/handoff/REVIEW_CAPTURE.md` — Updated with L1/L2 sections

## Acceptance Criteria
- [x] High-risk tasks require reviewer signoff.
- [x] Reviewer assignment rules are documented and automated.
- [x] Review capture includes required fixes and follow-ups.
- [x] Risk assessment engine maps triggers to risk levels (none/low/medium/high/critical).
- [x] Reviewer assignment matrix matches change types to agent/human reviewers.
- [x] Signoff state machine enforces valid transitions (10 states, no skipping layers).
- [x] L1-only flow works for low-risk changes (auto-APPROVED when L2 not required).
- [x] L1+L2 flow works for high-risk changes (agent or human L2 reviewer).
- [x] Changes-requested flow returns to DRAFT for rework.
- [x] L1 escalation forces L2 requirement even when not originally needed.
- [x] Review records support tenant isolation.
- [x] API routes enforce scope-based permissions.

## Key Artifacts
- `engine/src/agent33/review/models.py` — Review data models
- `engine/src/agent33/review/risk.py` — Risk assessment engine
- `engine/src/agent33/review/assignment.py` — Reviewer assignment matrix
- `engine/src/agent33/review/state_machine.py` — Signoff state machine
- `engine/src/agent33/review/service.py` — Review lifecycle service
- `engine/src/agent33/api/routes/reviews.py` — REST API endpoints
- `engine/tests/test_phase15_review.py` — 65 comprehensive tests
- `core/orchestrator/TWO_LAYER_REVIEW.md` — Process documentation

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/reviews/` | Create review record |
| GET | `/v1/reviews/` | List reviews (tenant-filtered) |
| GET | `/v1/reviews/{id}` | Get review details |
| DELETE | `/v1/reviews/{id}` | Delete review |
| POST | `/v1/reviews/{id}/assess` | Run risk assessment |
| POST | `/v1/reviews/{id}/ready` | Mark ready for review |
| POST | `/v1/reviews/{id}/assign-l1` | Assign L1 reviewer |
| POST | `/v1/reviews/{id}/l1` | Submit L1 decision |
| POST | `/v1/reviews/{id}/assign-l2` | Assign L2 reviewer |
| POST | `/v1/reviews/{id}/l2` | Submit L2 decision |
| POST | `/v1/reviews/{id}/approve` | Record final signoff |
| POST | `/v1/reviews/{id}/merge` | Mark as merged |

## Dependencies
- Phase 14

## Blocks
- Phase 16
