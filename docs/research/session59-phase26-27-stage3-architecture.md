# Session 59 -- Phase 26 Stage 3 + Phase 27 Stage 3: Combined Architecture

**Date:** 2026-03-10
**Scope:** Improvement-Cycle Wizard approval flows, diff-review UI, and workflow template wiring
**Status:** Research / design -- no code changes

---

## 1. Executive Summary

Phase 26 Stage 3 adds interactive plan/diff approval flows and a step-by-step
improvement-cycle creation wizard. Phase 27 Stage 3 wires canonical workflow
templates into the frontend wizard so operators can select a template, fill
parameters, preview, and execute -- with live status tracking via the existing
SSE transport.

The two stages share a single frontend feature (`improvement-cycle`) and
overlap on API surfaces (workflows, reviews, explanations, tool approvals).
This document defines the combined architecture across backend endpoints,
frontend components, data flow, and test strategy.

---

## 2. Existing Inventory

### 2.1 Backend (engine/)

| Subsystem | Key Files | Current State |
|---|---|---|
| Improvement service | `improvement/service.py`, `improvement/models.py` | Full lifecycle: intakes, lessons, checklists, metrics, refreshes, learning signals. 30+ API endpoints under `/v1/improvements/`. |
| Workflow engine | `workflows/definition.py`, `workflows/executor.py`, `workflows/events.py` | DAG-based execution with topological sort, step retries, expression evaluator. Registry + execution history in-memory. |
| Workflow routes | `api/routes/workflows.py` | CRUD (`POST /`, `GET /{name}`), execution (`POST /{name}/execute`), scheduling, history. |
| Workflow SSE | `api/routes/workflow_sse.py` | `GET /v1/workflows/{run_id}/events` -- authenticated SSE stream with heartbeat, sync event on connect. |
| Workflow WS | `api/routes/workflow_ws.py`, `workflows/ws_manager.py` | WebSocket manager with run registration, ownership checks, event broadcasting. |
| Reviews | `api/routes/reviews.py`, `review/service.py` | Two-layer signoff: create, assess risk, ready, L1, L2, approve, merge. State machine: DRAFT -> READY -> L1_REVIEW -> L2_REVIEW -> APPROVED -> MERGED. |
| Explanations | `api/routes/explanations.py`, `explanation/renderer.py` | `POST /v1/explanations/plan-review`, `POST /v1/explanations/diff-review`, `POST /v1/explanations/project-recap`. Returns HTML content. |
| Tool approvals | `api/routes/tool_approvals.py` | `GET /v1/approvals/tools`, `POST /v1/approvals/tools/{id}/decision`. Pending/approved/rejected lifecycle. |

### 2.2 Frontend (frontend/src/)

| Component / Module | File | Current State |
|---|---|---|
| ImprovementCycleWizard | `features/improvement-cycle/ImprovementCycleWizard.tsx` | 4-card wizard: (1) Artifact generation, (2) Review draft + risk, (3) Signoff (L1/L2/approve/merge), (4) Tool approvals. Fully wired to backend APIs. Tests in `.test.tsx`. |
| Presets | `features/improvement-cycle/presets.ts` | Two canonical presets (`retrospective`, `metrics-review`) loaded from YAML via Vite `?raw` import. Exports `buildWorkflowCreatePresetBody()` and `buildWorkflowExecutePreset()`. |
| Workflow YAML parser | `features/improvement-cycle/workflowYaml.ts` | Custom pure-TS YAML parser (no external dependency). Handles scalars, objects, arrays, block scalars. |
| WorkflowGraph | `components/WorkflowGraph.tsx` | ReactFlow-based DAG visualization with status-aware node colors, edge animation, polling. Uses `WorkflowStatusNode`. |
| ExplanationView | `components/ExplanationView.tsx` | Sandboxed iframe for HTML content, plain-text fallback. |
| Live transport | `lib/workflowLiveTransport.ts` | Authenticated SSE fetch-stream client for `/v1/workflows/{run_id}/events`. |
| Domain configs | `data/domains/improvements.ts`, `data/domains/workflows.ts` | 30 improvement operations, 8 workflow operations. Workflows domain includes `presetBinding` on create and execute operations. |
| Types | `types/index.ts` | `WorkflowPresetDefinition`, `WorkflowExecutePresetProjection`, `OperationPresetBinding`, `WorkflowLiveEvent`, `WorkflowLiveTransportConnection`. |

### 2.3 Workflow Templates (core/)

| Template | File | Steps |
|---|---|---|
| Retrospective | `core/workflows/improvement-cycle/retrospective.workflow.yaml` | validate -> collect -> summarize (3 steps, dependency-aware) |
| Metrics Review | `core/workflows/improvement-cycle/metrics-review.workflow.yaml` | validate -> collect -> summarize (3 steps, dependency-aware) |

---

## 3. Phase 26 Stage 3: Improvement-Cycle Approval Flows

### 3.1 Interactive Plan-Review Approval Flow

**Current state:** The wizard generates an artifact (plan or diff review) and
creates a linked review, but approval decisions are button-clicks with no
structured feedback loop.

**Stage 3 additions:**

#### 3.1.1 Approval Decision Model

Add a structured approval decision that captures the operator's intent beyond
a simple accept/reject:

```
ApprovalDecision:
  decision: "approved" | "changes_requested" | "escalated" | "deferred"
  rationale: string           # why this decision
  conditions: string[]        # conditional approval terms
  modification_summary: string  # if changes_requested, what changed
  linked_intake_id?: string   # optionally link to a research intake
```

**Backend endpoint (new):**

```
POST /v1/reviews/{review_id}/approve-with-rationale
```

Request body extends the existing `ApproveRequest` with `rationale` and
`modification_summary` fields. The review service records these on the
`final_signoff` model.

**Why a new endpoint rather than modifying `/approve`:** Backward compatibility.
The existing `/approve` endpoint is consumed by automated pipelines that do not
supply rationale. The new endpoint is additive.

#### 3.1.2 Approval Flow State Machine Extension

The existing review state machine (DRAFT -> READY -> L1_REVIEW -> L2_REVIEW ->
APPROVED -> MERGED) gains two optional transitions:

```
APPROVED -> CHANGES_REQUESTED  (when operator requests modifications)
CHANGES_REQUESTED -> READY     (when author addresses changes)
APPROVED -> DEFERRED           (when operator defers decision)
DEFERRED -> READY              (when revisited)
```

These transitions are additive. Existing terminal states (MERGED, REJECTED) are
unchanged.

#### 3.1.3 Frontend: Approval Decision Panel

Add a fifth card to the wizard (between current card 3 "Signoff" and card 4
"Tool Approvals"):

**Card 3.5: Approval Decision**

- Dropdown: decision type (approved / changes_requested / escalated / deferred)
- Textarea: rationale (required for non-approved decisions)
- Textarea: modification summary (visible only for `changes_requested`)
- Textarea: conditions (comma-separated, converted to array)
- Optional: "Link to intake" autocomplete (calls `GET /v1/improvements/intakes`)
- Submit button: calls the new approval endpoint

The card is enabled only when the review state is `APPROVED` (i.e., after the
existing signoff flow completes) or when the operator has `admin` scope.

### 3.2 Diff-Review UI

**Current state:** The wizard supports generating diff-review artifacts via
`POST /v1/explanations/diff-review`, and the resulting HTML is rendered in a
sandboxed iframe (`ExplanationView`). However, there is no structured diff
display -- the backend renders a single HTML blob.

**Stage 3 additions:**

#### 3.2.1 Structured Diff Display Component

Create `DiffReviewPanel.tsx` in `features/improvement-cycle/`:

```
DiffReviewPanel
  props:
    artifact: ExplanationArtifact
    onAcceptHunk?: (hunkIndex: number) => void
    onRejectHunk?: (hunkIndex: number) => void
```

Behavior:
- If the artifact content is HTML (detected by `isHtmlContent()`), render via
  `ExplanationView` (existing sandboxed iframe) as the primary display.
- Below the iframe, render a structured comment/annotation panel where the
  operator can add line-level or section-level comments.
- Comments are persisted as review artifacts via `POST /v1/reviews/{id}/assess`
  with a new `comments` field on the risk assessment body (extending
  `AssessRiskRequest`).

#### 3.2.2 Diff Content Parsing (Optional Enhancement)

If the diff artifact content contains unified-diff markers (`@@`, `---`,
`+++`), parse them client-side into hunk structures for per-hunk
accept/reject. This is an enhancement beyond the base iframe display.

Hunk data model:

```ts
interface DiffHunk {
  index: number;
  header: string;       // @@ line
  oldStart: number;
  newStart: number;
  lines: DiffLine[];
  decision: "pending" | "accepted" | "rejected";
}
```

This stays client-side only -- hunk decisions are rolled up into the approval
decision's `modification_summary`.

### 3.3 Step-by-Step Wizard for Improvement Cycle Creation

**Current state:** The wizard is a single-page 4-card layout. All cards are
visible simultaneously.

**Stage 3 additions:**

#### 3.3.1 Wizard Step Controller

Add a `WizardStepController` wrapper that:

1. Tracks the current step index (0-based).
2. Validates prerequisites before allowing forward navigation.
3. Renders a step indicator bar at the top.
4. Renders only the active card (with a summary of completed cards above it).

Step sequence:

| Step | Card | Prerequisites |
|---|---|---|
| 0 | Template Selection | None |
| 1 | Parameter Fill | Template selected |
| 2 | Artifact Preview | Parameters filled |
| 3 | Review & Risk | Artifact generated |
| 4 | Signoff | Review created |
| 5 | Approval Decision | Signoff complete |
| 6 | Tool Approvals | Any time (sidebar) |

The step controller exposes:

```ts
interface WizardStepState {
  currentStep: number;
  completedSteps: Set<number>;
  canAdvance: boolean;
  canGoBack: boolean;
  advance: () => void;
  goBack: () => void;
  jumpTo: (step: number) => void;  // only to completed steps
}
```

#### 3.3.2 Template Selection Step (Step 0 -- New)

Currently the preset dropdown is embedded in card 1. Stage 3 extracts it into
a dedicated first step:

- Grid of preset cards (currently 2: retrospective, metrics-review).
- Each card shows: label, description, source path, step count, input
  parameter names.
- Selecting a card highlights it and enables "Next".
- "Custom" option at the end allows the operator to paste raw JSON/YAML.

#### 3.3.3 Parameter Fill Step (Step 1 -- New)

Auto-generates a form from the selected template's `inputs` definition:

```ts
function buildParameterForm(
  inputs: Record<string, ParameterDef>
): FormField[]
```

Each `ParameterDef` maps to a form field:
- `type: "string"` -> text input
- `type: "array"` -> tag input (add/remove items)
- `type: "object"` -> JSON textarea
- `type: "integer"` -> number input
- `required: true` -> field validation

Default values from the preset's `executePreset.body.inputs` are pre-filled.

The parameter form data is stored in wizard state and used to construct the
workflow execution request body.

---

## 4. Phase 27 Stage 3: Workflow Template Wiring

### 4.1 Improvement-Cycle Workflow Template Definition

**Current state:** Two YAML templates exist at
`core/workflows/improvement-cycle/`. They are loaded via Vite `?raw` import
in `presets.ts` and parsed by `workflowYaml.ts`.

**Stage 3 additions:**

#### 4.1.1 Template Catalog Endpoint (New Backend)

Add a read-only endpoint that serves the canonical template catalog:

```
GET /v1/workflows/templates
```

Response:

```json
{
  "templates": [
    {
      "id": "improvement-cycle-retrospective",
      "name": "improvement-cycle-retrospective",
      "version": "1.0.0",
      "description": "Deterministic retrospective scaffold...",
      "source_path": "core/workflows/improvement-cycle/retrospective.workflow.yaml",
      "inputs": { ... },
      "step_count": 3,
      "tags": ["improvement-cycle", "retrospective", "template"]
    }
  ]
}
```

Implementation: A `TemplateCatalog` service that scans
`core/workflows/improvement-cycle/` at startup and loads definitions via
`WorkflowDefinition.load_from_file()`. The catalog is read-only and
refreshable via:

```
POST /v1/workflows/templates/refresh
```

This endpoint is idempotent -- it re-scans the directory and updates the
in-memory catalog.

File: `engine/src/agent33/api/routes/workflow_templates.py`

#### 4.1.2 Template Schema Endpoint

For the parameter-fill step, the frontend needs the input schema:

```
GET /v1/workflows/templates/{template_id}/schema
```

Response:

```json
{
  "template_id": "improvement-cycle-retrospective",
  "inputs": {
    "session_id": {
      "type": "string",
      "description": "Session or milestone identifier being reviewed.",
      "required": true,
      "default": null
    },
    "scope": {
      "type": "string",
      "description": "Area or stream being reviewed.",
      "required": false,
      "default": "full-delivery"
    }
  },
  "outputs": { ... }
}
```

This is derived from the `WorkflowDefinition.inputs` and `.outputs` already
parsed by the YAML loader.

### 4.2 Frontend Wizard to Backend Workflow Execution Wiring

#### 4.2.1 Execution Flow

The wizard's submit action performs a two-phase operation:

**Phase A: Register the workflow (if not already registered)**

```
POST /v1/workflows/
Body: <full workflow definition from template>
```

If the workflow already exists (409 Conflict), skip to Phase B.

**Phase B: Execute the workflow**

```
POST /v1/workflows/{name}/execute
Body: {
  inputs: <filled parameters from wizard step 1>,
  run_id: <optional caller-supplied ID for tracking>
}
```

This two-phase approach already exists in the current wizard (`handleApplyPreset`
creates the workflow, and execute is a separate action). Stage 3 combines them
into a single submit action with automatic conflict handling.

#### 4.2.2 Execution Response Handling

On successful execution, the wizard:

1. Captures `run_id` from the response.
2. Connects the SSE live transport (`connectWorkflowLiveTransport`) using the
   run_id.
3. Transitions to the progress display step.
4. On receiving `workflow_completed` or `workflow_failed` events, transitions
   to the results step.

#### 4.2.3 Wire Diagram

```
[Template Selection]
       |
       v
[Parameter Fill] -- form auto-generated from template.inputs
       |
       v
[Preview] -- renders workflow YAML + filled params side-by-side
       |
       v
[Execute] -- POST /v1/workflows/ (register)
          -- POST /v1/workflows/{name}/execute (run)
       |
       v
[Progress] -- SSE stream via /v1/workflows/{run_id}/events
           -- WorkflowGraph visualization with live status updates
       |
       v
[Results] -- displays step results, generates explanation artifact
          -- transitions to approval flow (Phase 26)
```

### 4.3 Multi-Step Wizard UX

#### 4.3.1 Step Indicator Bar

A horizontal progress bar at the top of the wizard showing:

```
[Select Template] -> [Fill Parameters] -> [Preview] -> [Execute & Track] -> [Review & Approve]
```

Each step shows:
- Step number and title
- Status icon: pending (circle), active (filled circle), complete (check),
  error (X)
- Clickable only for completed steps (allows going back)

#### 4.3.2 Preview Step

The preview step renders:

1. **Template summary**: name, version, description, tags.
2. **Filled parameters**: key-value table with the operator's inputs.
3. **Workflow graph**: static `WorkflowGraph` rendering of the template's
   DAG structure (nodes from `steps`, edges from `depends_on`).
4. **Raw YAML**: collapsible code block showing the canonical template source.
5. **Execute button**: disabled if any required parameter is missing.

#### 4.3.3 Progress Display

Once execution starts, the wizard shows:

1. **Live workflow graph**: `WorkflowGraph` component connected to SSE events
   via `workflowLiveTransport`. Node statuses update in real-time (pending ->
   running -> completed/failed).
2. **Event log**: scrolling list of SSE events with timestamps.
3. **Duration counter**: elapsed time since execution started.
4. **Cancel button**: sends a signal to abort (if supported by the backend).

### 4.4 Status Tracking and Progress Display

#### 4.4.1 Workflow Run Tracker State

```ts
interface WorkflowRunState {
  runId: string;
  workflowName: string;
  status: "pending" | "running" | "completed" | "failed";
  startedAt: number;
  completedAt?: number;
  durationMs?: number;
  stepStatuses: Record<string, string>;
  events: WorkflowLiveEvent[];
  result?: Record<string, unknown>;
  error?: string;
}
```

The state is updated by the SSE event handler:

- `sync` event: initializes step statuses from the current run state.
- `step_started` / `step_completed` / `step_failed` / `step_skipped`: updates
  individual step status.
- `workflow_completed` / `workflow_failed`: sets terminal status, captures
  result or error, disconnects SSE.

#### 4.4.2 Graph Refresh Integration

The existing `WorkflowGraph` component already supports `onRefresh` polling.
For Stage 3, the SSE event handler replaces polling:

1. On receiving a graph-refresh event (`shouldRefreshWorkflowGraph()` returns
   true), update the graph data by calling
   `GET /v1/visualizations/workflows/{workflow_id}/graph` or by directly
   mapping `stepStatuses` onto the existing graph nodes.
2. The direct mapping approach is preferred (no additional API call):
   - Extract `step_id` and new status from the SSE event.
   - Update the corresponding node's `status` field in the `WorkflowGraphData`.
   - ReactFlow re-renders with the new status colors and edge animations.

---

## 5. Shared Concerns

### 5.1 Frontend Component Inventory

#### Existing Components (No Changes)

| Component | File | Role |
|---|---|---|
| ExplanationView | `components/ExplanationView.tsx` | HTML iframe rendering |
| WorkflowGraph | `components/WorkflowGraph.tsx` | ReactFlow DAG visualization |
| WorkflowStatusNode | `components/WorkflowStatusNode.tsx` | Custom ReactFlow node |
| OperationCard | `components/OperationCard.tsx` | Domain operation executor |
| DomainPanel | `components/DomainPanel.tsx` | Domain config browser |
| ObservationStream | `components/ObservationStream.tsx` | SSE stream UI (reference pattern) |

#### Modified Components

| Component | File | Changes |
|---|---|---|
| ImprovementCycleWizard | `features/improvement-cycle/ImprovementCycleWizard.tsx` | Refactor from flat 4-card layout to step-controlled wizard. Add approval decision card. Add progress/results steps. |
| presets.ts | `features/improvement-cycle/presets.ts` | Add optional catalog-fetch fallback alongside static YAML imports. |

#### New Components

| Component | File | Purpose |
|---|---|---|
| WizardStepController | `features/improvement-cycle/WizardStepController.tsx` | Step navigation, progress bar, prerequisite validation |
| TemplateSelectionStep | `features/improvement-cycle/steps/TemplateSelectionStep.tsx` | Grid of template cards for preset selection |
| ParameterFillStep | `features/improvement-cycle/steps/ParameterFillStep.tsx` | Auto-generated form from template input schema |
| PreviewStep | `features/improvement-cycle/steps/PreviewStep.tsx` | Template summary + filled params + static graph + raw YAML |
| ExecuteTrackStep | `features/improvement-cycle/steps/ExecuteTrackStep.tsx` | Execution trigger, SSE connection, live graph, event log |
| ApprovalDecisionStep | `features/improvement-cycle/steps/ApprovalDecisionStep.tsx` | Structured approval decision with rationale |
| DiffReviewPanel | `features/improvement-cycle/DiffReviewPanel.tsx` | Structured diff display with annotation |
| EventLog | `features/improvement-cycle/EventLog.tsx` | Scrolling SSE event log with timestamps |

### 5.2 API Endpoint Design

#### New Endpoints

| Method | Path | Purpose | Request Model |
|---|---|---|---|
| GET | `/v1/workflows/templates` | List canonical workflow templates | None (query: `tags`, `limit`) |
| GET | `/v1/workflows/templates/{template_id}/schema` | Get template input/output schema | None |
| POST | `/v1/workflows/templates/refresh` | Re-scan template directory | None |
| POST | `/v1/reviews/{review_id}/approve-with-rationale` | Structured approval with rationale | `ApproveWithRationaleRequest` |

#### New Backend Files

| File | Purpose |
|---|---|
| `engine/src/agent33/api/routes/workflow_templates.py` | Template catalog router |
| `engine/src/agent33/workflows/template_catalog.py` | Template discovery and caching |

#### Modified Endpoints (Optional)

| Method | Path | Change |
|---|---|---|
| POST | `/v1/reviews/{review_id}/assess` | Add optional `comments` field to `AssessRiskRequest` for diff annotations |

### 5.3 Backend Models

#### New Pydantic Models

```python
# In workflow_templates.py or a new templates module

class TemplateSummary(BaseModel):
    id: str
    name: str
    version: str
    description: str | None
    source_path: str
    inputs: dict[str, ParameterDef]
    outputs: dict[str, ParameterDef]
    step_count: int
    tags: list[str]

class TemplateSchema(BaseModel):
    template_id: str
    inputs: dict[str, ParameterDef]
    outputs: dict[str, ParameterDef]

class ApproveWithRationaleRequest(BaseModel):
    approver_id: str
    decision: str  # "approved" | "changes_requested" | "escalated" | "deferred"
    rationale: str = ""
    modification_summary: str = ""
    conditions: list[str] = Field(default_factory=list)
    linked_intake_id: str | None = None
```

### 5.4 Test Strategy

#### 5.4.1 Backend Tests

| Test File | Coverage Target |
|---|---|
| `tests/test_workflow_templates.py` | Template catalog: discovery, listing, schema endpoint, refresh idempotency, missing directory handling |
| `tests/test_review_approval_rationale.py` | Extended approval: rationale persistence, state transitions (APPROVED -> CHANGES_REQUESTED -> READY), deferred flow |
| `tests/test_workflow_templates_auth.py` | Auth: template endpoints require `workflows:read` scope, refresh requires `workflows:write` |

Each test must:
- Assert on actual response shapes (not just status codes).
- Test both success and error paths.
- Verify state transitions produce the expected model state.
- Use mock services where external dependencies exist.

#### 5.4.2 Frontend Tests

| Test File | Coverage Target |
|---|---|
| `features/improvement-cycle/WizardStepController.test.tsx` | Step navigation: forward/back, prerequisite gating, jump-to-completed |
| `features/improvement-cycle/steps/TemplateSelectionStep.test.tsx` | Preset card rendering, selection state, custom option |
| `features/improvement-cycle/steps/ParameterFillStep.test.tsx` | Auto-form generation for string/array/object/integer types, required validation, default pre-fill |
| `features/improvement-cycle/steps/ExecuteTrackStep.test.tsx` | Execution trigger (register + execute), SSE mock events updating graph state, terminal event handling |
| `features/improvement-cycle/steps/ApprovalDecisionStep.test.tsx` | Decision form rendering, rationale required for non-approved, API call shape verification |
| `features/improvement-cycle/DiffReviewPanel.test.tsx` | HTML content iframe rendering, annotation submission |

All frontend tests must use `@testing-library/react` with `userEvent` for
interaction simulation, consistent with the existing
`ImprovementCycleWizard.test.tsx` pattern.

### 5.5 File Layout

```
engine/src/agent33/
  api/routes/
    workflow_templates.py          # NEW: template catalog endpoints
  review/
    service.py                     # MODIFIED: approve_with_rationale method
    models.py                      # MODIFIED: extended signoff model
  workflows/
    template_catalog.py            # NEW: template discovery and caching

frontend/src/
  features/improvement-cycle/
    ImprovementCycleWizard.tsx      # MODIFIED: refactor to step-controlled layout
    ImprovementCycleWizard.test.tsx # MODIFIED: update for new step flow
    WizardStepController.tsx        # NEW: step navigation controller
    WizardStepController.test.tsx   # NEW
    DiffReviewPanel.tsx             # NEW: structured diff display
    DiffReviewPanel.test.tsx        # NEW
    EventLog.tsx                    # NEW: SSE event log
    presets.ts                      # MODIFIED: optional catalog fetch
    presets.test.ts                 # EXISTING: update for new behavior
    workflowYaml.ts                # EXISTING: no changes
    steps/
      TemplateSelectionStep.tsx     # NEW
      TemplateSelectionStep.test.tsx # NEW
      ParameterFillStep.tsx         # NEW
      ParameterFillStep.test.tsx    # NEW
      PreviewStep.tsx               # NEW
      ExecuteTrackStep.tsx          # NEW
      ExecuteTrackStep.test.tsx     # NEW
      ApprovalDecisionStep.tsx      # NEW
      ApprovalDecisionStep.test.tsx # NEW

core/workflows/improvement-cycle/
  retrospective.workflow.yaml      # EXISTING: no changes
  metrics-review.workflow.yaml     # EXISTING: no changes
```

---

## 6. Data Flow Diagrams

### 6.1 Complete Wizard Flow

```
Operator
  |
  v
[Step 0: Template Selection]
  |  reads: presets.ts (static) or GET /v1/workflows/templates (dynamic)
  v
[Step 1: Parameter Fill]
  |  reads: template.inputs schema
  |  writes: wizard state (filled params)
  v
[Step 2: Preview]
  |  reads: wizard state, template definition
  |  renders: WorkflowGraph (static), parameter table, raw YAML
  v
[Step 3: Execute & Track]
  |  calls: POST /v1/workflows/ (register, handles 409)
  |  calls: POST /v1/workflows/{name}/execute (run)
  |  connects: GET /v1/workflows/{run_id}/events (SSE)
  |  renders: WorkflowGraph (live), EventLog, duration
  v
[Step 4: Review & Signoff]
  |  calls: POST /v1/explanations/{mode} (generate artifact)
  |  calls: POST /v1/reviews/ (create review)
  |  calls: POST /v1/reviews/{id}/assess (risk)
  |  calls: POST /v1/reviews/{id}/ready, assign-l1, l1, assign-l2, l2
  v
[Step 5: Approval Decision]
  |  calls: POST /v1/reviews/{id}/approve-with-rationale
  |  optionally: POST /v1/improvements/intakes (link)
  v
[Sidebar: Tool Approvals]
     calls: GET /v1/approvals/tools
     calls: POST /v1/approvals/tools/{id}/decision
```

### 6.2 SSE Event Flow During Execution

```
Backend (WorkflowExecutor)
  |
  v
ws_manager.publish_event(WorkflowEvent)
  |
  v
SSE endpoint (/v1/workflows/{run_id}/events)
  |  formats: data: {json}\n\n
  v
workflowLiveTransport.ts (fetch stream reader)
  |  parses: SSE chunks
  v
onEvent callback
  |  checks: shouldRefreshWorkflowGraph(event)
  |  checks: isWorkflowTerminalEvent(event)
  v
ExecuteTrackStep state update
  |  updates: stepStatuses, events array, WorkflowGraphData
  v
WorkflowGraph re-render (ReactFlow)
  |  updates: node status colors, edge animations
```

---

## 7. Implementation Sequencing

### PR 1: Template Catalog Backend

**Scope:** `workflow_templates.py`, `template_catalog.py`, tests
**Estimated tests:** 15-20
**Dependencies:** None (purely additive backend)

Deliverables:
- `TemplateCatalog` class with directory scanning and definition loading
- Three endpoints: list, schema, refresh
- Wired into main app lifespan
- Full test coverage for discovery, listing, schema, refresh, error paths

### PR 2: Extended Review Approval

**Scope:** `review/service.py`, `review/models.py`, `reviews.py`, tests
**Estimated tests:** 10-15
**Dependencies:** None (purely additive backend)

Deliverables:
- `approve_with_rationale` method on `ReviewService`
- CHANGES_REQUESTED and DEFERRED state transitions
- New endpoint wired
- Test coverage for all new transitions and error paths

### PR 3: Wizard Step Controller + Template Selection + Parameter Fill

**Scope:** Frontend step controller, two new step components, modified wizard
**Estimated tests:** 20-25
**Dependencies:** PR 1 (for schema endpoint, or use static fallback)

Deliverables:
- `WizardStepController` with navigation logic
- `TemplateSelectionStep` with preset cards
- `ParameterFillStep` with auto-form generation
- Refactored `ImprovementCycleWizard` to use step controller
- Tests for all three components

### PR 4: Execute & Track + Preview + Progress Display

**Scope:** Frontend execution wiring, SSE integration, live graph
**Estimated tests:** 15-20
**Dependencies:** PR 3 (wizard step controller)

Deliverables:
- `PreviewStep` with static graph and parameter table
- `ExecuteTrackStep` with SSE connection and live graph updates
- `EventLog` component
- Graph status update from SSE events (direct mapping, no extra API call)
- Tests with mocked SSE events

### PR 5: Approval Decision Step + Diff Review Panel

**Scope:** Frontend approval flow, diff display
**Estimated tests:** 10-15
**Dependencies:** PR 2 (backend approval endpoint), PR 3 (wizard controller)

Deliverables:
- `ApprovalDecisionStep` with structured decision form
- `DiffReviewPanel` with annotation support
- Integration with existing review signoff flow
- Tests for decision form validation and API call shapes

---

## 8. Risk Assessment

| Risk | Impact | Mitigation |
|---|---|---|
| Template YAML parsing differences between frontend (custom parser) and backend (PyYAML) | Medium | Use backend schema endpoint as source of truth for parameter forms; frontend parser only used for preview rendering |
| SSE connection drops during long-running workflows | Medium | Existing heartbeat mechanism in `workflow_sse.py`; add reconnection logic in `workflowLiveTransport.ts` |
| Review state machine complexity with new transitions | Low | New transitions are additive and guarded by explicit status checks in service layer |
| Frontend test infrastructure dependency on `@testing-library/react` | Low | Already established in `ImprovementCycleWizard.test.tsx` |
| Template directory not mounted in Docker builds | Medium | Template catalog should handle missing directory gracefully (empty catalog, not crash) |

---

## 9. Open Questions

1. **Template versioning:** Should the template catalog support multiple
   versions of the same template, or is latest-only sufficient? Current
   recommendation: latest-only, with the YAML `version` field as metadata.

2. **Custom templates:** Should operators be able to upload custom workflow
   templates via the wizard, or only use the canonical ones from
   `core/workflows/`? Current recommendation: canonical-only for Stage 3,
   with a "paste raw YAML/JSON" escape hatch already present in Step 0.

3. **Approval notification:** Should the approval decision trigger a
   notification (NATS event, webhook)? Current recommendation: yes, via the
   existing NATS messaging bus, but this is a follow-up concern.

4. **Workflow cancellation:** The progress display shows a cancel button, but
   the backend does not currently support mid-execution cancellation. This
   is out of scope for Stage 3 -- the button should be labeled "Close" and
   disconnect the SSE stream without canceling the backend execution.
