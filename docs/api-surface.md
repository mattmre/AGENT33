# API Surface

Source of truth:
- Route modules in `engine/src/agent33/api/routes/`
- Auth middleware in `engine/src/agent33/security/middleware.py`
- Scope checks in `engine/src/agent33/security/permissions.py`

## 1. Authentication Rules

Public (no auth required):
- `GET /health`
- `GET /health/channels`
- `POST /v1/auth/token`
- `GET /v1/dashboard/`
- `GET /v1/dashboard/metrics`
- `GET /v1/dashboard/lineage/{workflow_id}`
- `/docs`, `/redoc`, `/openapi.json`

All other endpoints require authentication (`Bearer` JWT or `X-API-Key`).

Defined scopes:
- `admin`
- `agents:read`
- `agents:write`
- `agents:invoke`
- `workflows:read`
- `workflows:write`
- `workflows:execute`
- `tools:execute`

## 2. Endpoint Map by Domain

### Health

| Method | Path | Scope |
| --- | --- | --- |
| GET | `/health` | Public |
| GET | `/health/channels` | Public |

### Auth

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/auth/token` | Public |
| POST | `/v1/auth/api-keys` | `admin` |
| DELETE | `/v1/auth/api-keys/{key_id}` | Authenticated (ownership/admin logic in handler) |

### Chat

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/chat/completions` | Authenticated |

### Agents

| Method | Path | Scope |
| --- | --- | --- |
| GET | `/v1/agents/capabilities/catalog` | Authenticated |
| GET | `/v1/agents/search` | `agents:read` |
| GET | `/v1/agents/by-id/{agent_id}` | `agents:read` |
| GET | `/v1/agents/` | `agents:read` |
| GET | `/v1/agents/{name}` | `agents:read` |
| POST | `/v1/agents/` | `agents:write` |
| POST | `/v1/agents/{name}/invoke` | `agents:invoke` |

### Workflows

| Method | Path | Scope |
| --- | --- | --- |
| GET | `/v1/workflows/` | `workflows:read` |
| GET | `/v1/workflows/{name}` | `workflows:read` |
| POST | `/v1/workflows/` | `workflows:write` |
| POST | `/v1/workflows/{name}/execute` | `workflows:execute` |

### Memory

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/memory/search` | `agents:read` |
| GET | `/v1/memory/sessions/{session_id}/observations` | `agents:read` |
| POST | `/v1/memory/sessions/{session_id}/summarize` | `agents:write` |

### Reviews

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/reviews/` | `workflows:write` |
| GET | `/v1/reviews/` | `workflows:read` |
| GET | `/v1/reviews/{review_id}` | `workflows:read` |
| DELETE | `/v1/reviews/{review_id}` | `workflows:write` |
| POST | `/v1/reviews/{review_id}/assess` | `workflows:write` |
| POST | `/v1/reviews/{review_id}/ready` | `workflows:write` |
| POST | `/v1/reviews/{review_id}/assign-l1` | `workflows:write` |
| POST | `/v1/reviews/{review_id}/l1` | `workflows:write` |
| POST | `/v1/reviews/{review_id}/assign-l2` | `workflows:write` |
| POST | `/v1/reviews/{review_id}/l2` | `workflows:write` |
| POST | `/v1/reviews/{review_id}/approve` | `workflows:write` |
| POST | `/v1/reviews/{review_id}/merge` | `workflows:write` |

### Traces

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/traces/` | `tools:execute` |
| GET | `/v1/traces/` | `workflows:read` |
| GET | `/v1/traces/{trace_id}` | `workflows:read` |
| POST | `/v1/traces/{trace_id}/actions` | `tools:execute` |
| POST | `/v1/traces/{trace_id}/complete` | `tools:execute` |
| POST | `/v1/traces/{trace_id}/failures` | `tools:execute` |
| GET | `/v1/traces/{trace_id}/failures` | `workflows:read` |

### Evaluations

| Method | Path | Scope |
| --- | --- | --- |
| GET | `/v1/evaluations/golden-tasks` | `workflows:read` |
| GET | `/v1/evaluations/golden-cases` | `workflows:read` |
| GET | `/v1/evaluations/gates/{gate}/tasks` | `workflows:read` |
| POST | `/v1/evaluations/runs` | `tools:execute` |
| GET | `/v1/evaluations/runs` | `workflows:read` |
| GET | `/v1/evaluations/runs/{run_id}` | `workflows:read` |
| POST | `/v1/evaluations/runs/{run_id}/results` | `tools:execute` |
| POST | `/v1/evaluations/runs/{run_id}/baseline` | `tools:execute` |
| GET | `/v1/evaluations/baselines` | `workflows:read` |
| GET | `/v1/evaluations/regressions` | `workflows:read` |
| PATCH | `/v1/evaluations/regressions/{regression_id}/triage` | `tools:execute` |
| POST | `/v1/evaluations/regressions/{regression_id}/resolve` | `tools:execute` |

### Autonomy

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/autonomy/budgets` | `tools:execute` |
| GET | `/v1/autonomy/budgets` | `workflows:read` |
| GET | `/v1/autonomy/budgets/{budget_id}` | `workflows:read` |
| DELETE | `/v1/autonomy/budgets/{budget_id}` | `tools:execute` |
| POST | `/v1/autonomy/budgets/{budget_id}/transition` | `tools:execute` |
| POST | `/v1/autonomy/budgets/{budget_id}/activate` | `tools:execute` |
| POST | `/v1/autonomy/budgets/{budget_id}/suspend` | `tools:execute` |
| POST | `/v1/autonomy/budgets/{budget_id}/complete` | `tools:execute` |
| GET | `/v1/autonomy/budgets/{budget_id}/preflight` | `workflows:read` |
| POST | `/v1/autonomy/budgets/{budget_id}/enforcer` | `tools:execute` |
| POST | `/v1/autonomy/budgets/{budget_id}/enforce/file` | `tools:execute` |
| POST | `/v1/autonomy/budgets/{budget_id}/enforce/command` | `tools:execute` |
| POST | `/v1/autonomy/budgets/{budget_id}/enforce/network` | `tools:execute` |
| GET | `/v1/autonomy/escalations` | `workflows:read` |
| POST | `/v1/autonomy/budgets/{budget_id}/escalate` | `tools:execute` |
| POST | `/v1/autonomy/escalations/{escalation_id}/acknowledge` | `tools:execute` |
| POST | `/v1/autonomy/escalations/{escalation_id}/resolve` | `tools:execute` |

### Releases

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/releases` | `tools:execute` |
| GET | `/v1/releases` | `workflows:read` |
| GET | `/v1/releases/{release_id}` | `workflows:read` |
| POST | `/v1/releases/{release_id}/freeze` | `tools:execute` |
| POST | `/v1/releases/{release_id}/rc` | `tools:execute` |
| POST | `/v1/releases/{release_id}/validate` | `tools:execute` |
| POST | `/v1/releases/{release_id}/publish` | `tools:execute` |
| GET | `/v1/releases/{release_id}/checklist` | `workflows:read` |
| PATCH | `/v1/releases/{release_id}/checklist` | `tools:execute` |
| POST | `/v1/releases/sync/rules` | `tools:execute` |
| GET | `/v1/releases/sync/rules` | `workflows:read` |
| POST | `/v1/releases/sync/rules/{rule_id}/dry-run` | `tools:execute` |
| POST | `/v1/releases/sync/rules/{rule_id}/execute` | `tools:execute` |
| POST | `/v1/releases/{release_id}/rollback` | `tools:execute` |
| GET | `/v1/releases/rollbacks` | `workflows:read` |
| POST | `/v1/releases/rollback/recommend` | `workflows:read` |

### Improvements

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/improvements/intakes` | Authenticated |
| GET | `/v1/improvements/intakes` | Authenticated |
| GET | `/v1/improvements/intakes/{intake_id}` | Authenticated |
| POST | `/v1/improvements/intakes/{intake_id}/transition` | Authenticated |
| POST | `/v1/improvements/lessons` | Authenticated |
| GET | `/v1/improvements/lessons` | Authenticated |
| GET | `/v1/improvements/lessons/{lesson_id}` | Authenticated |
| POST | `/v1/improvements/lessons/{lesson_id}/complete-action` | Authenticated |
| POST | `/v1/improvements/lessons/{lesson_id}/verify` | Authenticated |
| POST | `/v1/improvements/checklists` | Authenticated |
| GET | `/v1/improvements/checklists` | Authenticated |
| GET | `/v1/improvements/checklists/{checklist_id}` | Authenticated |
| POST | `/v1/improvements/checklists/{checklist_id}/complete` | Authenticated |
| GET | `/v1/improvements/checklists/{checklist_id}/evaluate` | Authenticated |
| GET | `/v1/improvements/metrics` | Authenticated |
| GET | `/v1/improvements/metrics/history` | Authenticated |
| POST | `/v1/improvements/metrics/snapshot` | Authenticated |
| POST | `/v1/improvements/metrics/default-snapshot` | Authenticated |
| GET | `/v1/improvements/metrics/trend/{metric_id}` | Authenticated |
| POST | `/v1/improvements/refreshes` | Authenticated |
| GET | `/v1/improvements/refreshes` | Authenticated |
| GET | `/v1/improvements/refreshes/{refresh_id}` | Authenticated |
| POST | `/v1/improvements/refreshes/{refresh_id}/complete` | Authenticated |

### Dashboard

| Method | Path | Scope |
| --- | --- | --- |
| GET | `/v1/dashboard/` | Public |
| GET | `/v1/dashboard/metrics` | Public |
| GET | `/v1/dashboard/lineage/{workflow_id}` | Public |

### Training

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/training/{agent}/rollout` | Authenticated |
| POST | `/v1/training/{agent}/optimize` | Authenticated |
| GET | `/v1/training/{agent}/rollouts` | Authenticated |
| GET | `/v1/training/{agent}/metrics` | Authenticated |
| POST | `/v1/training/{agent}/revert` | Authenticated |

### Webhooks

| Method | Path | Scope |
| --- | --- | --- |
| POST | `/v1/webhooks/telegram` | Authenticated |
| POST | `/v1/webhooks/discord` | Authenticated |
| POST | `/v1/webhooks/slack` | Authenticated |
| GET | `/v1/webhooks/whatsapp` | Authenticated |
| POST | `/v1/webhooks/whatsapp` | Authenticated |

## 3. Notes

- A route being "Authenticated" without scope checks means middleware auth is required, but endpoint-level role/scope enforcement is not currently added.
- The API key delete route enforces ownership/admin logic in handler code rather than route dependency scope.
