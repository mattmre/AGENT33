# Walkthroughs

These walkthroughs assume:

- API is running at `http://localhost:8000`
- `TOKEN` is set (see `setup-guide.md`)

Example header used below:

```bash
-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json"
```

## 1. Agent Discovery and Invocation

List registered agents:

```bash
curl http://localhost:8000/v1/agents/ \
  -H "Authorization: Bearer $TOKEN"
```

Search by role:

```bash
curl "http://localhost:8000/v1/agents/search?role=orchestrator" \
  -H "Authorization: Bearer $TOKEN"
```

Invoke the orchestrator:

```bash
curl -X POST http://localhost:8000/v1/agents/orchestrator/invoke \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {
      "task": "Create a short rollout plan for adding cache metrics"
    },
    "model": "llama3.2",
    "temperature": 0.2
  }'
```

## 2. Workflow Registration and Execution

Register a minimal workflow:

```bash
curl -X POST http://localhost:8000/v1/workflows/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello-flow",
    "version": "1.0.0",
    "description": "simple workflow",
    "triggers": {"manual": true},
    "inputs": {
      "name": {"type": "string", "required": true}
    },
    "outputs": {
      "message": {"type": "string"}
    },
    "steps": [
      {
        "id": "build-message",
        "action": "transform",
        "inputs": {
          "template": {
            "message": "Hello {{ name }}"
          }
        }
      }
    ],
    "execution": {"mode": "sequential"}
  }'
```

Execute it:

```bash
curl -X POST http://localhost:8000/v1/workflows/hello-flow/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "inputs": {"name": "AGENT-33"}
  }'
```

## 3. Memory Search and Session Queries

Search progressive recall index:

```bash
curl -X POST http://localhost:8000/v1/memory/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"release checklist", "level":"index", "top_k":5}'
```

List buffered observations for a session:

```bash
curl http://localhost:8000/v1/memory/sessions/session-123/observations \
  -H "Authorization: Bearer $TOKEN"
```

Summarize a session:

```bash
curl -X POST http://localhost:8000/v1/memory/sessions/session-123/summarize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 4. Review Lifecycle (Two-Layer Signoff)

Create review:

```bash
curl -X POST http://localhost:8000/v1/reviews/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id":"TASK-101","branch":"feat/docs-refresh","pr_number":12}'
```

Assess risk:

```bash
curl -X POST http://localhost:8000/v1/reviews/<review_id>/assess \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"triggers":["api-public","security"]}'
```

Move to ready and assign L1:

```bash
curl -X POST http://localhost:8000/v1/reviews/<review_id>/ready -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:8000/v1/reviews/<review_id>/assign-l1 -H "Authorization: Bearer $TOKEN"
```

Submit L1 decision:

```bash
curl -X POST http://localhost:8000/v1/reviews/<review_id>/l1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"decision":"approved","issues":[],"comments":"L1 pass"}'
```

If L2 required, continue:

```bash
curl -X POST http://localhost:8000/v1/reviews/<review_id>/assign-l2 -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:8000/v1/reviews/<review_id>/l2 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"decision":"approved","issues":[],"comments":"L2 pass"}'
```

Finalize:

```bash
curl -X POST http://localhost:8000/v1/reviews/<review_id>/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approver_id":"release-manager","conditions":[]}'

curl -X POST http://localhost:8000/v1/reviews/<review_id>/merge \
  -H "Authorization: Bearer $TOKEN"
```

## 5. Evaluation Run and Regression Handling

Create run:

```bash
curl -X POST http://localhost:8000/v1/evaluations/runs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"gate":"G-PR","commit_hash":"abc123","branch":"main"}'
```

Submit task results:

```bash
curl -X POST http://localhost:8000/v1/evaluations/runs/<run_id>/results \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_results": [
      {"item_id":"GT-01","result":"pass","checks_passed":3,"checks_total":3,"duration_ms":1200}
    ],
    "rework_count": 0,
    "scope_violations": 0
  }'
```

Save baseline from completed run:

```bash
curl -X POST http://localhost:8000/v1/evaluations/runs/<run_id>/baseline \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"commit_hash":"abc123","branch":"main"}'
```

List regressions:

```bash
curl http://localhost:8000/v1/evaluations/regressions \
  -H "Authorization: Bearer $TOKEN"
```

## 6. Autonomy Budget Lifecycle

Create budget:

```bash
curl -X POST http://localhost:8000/v1/autonomy/budgets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id":"TASK-201",
    "agent_id":"AGT-003",
    "in_scope":["engine/src/**"],
    "out_of_scope":["infra/**"],
    "default_escalation_target":"orchestrator"
  }'
```

Activate and create runtime enforcer:

```bash
curl -X POST http://localhost:8000/v1/autonomy/budgets/<budget_id>/activate \
  -H "Authorization: Bearer $TOKEN"

curl -X POST http://localhost:8000/v1/autonomy/budgets/<budget_id>/enforcer \
  -H "Authorization: Bearer $TOKEN"
```

Run sample enforcement checks:

```bash
curl -X POST http://localhost:8000/v1/autonomy/budgets/<budget_id>/enforce/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command":"pytest -q"}'

curl -X POST http://localhost:8000/v1/autonomy/budgets/<budget_id>/escalate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Manual escalation for policy review","target":"director","urgency":"normal"}'
```

## 7. Release Lifecycle, Sync, and Rollback

Create release:

```bash
curl -X POST http://localhost:8000/v1/releases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"version":"1.4.0","release_type":"minor","description":"Feature bundle"}'
```

Move through lifecycle:

```bash
curl -X POST http://localhost:8000/v1/releases/<release_id>/freeze -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:8000/v1/releases/<release_id>/rc -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"rc_version":"1.4.0-rc1"}'
curl -X POST http://localhost:8000/v1/releases/<release_id>/validate -H "Authorization: Bearer $TOKEN"
```

If publish fails checklist validation, inspect checklist:

```bash
curl http://localhost:8000/v1/releases/<release_id>/checklist \
  -H "Authorization: Bearer $TOKEN"
```

Create sync rule and dry-run:

```bash
curl -X POST http://localhost:8000/v1/releases/sync/rules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source_pattern":"core/**/*.md",
    "target_repo":"example/downstream",
    "target_path":"docs",
    "strategy":"copy",
    "frequency":"manual"
  }'

curl -X POST http://localhost:8000/v1/releases/sync/rules/<rule_id>/dry-run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"available_files":["core/README.md"],"release_version":"1.4.0"}'
```

## 8. Improvement Intake and Lessons

Submit intake:

```bash
curl -X POST http://localhost:8000/v1/improvements/intakes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Need workflow action routing",
    "summary":"Route action should dispatch by model capability",
    "source":"internal-review",
    "submitted_by":"platform-team",
    "research_type":"technical",
    "urgency":"high",
    "priority_score":8
  }'
```

Transition intake:

```bash
curl -X POST http://localhost:8000/v1/improvements/intakes/<intake_id>/transition \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"new_status":"triaged","decision_by":"director"}'
```

Record lesson:

```bash
curl -X POST http://localhost:8000/v1/improvements/lessons \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recorded_by":"qa-agent",
    "phase":"phase-18",
    "event_type":"observation",
    "what_happened":"auth scopes were missing in one route",
    "insight":"scope checks must be enforced in every route",
    "recommendation":"add route-level scope checklist"
  }'
```

## 9. Trace and Failure Capture

Start trace:

```bash
curl -X POST http://localhost:8000/v1/traces/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_id":"TASK-301","session_id":"session-301","agent_id":"AGT-001","agent_role":"orchestrator"}'
```

Add action:

```bash
curl -X POST http://localhost:8000/v1/traces/<trace_id>/actions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"step_id":"step-1","action_id":"act-1","tool":"shell","input_data":"pytest -q","output_data":"ok","duration_ms":850,"status":"success"}'
```

Complete trace:

```bash
curl -X POST http://localhost:8000/v1/traces/<trace_id>/complete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"completed"}'
```

## 10. Workflow Graph Visualization (Phase 25)

Get visual graph representation of a workflow:

```bash
curl http://localhost:8000/v1/visualizations/workflows/hello-flow/graph \
  -H "Authorization: Bearer $TOKEN"
```

Response includes nodes, edges, layout coordinates, and execution status overlay:

```json
{
  "workflow_id": "hello-flow",
  "workflow_version": "1.0.0",
  "nodes": [
    {
      "id": "build-message",
      "name": "build-message",
      "action": "transform",
      "x": 80,
      "y": 80,
      "position": {"x": 80, "y": 80},
      "metadata": {
        "inputs": {...},
        "outputs": {...}
      },
      "status": "success"
    }
  ],
  "edges": [],
  "layout": {
    "type": "layered",
    "width": 280,
    "height": 280,
    "layer_spacing": 200,
    "node_spacing": 150
  },
  "metadata": {
    "generated_at": "2026-02-17T...",
    "step_count": 1,
    "execution_mode": "sequential"
  }
}
```

### Using the Frontend Workflow Graph View

1. Navigate to `http://localhost:3000` and login with bootstrap credentials
2. Select the **Workflows** domain from the sidebar
3. Choose **Workflow Graph** operation
4. Enter the workflow ID (e.g., `hello-flow`) in the path parameter field
5. Click **Run** to fetch and render the graph
6. Use the interactive controls:
   - **Zoom**: Mouse wheel or zoom controls
   - **Pan**: Click and drag on the canvas
   - **Node details**: Click any node to view inputs, outputs, status, and metadata
   - **Deselect**: Click on empty canvas to hide detail sidebar

The graph view is useful for:
- Debugging workflow execution paths and dependencies
- Identifying failed steps visually with status indicators
- Understanding complex workflow structures without manual trace correlation
- Sharing workflow architecture diagrams with non-technical stakeholders
