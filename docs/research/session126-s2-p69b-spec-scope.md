# Session 126 S2 — P69b Spec Scope

Prepared: 2026-04-11
Branch: session126-s2-p69b-spec
Slice: POST-4.1 (P69b UX Spec + API Contract)

---

## 1. Research Findings

### 1.1 Existing Autonomy Enforcement Layer

`engine/src/agent33/autonomy/` implements a complete budget-lifecycle state machine:

**BudgetState** (`models.py`): `DRAFT → PENDING_APPROVAL → ACTIVE → SUSPENDED / EXPIRED / COMPLETED / REJECTED`

The `RuntimeEnforcer` (`enforcement.py`) enforces 8 runtime enforcement points (EF-01 through EF-08) covering file reads/writes, command execution, network, iteration count, duration, files modified, and lines changed. All enforcement is synchronous and in-process; there is no existing pause/resume mechanism at the invocation level.

The `AutonomyService` (`service.py`) orchestrates CRUD, lifecycle transitions, preflight (PF-01 through PF-10), and enforcement. It persists state to an `OrchestrationStateStore` (namespace-based KV). The `snapshot_state()` / `restore_state()` pattern on `RuntimeEnforcer` already serialises full enforcement context — this is the natural place to snapshot state when pausing a P69b invocation.

**Key insight**: The existing system's `require_approval_commands` list on `AutonomyBudget` is the closest precursor to P69b. Currently, `EnforcementResult.WARNED` is returned for approval-required commands, but there is no DB-backed pause record, no API surface for operators to act on, and no timeout/nonce system. P69b fills exactly that gap.

### 1.2 Existing Tool Approval Layer

`engine/src/agent33/tools/approvals.py` already has:
- `ApprovalStatus`: `PENDING | APPROVED | REJECTED | CONSUMED | EXPIRED`
- `ToolApprovalRequest`: in-memory record with `expires_at`, `reviewed_by`, `reviewed_at`
- `ToolApprovalService`: in-memory service with optional durable KV backing

`engine/src/agent33/tools/governance.py` integrates `ToolApprovalService` with `ApprovalTokenManager`. The `_try_consume_approval()` method already validates `__approval_token` parameters using HMAC-based `ApprovalTokenManager` from `agent33.security.approval_tokens`.

**Key insight**: The existing approval token manager provides a partial HMAC token pattern but it is not keyed to `(run_id, tool_name, timestamp_window)`. P69b introduces a stronger, invocation-scoped nonce scheme backed by a dedicated `PausedInvocation` DB record rather than the in-memory `ToolApprovalService`.

### 1.3 Existing State Machine

`engine/src/agent33/workflows/state_machine.py` implements an XState-inspired `StateMachine` with `StateNode`, `Transition`, guard functions, entry/exit actions, and `HistoryState` (deep/shallow). The `send(event)` → `state_transition` structlog pattern is the logging convention P69b will follow.

### 1.4 Tool Governance Policy Model

`governance.py` implements tool policies as a dict of `"tool_name" → "allow|deny|ask"` with wildcard support (exact, pattern, global `*`). The `ask` policy already routes to `ToolApprovalService.request()`. P69b extends this flow: instead of in-memory approval records, it persists a `PausedInvocation` row, halts execution, and streams an SSE event to the operator dashboard.

### 1.5 Execution Models

`engine/src/agent33/execution/models.py` defines `ExecutionContract` (with `execution_id`, `tool_id`, `inputs`, `sandbox`, `metadata`) and `ExecutionResult`. P69b's `PausedInvocation` DB record is a sibling to `ExecutionContract` at the invocation level, not the contract level.

---

## 2. Session 122 Locked Decisions

The following architectural decisions were locked in Session 122 and are binding for this spec:

| Decision | Value |
|----------|-------|
| Pause storage | `PausedInvocation` as a DB record (not mutable in-memory flag) |
| Headless mode env var | `AGENT33_HEADLESS_TOOL_APPROVAL=approve\|deny`, default `deny` |
| HMAC nonce formula | `HMAC-SHA256(f"{run_id}:{tool_name}:{floor(timestamp/30)}", tenant_secret)` |
| Feature flag name | `p69b_tool_approval_enabled` |
| Kill switch path | `/tmp/agent33_disable_p69b` |
| Approval timeout | Default 5 minutes, configurable per tenant |
| Notification channel | SSE event emitted to operator dashboard |

---

## 3. Deliverables

### 3.1 P69b UX Spec (`session126-p69b-ux-spec.md`)

Covers operator-facing experience end-to-end:
- Feature overview and lifecycle fit
- Trigger conditions (per-tool, per-tenant, per-autonomy-budget-threshold)
- Pause state: what the system does when pausing (DB write, SSE emit, execution halt, state preservation)
- User-facing invocation states: `RUNNING → PAUSED_FOR_APPROVAL → RUNNING | FAILED`
- Approval flows: interactive, timeout, batch
- Headless mode: env var semantics, CI use, default-deny rationale
- Replay protection: why nonces matter, HMAC formula, 30-second window
- Feature flag lifecycle: enable/disable, kill switch, monitoring
- Error states: all named error codes

### 3.2 P69b API Contract (`session126-p69b-api-contract.md`)

Covers the machine-readable interface:
- 4 REST endpoints with full request/response schemas
- State machine ASCII diagram
- `PausedInvocation` DB model field definitions
- Complete error taxonomy (5 error codes)
- Full HMAC nonce specification with examples

### 3.3 Open Architectural Questions

The following questions arose during research that may need follow-up in POST-4.3 (implementation):

1. **Invocation model**: The spec references `invocation_id` and `run_id` but the engine's current `ExecutionContract` uses `execution_id`. POST-4.3 will need to clarify whether `invocation_id == execution_id` or whether there is a parent run record above the contract level.

2. **SSE event schema**: The pause notification is specified to emit an SSE event, but the SSE event schema is the subject of POST-4.2. POST-4.3 must depend on POST-4.2's schema before implementing the notification path.

3. **Tenant secret storage**: The HMAC nonce uses `tenant_secret`. The current engine has a JWT/API-key auth layer (`security/`) but no explicit `tenant_secret` field in the tenant model. POST-4.3 will need to define where this secret is stored and rotated.

4. **Concurrency**: If multiple tool calls within a single invocation all require approval simultaneously (e.g., a parallel group step), P69b must define whether they generate one `PausedInvocation` record per tool call or a grouped record. The current spec assumes one record per tool call; POST-4.3 should confirm this.
