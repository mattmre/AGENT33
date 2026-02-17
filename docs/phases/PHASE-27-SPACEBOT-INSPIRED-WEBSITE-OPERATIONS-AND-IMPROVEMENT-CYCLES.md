# Phase 27: Spacebot-Inspired Website Operations and Improvement Cycles

## Status: Discovery Complete

**Discovery Branch**: `phase27/discovery-spacebot-mapping`  
**Gap Analysis**: `docs/research/phase27-spacebot-website-gap-analysis.md`  
**Progress Log**: `docs/progress/phase-27-spacebot-inspired-website-log.md`

## Overview
- **Phase**: 27 of 27+
- **Category**: Product / Multi-User Agent UX
- **Primary Goal**: Add Spacebot-inspired website functionality to AGENT-33 (concurrent operations, operator control surfaces, and rich agent process visibility) while preserving AGENT-33 core values around ingesting research, driving improvement, and supporting human-style improvement cycles.

## Objectives
- Deliver a website operations hub that makes channel/branch/worker style execution visible and operable.
- Support concurrent long-running work without blocking operator interaction flows.
- Preserve and elevate AGENT-33's research intake and continuous improvement loops as first-class website workflows.
- Introduce guided human improvement cycle workflows (`observe -> research -> decide -> execute -> review -> improve`) backed by existing orchestration and governance patterns.
- Keep all new UX and APIs multi-tenant, auth-aware, and policy-enforced.

## Scope

### In Scope
- Website experience patterns inspired by Spacebot's concurrent process model, adapted to AGENT-33 architecture.
- Backend contracts for operations state, task delegation, and process/event status views.
- Frontend modules for operations hub navigation, active work tracking, and improvement-cycle workflow entry points.
- Integration with AGENT-33 research intake, lessons learned, and improvement tracking.
- Documentation and tests for new website surfaces and API contracts.

### Out of Scope
- Rewriting AGENT-33 runtime to match Spacebot internals one-to-one.
- Dropping or bypassing AGENT-33 governance, tenancy, or security constraints.
- Full parity with every external Spacebot feature in a single phase.
- Replacing existing workflow engine primitives that already satisfy AGENT-33 requirements.

## Staged Implementation Plan

**Stage 1: Backend Aggregation + Basic Hub** (Week 1)
- Goal: Prove backend contracts and surface active work in a single view
- Backend aggregation service and `/v1/operations/hub` endpoint
- Aggregates running traces, active budgets, pending improvements, recent workflows
- Unit tests and auth enforcement validation

**Stage 2: Concurrent Operations UI + Control Surfaces** (Week 2)
- Goal: Deliver frontend operations hub with drill-down and lifecycle controls
- Frontend operations hub module with process list, detail sidebar, control panel
- Polling-based status updates (<2s interval)
- Map autonomy budgets → "channels", parallel groups → "worker pools", traces → "tasks"

**Stage 3: Guided Improvement-Cycle Flows** (Week 3)
- Goal: Introduce explicit human-style improvement workflow UX
- Improvement-cycle workflow templates (observe → decide → execute → review → improve)
- Frontend improvement-cycle wizard integrated with operations hub
- Improvement metrics dashboard widget

**Reference**: See `docs/research/phase27-spacebot-website-gap-analysis.md` for detailed stage specifications, API schemas, and risk mitigations.

## Deliverables

| # | Deliverable | Target Path | Description | Stage |
|---|-------------|-------------|-------------|-------|
| 1 | Spacebot-to-AGENT-33 capability map | `docs/research/phase27-spacebot-website-gap-analysis.md` | Map inspired features to AGENT-33-equivalent architecture and identify gaps | ✅ Discovery |
| 2 | Operations hub API routes | `engine/src/agent33/api/routes/operations_hub.py` | Authenticated endpoints for active processes, delegation state, and lifecycle actions | Stage 1 |
| 3 | Operations orchestration service | `engine/src/agent33/services/operations_hub.py` | Normalized process state aggregation and website-friendly response shaping | Stage 1 |
| 4 | Frontend operations hub module | `frontend/src/features/operations-hub/` | UI for concurrent process visibility, delegation traces, and operator controls | Stage 2 |
| 5 | Improvement cycle UI flows | `frontend/src/features/improvement-cycle/` | Guided workflows for research-driven, human-style continuous improvement loops | Stage 3 |
| 6 | Improvement-cycle workflow templates | `core/workflows/improvement-cycle/` | Reusable workflow templates mirroring human improvement cadence | Stage 3 |
| 7 | Backend tests | `engine/tests/test_operations_hub_api.py` | API and service tests for visibility and lifecycle interactions | Stage 1 |
| 8 | Frontend tests | `frontend/src/features/operations-hub/*.test.tsx` | View-model and interaction tests for operations and improvement-cycle flows | Stage 2-3 |
| 9 | Operator walkthrough updates | `docs/walkthroughs.md` | How to run website workflows for ingestion, research, and iterative improvement | Stage 3 |
| 10 | Progress evidence log | `docs/progress/phase-27-spacebot-inspired-website-log.md` | Validation commands, screenshots, and rollout notes | ✅ Discovery (ongoing) |

## Acceptance Criteria
- [ ] Operators can view concurrent active processes and their status transitions from the website.
- [ ] Operators can inspect delegation lineage (request -> branch/worker execution -> result).
- [ ] Website workflows support non-blocking long tasks while preserving responsive UI interaction.
- [ ] Improvement cycle workflow (`observe -> research -> decide -> execute -> review -> improve`) is executable end-to-end.
- [ ] Research intake and lessons-learned paths remain first-class and are not regressed by the new UX.
- [ ] Existing AGENT-33 multi-tenant auth boundaries and policy checks apply to all new routes.
- [ ] Backend and frontend tests pass for all new operations-hub and improvement-cycle surfaces.
- [ ] Operator docs include concrete workflows and troubleshooting guidance.
- [ ] Metrics capture includes cycle completion, review turnaround, and improvement adoption signals.
- [ ] Phase validates incremental delivery without forcing broad runtime rewrites.

## Dependencies
- Phase 20 (continuous improvement and research intake primitives)
- Phase 22 (frontend platform and access layer)
- Phase 25 (visual workflow context for operational comprehension)
- Phase 26 (decision/review page primitives and explainability artifacts)
- Phase 18 (autonomy and policy enforcement for new lifecycle actions)

## Blocks
- Future advanced collaboration and external sharing capabilities, if introduced in later phases.

## Orchestration Guidance

### Discovery Phase (✅ Complete)
1. **Capability mapping**:
   - ✅ Spacebot-to-AGENT-33 capability mapping table created
   - ✅ Gap analysis identifies 80%+ existing backend primitives
   - ✅ Non-negotiable constraints documented (research intake, improvement tracking first-class)
2. **Staged implementation plan**:
   - ✅ Three-stage rollout defined (backend → frontend UI → improvement-cycle UX)
   - ✅ API surface proposal with schemas and endpoints
   - ✅ Risk assessment with mitigations
   - ✅ Success metrics defined

### Implementation Phases (Planned)

**Stage 1: Backend Aggregation** (Week 1)
1. Implement `operations_hub.py` service:
   - Aggregate from traces, budgets, improvements, workflows
   - Filter by recency (default 24h) and status
   - Implement pagination (max 100 processes)
2. Create `/v1/operations/hub` API route:
   - Auth enforcement (`workflows:read` scope)
   - Query params: `include`, `since`, `status`
   - Return normalized process list
3. Add supporting endpoints:
   - `GET /v1/operations/processes/{id}` - unified detail view
   - `POST /v1/operations/processes/{id}/control` - lifecycle actions
4. Write unit tests and validate auth boundaries

**Stage 2: Frontend Operations Hub** (Week 2)
1. Create `features/operations-hub/` module:
   - `OperationsHubPage.tsx` - main dashboard
   - `ProcessDetailSidebar.tsx` - drill-down view
   - `ProcessControlPanel.tsx` - pause/resume/cancel controls
2. Implement polling refresh (<2s interval, exponential backoff)
3. Map AGENT-33 concepts to Spacebot-inspired UX:
   - Autonomy budget → "Channel"
   - Workflow parallel group → "Worker Pool"
   - Trace → "Active Task"
4. Add delegation lineage visualization from trace actions
5. Write frontend tests for interactions

**Stage 3: Improvement-Cycle Flows** (Week 3)
1. Create improvement-cycle workflow templates:
   - `observe-decide-execute.yaml`
   - `review-improve.yaml`
2. Build `features/improvement-cycle/` wizard:
   - Multi-step form: Observe → Research → Decide → Execute → Review → Improve
   - Link to research intake, triage, lesson capture, checklist completion
3. Integrate improvement metrics widget into operations hub
4. Add "Start Improvement Cycle" button to operations hub
5. Validate end-to-end cycle completion
6. Update operator walkthroughs

## Review Checklist

### Discovery Phase
- [x] Capability map reviewed for architectural fit and scope discipline.
- [x] Gap analysis confirms 80%+ existing backend primitives reusable.
- [x] Non-negotiable constraints documented and accepted.
- [x] Staged implementation plan defined with clear acceptance criteria per stage.
- [x] API surface proposal includes schemas and auth enforcement strategy.
- [x] Risk assessment completed with mitigations for all identified risks.

### Stage 1 (Backend Aggregation)
- [ ] Operations hub service aggregates from all required subsystems.
- [ ] API routes enforce auth scopes and multi-tenant filtering.
- [ ] Unit tests achieve >90% coverage for aggregation logic.
- [ ] Performance validated: <1s response for typical active process counts (<50).

### Stage 2 (Frontend Operations Hub)
- [ ] Operations hub dashboard renders process list with correct status.
- [ ] Process detail sidebar shows delegation lineage and action history.
- [ ] Control panel pause/resume/cancel actions trigger correct backend APIs.
- [ ] Polling refresh works without memory leaks or excessive API load.
- [ ] Frontend tests pass for all interaction flows.

### Stage 3 (Improvement-Cycle Flows)
- [ ] Improvement-cycle workflow templates validate and execute end-to-end.
- [ ] Improvement-cycle wizard guides operators through full cycle.
- [ ] Improvement metrics visible in operations hub dashboard.
- [ ] Research intake and improvement tracking not regressed.
- [ ] Operator walkthroughs include improvement-cycle examples with screenshots.

## Non-Negotiable Constraints

Phase 27 implementation **must** preserve:

1. **Research intake remains first-class**: Any new UX surfaces research intake submission and status tracking prominently
2. **Improvement tracking is not regressed**: Lessons learned, checklists, and metrics endpoints are used by the operations hub, not bypassed
3. **Governance boundaries are enforced**: All new operations hub routes respect auth scopes, autonomy budget limits, and policy checks
4. **Multi-tenant safety is preserved**: Operations hub state is filtered by user identity and tenant context
5. **No runtime rewrites**: We do not replace AGENT-33's workflow engine or trace collector to match Spacebot internals one-to-one
6. **Incremental delivery**: Each stage delivers operator-validatable value without requiring all three stages to complete

## Success Metrics

Phase 27 is successful if:

1. **Operations hub delivers value**: Operators report >30% faster debugging of concurrent work (measure: time to identify stuck process)
2. **Research intake not regressed**: Improvement intake submission rate ≥ Phase 20 baseline (5+ items/quarter)
3. **Improvement cycle adoption**: ≥3 improvement cycles completed end-to-end via wizard in first month post-launch
4. **No governance bypasses**: 100% of operations hub control actions pass auth/policy checks in audit logs
5. **Performance acceptable**: Operations hub page load <1s for typical active process counts (<50 processes)
6. **Operator satisfaction**: Post-phase survey shows ≥70% prefer operations hub over terminal-only workflows

## References
- **Gap Analysis**: `docs/research/phase27-spacebot-website-gap-analysis.md` ⭐ Start here for detailed capability mapping, API schemas, and risk mitigations
- **Progress Log**: `docs/progress/phase-27-spacebot-inspired-website-log.md`
- Spacebot reference: https://github.com/spacedriveapp/spacebot
- Phase 20 spec: `docs/phases/PHASE-20-CONTINUOUS-IMPROVEMENT-AND-RESEARCH-INTAKE.md`
- Phase 22 spec: `docs/phases/PHASE-22-UNIFIED-UI-PLATFORM-AND-ACCESS-LAYER.md`
- Phase 25 spec: `docs/phases/PHASE-25-VISUAL-EXPLAINER-INTEGRATION.md`
- Phase 26 spec: `docs/phases/PHASE-26-VISUAL-EXPLAINER-DECISION-AND-REVIEW-PAGES.md`
