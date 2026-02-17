# Phase 27: Spacebot Website Gap Analysis

**Date**: 2026-02-17  
**Phase**: 27 of 27+  
**Status**: Discovery  
**Reference**: [Spacebot GitHub](https://github.com/spacedriveapp/spacebot)

## Executive Summary

This analysis maps Spacebot-inspired interaction patterns to AGENT33's existing architecture to deliver an operations hub and improvement-cycle UX. The goal is to introduce concurrent operations visibility, operator control surfaces, and rich agent process monitoring **without rewriting AGENT33's governance foundation or dropping research intake and improvement tracking as first-class concerns**.

**Key Finding**: AGENT33 already has 80%+ of the necessary backend primitives (traces, workflows, autonomy budgets, improvement intake). The gap is primarily in **frontend orchestration** for concurrent operations monitoring and **explicit improvement-cycle workflow UX** patterns.

**Recommendation**: Implement in three staged slices (Stage 1: backend aggregation + basic hub; Stage 2: concurrent operations UI; Stage 3: guided improvement-cycle flows) to validate operator value incrementally.

---

## Capability Mapping Table

| Spacebot Pattern | AGENT33 Existing Equivalent | Gap | Recommendation |
|------------------|----------------------------|-----|----------------|
| **Concurrent process/task tracking** | Trace lifecycle (`/v1/traces/*`), workflow execution | No unified "operations hub" view aggregating active work | **Stage 1**: Create `/v1/operations/hub` aggregator pulling from traces, workflows, budgets |
| **Worker/channel execution model** | Autonomy budgets, workflow parallel groups | No explicit channel/worker visualization | **Stage 2**: Map budget → "channel", parallel group → "worker pool" in frontend |
| **Operator control surfaces** | Workflow `execute`, trace `complete`, budget `suspend` | Missing unified "pause/resume/cancel" interface | **Stage 2**: Add operations hub controls wrapping existing lifecycle APIs |
| **Real-time status updates** | Polling-based (Phase 25 MVP pattern) | No WebSocket/SSE infrastructure | **Stage 2**: Use polling (<2s); defer WebSockets to post-Phase-27 |
| **Task delegation lineage** | Trace actions, workflow step history | No "request → branch → worker → result" UI flow | **Stage 2**: Build delegation trace view from existing observability data |
| **Research intake** | Improvement intakes (`/v1/improvements/intakes/*`) | ✅ Already first-class | **Stage 3**: Ensure operations hub links to intake submission |
| **Improvement tracking** | Lessons learned, checklists, metrics (`/v1/improvements/*`) | ✅ Already first-class | **Stage 3**: Surface improvement metrics in operations hub dashboard |
| **Human improvement cycles** | Research intake → triage → lessons learned loop | No guided "observe → decide → execute → review → improve" UX | **Stage 3**: Create improvement-cycle workflow templates + frontend wizard |
| **Multi-agent coordination** | Workflow parallel groups, agent invoke chains | No coordination map visualization | ⚠️ Out of scope Phase 27; deferred to future phase |

---

## Explicit Non-Negotiable Constraints

1. **Research intake remains first-class**: Any new UX **must** surface research intake submission and status tracking prominently.
2. **Improvement tracking is not regressed**: Lessons learned, checklists, and metrics endpoints are used by the operations hub, not bypassed.
3. **Governance boundaries are enforced**: All new operations hub routes respect auth scopes, autonomy budget limits, and policy checks.
4. **Multi-tenant safety is preserved**: Operations hub state is filtered by user identity and tenant context.
5. **No runtime rewrites**: We do not replace AGENT33's workflow engine or trace collector to match Spacebot internals one-to-one.
6. **Incremental delivery**: Each stage delivers operator-validatable value without requiring all three stages to complete.

---

## Staged Implementation Slices

### Stage 1: Backend Aggregation + Basic Hub (Week 1)

**Goal**: Prove backend contracts and surface active work in a single view.

**Deliverables**:
- `engine/src/agent33/api/routes/operations_hub.py`: New route module
- `engine/src/agent33/services/operations_hub.py`: Aggregation service
- Endpoint: `GET /v1/operations/hub` → returns normalized active processes JSON
- Aggregates from:
  - Running traces (`state="running"`)
  - Active autonomy budgets (`state="active"`)
  - Pending improvements (`status="analyzing"`)
  - Recent workflow executions (last 24h)

**Acceptance**:
- `/v1/operations/hub` returns 200 with process list
- Unit tests pass for aggregation logic
- Auth middleware enforces `workflows:read` scope

**Evidence Required**:
- `curl` output showing aggregated response
- Test coverage report

### Stage 2: Concurrent Operations UI + Control Surfaces (Week 2)

**Goal**: Deliver frontend operations hub with drill-down and lifecycle controls.

**Deliverables**:
- `frontend/src/features/operations-hub/`: React module
  - `OperationsHubPage.tsx`: Main view with process list
  - `ProcessDetailSidebar.tsx`: Drill-down for trace/budget/workflow
  - `ProcessControlPanel.tsx`: Pause/resume/cancel buttons
- `frontend/src/data/domains/operations.ts`: Domain operations
- Polling refresh (<2s interval) for status updates
- Map concepts:
  - Autonomy budget → "Channel"
  - Workflow parallel group → "Worker Pool"
  - Trace → "Active Task"

**Acceptance**:
- Operators can view all active processes in a single dashboard
- Clicking a process shows detail sidebar with lineage
- Control buttons (pause/resume/cancel) trigger correct backend lifecycle APIs
- Polling updates status without page reload

**Evidence Required**:
- Screenshots of operations hub with active processes
- Video of pause/resume interaction
- Frontend test results

### Stage 3: Guided Improvement-Cycle Flows (Week 3)

**Goal**: Introduce explicit human-style improvement workflow UX.

**Deliverables**:
- `core/workflows/improvement-cycle/`: Workflow templates
  - `observe-decide-execute.yaml`: Research intake → analysis → decision
  - `review-improve.yaml`: Lesson capture → verification → metric update
- `frontend/src/features/improvement-cycle/`: React module
  - `ImprovementCycleWizard.tsx`: Multi-step form
  - Stages: Observe (intake submission) → Research (analysis view) → Decide (triage action) → Execute (lesson capture) → Review (verification) → Improve (checklist update)
- Operations hub link: "Start Improvement Cycle" button
- Improvement metrics widget in operations hub dashboard

**Acceptance**:
- Operators can start improvement cycle from operations hub
- Wizard guides through intake → triage → lesson → checklist flow
- Improvement metrics visible in operations hub dashboard
- Workflow templates validate and execute end-to-end

**Evidence Required**:
- Improvement-cycle workflow execution logs
- Metrics dashboard screenshot showing cycle completion
- Walkthrough documentation with operator steps

---

## Proposed API Surface for Operations Hub

### Core Endpoint

**`GET /v1/operations/hub`**

Query Parameters:
- `include` (optional): CSV list of `traces,budgets,workflows,improvements`
- `since` (optional): ISO timestamp for recency filter (default: 24h)
- `status` (optional): Filter by state (`running`, `active`, `pending`)

Response Schema:
```json
{
  "timestamp": "2026-02-18T12:34:56Z",
  "active_count": 12,
  "processes": [
    {
      "id": "trace-abc123",
      "type": "trace",
      "status": "running",
      "started_at": "2026-02-18T10:00:00Z",
      "name": "PR Review Workflow",
      "metadata": {
        "workflow_id": "review-automation",
        "step_count": 5,
        "current_step": 3
      }
    },
    {
      "id": "budget-xyz789",
      "type": "autonomy_budget",
      "status": "active",
      "started_at": "2026-02-18T09:30:00Z",
      "name": "Release RC Generation",
      "metadata": {
        "file_operations_used": 12,
        "file_operations_limit": 50,
        "escalations": 0
      }
    },
    {
      "id": "intake-def456",
      "type": "improvement_intake",
      "status": "analyzing",
      "started_at": "2026-02-17T16:00:00Z",
      "name": "Improve evaluation latency",
      "metadata": {
        "research_type": "performance",
        "urgency": "medium"
      }
    }
  ]
}
```

### Supporting Endpoints

**`GET /v1/operations/processes/{process_id}`**

Unified detail view for any process type (traces, budgets, improvements).

Response includes:
- Full lifecycle state
- Delegation lineage (if applicable)
- Action history
- Related artifacts (logs, traces, reviews)

**`POST /v1/operations/processes/{process_id}/control`**

Unified lifecycle action interface.

Request Body:
```json
{
  "action": "pause" | "resume" | "cancel",
  "reason": "Operator override for debugging"
}
```

Routes to appropriate backend API:
- Trace: `/v1/traces/{id}/complete` (for cancel)
- Budget: `/v1/autonomy/budgets/{id}/suspend` (for pause)
- Workflow: (future: add pause/resume to workflow engine)

---

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Aggregation latency** | Operations hub slow with many active processes | Medium | Implement pagination (max 100 processes), add caching layer, index by recency |
| **Polling overhead** | High refresh rate causes API load | Low | Use exponential backoff if no changes detected, max 1 request per 2s |
| **Unified control interface complexity** | Different process types need different lifecycle APIs | High | Create adapter layer in `operations_hub.py` that translates control actions to type-specific calls |
| **Improvement-cycle workflow adoption** | Operators ignore wizard and use direct API calls | Medium | Make wizard faster than manual workflow, integrate into operations hub prominently |
| **Scope creep into multi-agent coordination** | Attempt to build full Spacebot coordination maps | Medium | Defer to future phase, document explicitly as out-of-scope for Phase 27 |
| **Auth scope conflicts** | New routes bypass existing policy checks | Low | Reuse `/v1/workflows/` and `/v1/improvements/` auth patterns, add explicit scope checks in tests |
| **Frontend state management complexity** | Operations hub state diverges from backend | Medium | Use polling refresh, avoid client-side caching beyond 2s TTL, rely on backend as source of truth |

---

## Success Metrics

Phase 27 is successful if:

1. **Operations hub delivers value**: Operators report faster debugging of concurrent work (measure: time to identify stuck process reduces by >30%)
2. **Research intake not regressed**: Improvement intake submission rate ≥ Phase 20 baseline (5+ items/quarter)
3. **Improvement cycle adoption**: ≥3 improvement cycles completed end-to-end via wizard in first month post-launch
4. **No governance bypasses**: 100% of operations hub control actions pass auth/policy checks in audit logs
5. **Performance acceptable**: Operations hub page load <1s for typical active process counts (<50 processes)
6. **Operator satisfaction**: Post-phase survey shows ≥70% prefer operations hub over terminal-only workflows

---

## Next Steps (Post-Discovery)

1. **Architect**: Review and approve this gap analysis
2. **Implementer**: Begin Stage 1 backend aggregation
3. **QA**: Define acceptance test scenarios for each stage
4. **Documentation**: Prepare walkthrough outlines for operations hub and improvement-cycle wizard
5. **Orchestrator**: Schedule stage checkpoints and validation reviews

---

## References

- Spacebot GitHub: https://github.com/spacedriveapp/spacebot
- Phase 27 Spec: `docs/phases/PHASE-27-SPACEBOT-INSPIRED-WEBSITE-OPERATIONS-AND-IMPROVEMENT-CYCLES.md`
- Phase 20 (Improvement Primitives): `docs/phases/PHASE-20-CONTINUOUS-IMPROVEMENT-AND-RESEARCH-INTAKE.md`
- Phase 22 (UI Platform): `docs/phases/PHASE-22-UNIFIED-UI-PLATFORM-AND-ACCESS-LAYER.md`
- AGENT33 API Surface: `docs/api-surface.md`
- Functionality Map: `docs/functionality-and-workflows.md`
