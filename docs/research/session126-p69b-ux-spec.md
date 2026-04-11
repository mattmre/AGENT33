# P69b Tool Approval — UX Specification

**Document**: POST-4.1 UX Spec
**Slice**: S2 (P69b Spec)
**Branch**: session126-s2-p69b-spec
**Prepared**: 2026-04-11
**Status**: Draft — authoritative for POST-4.3 implementation

---

## 1. Overview

### 1.1 What P69b Is

P69b (Tool Approval Gate) introduces human-in-the-loop (HITL) oversight for agent tool calls. When an agent invocation reaches a tool call that requires operator approval, the system pauses execution, persists a `PausedInvocation` record to the database, and streams a `tool_approval_required` SSE event to the operator dashboard. Execution halts until an operator approves or denies the pending call, or until the configurable timeout elapses.

P69b does not block all tool calls — only those that match one or more trigger conditions (see Section 2). Approved calls execute normally; denied calls terminate the invocation with a structured error.

### 1.2 Why P69b Exists

The existing autonomy enforcement layer (`engine/src/agent33/autonomy/`) enforces per-budget runtime limits (file reads/writes, commands, network, duration, etc.) but has no mechanism for an operator to review and approve a specific tool call before it executes. The existing `ToolApprovalService` in `engine/src/agent33/tools/approvals.py` provides an in-memory approval record but has no DB persistence, no API surface for operators to act on, no timeout, and no replay protection.

P69b fills this gap by:

- Persisting a `PausedInvocation` DB record (instead of an ephemeral in-memory flag) so approval state survives process restarts.
- Providing four REST API endpoints operators and CI systems can call to inspect, approve, or deny pending tool calls.
- Streaming `tool_approval_required` SSE events so operator dashboards receive real-time notification without polling.
- Defining a deterministic HMAC nonce scheme to prevent replay attacks across approval requests.

### 1.3 How P69b Fits the Agent Invocation Lifecycle

The invocation lifecycle with P69b enabled is:

```
Agent receives task
        │
        ▼
  Tool call selected
        │
        ▼
  Trigger check ──── not flagged ──► tool executes normally
        │
      flagged
        │
        ▼
  snapshot_state()          ← preserves RuntimeEnforcer enforcement context
        │
        ▼
  Write PausedInvocation    ← DB record: pending status, nonce, expires_at
        │
        ▼
  Emit SSE event            ← tool_approval_required to operator dashboard
        │
        ▼
  Halt execution            ← invocation enters PAUSED_FOR_APPROVAL state
        │
        ▼
  Operator acts ──── approve ──► restore_state() → tool executes → RUNNING
                └── deny    ──► ToolApprovalDenied → FAILED
                └── timeout ──► ToolApprovalTimeout → FAILED
```

P69b sits at the boundary between the tool governance layer (`tools/governance.py`) and the execution layer (`execution/executor.py`). The governance layer's existing `ask` policy (per `"tool_name" → "allow|deny|ask"`) is the entry point. P69b replaces the in-memory `ToolApprovalService.request()` call with a DB-backed pause+notify flow.

---

## 2. Trigger Conditions

An incoming tool call is flagged for approval if **any one** of the following conditions is met. Conditions are evaluated in order; the first match wins.

### 2.1 Per-Tool Governance Policy (`ask`)

The tool governance policy map (dict of `tool_name → allow|deny|ask`) assigns an `ask` policy to specific tools. Wildcard patterns (exact, glob, and global `*`) are supported per the existing governance policy model.

Examples:
- `"shell_exec": "ask"` — any shell execution requires approval.
- `"file_write_*": "ask"` — all file-write tool variants require approval.
- `"*": "ask"` — all tool calls require approval (maximum oversight mode).

### 2.2 Per-Tenant Autonomy Budget Threshold

An `AutonomyBudget` record can declare a list of `require_approval_commands`. When a tool call matches any command name in this list, it is flagged regardless of the governance policy map. This allows tenant-level overrides without modifying the global policy.

Additionally, when the RuntimeEnforcer detects that an enforcement point (EF-01 through EF-08) is within a configured warning threshold of its budget limit — for example, 80% of the allowed file-write budget consumed — a tenant can opt in to require approval for all subsequent calls in that category until the operator explicitly resumes.

### 2.3 Destructive Tool Flag

Individual tool definitions can carry a `requires_approval: true` metadata flag in their JSON schema definition or SKILL.md frontmatter. Tools flagged this way always require approval regardless of governance policy or budget state. This flag is intended for tools whose side effects are irreversible (e.g., `delete_database`, `send_email`, `deploy_to_production`).

---

## 3. Pause State Mechanics

### 3.1 What Happens When Execution Pauses

When a tool call is flagged for approval, the system executes the following steps atomically before halting execution:

**Step 1 — Snapshot invocation state**

The `RuntimeEnforcer.snapshot_state()` method (already implemented in `engine/src/agent33/autonomy/enforcement.py`) serialises the full enforcement context — budget counters, stop conditions, accumulated file paths, command history — into a JSON blob. This blob is stored alongside the `PausedInvocation` record so that `restore_state()` can resume enforcement exactly where it left off if the call is approved.

**Step 2 — Compute HMAC nonce**

A deterministic nonce is computed for this (run_id, tool_name, timestamp_window) tuple (see Section 7 for the full formula). The nonce uniquely identifies this approval request within its 30-second window and is used to detect replay attacks.

**Step 3 — Write PausedInvocation DB record**

A `PausedInvocation` record is inserted with `status = pending`, `tool_name`, `tool_input` (JSONB), the computed `nonce`, `created_at = now()`, and `expires_at = now() + timeout_seconds`. All fields include `tenant_id` for row-level isolation.

**Step 4 — Emit SSE event**

A `tool_approval_required` SSE event is emitted to the operator dashboard channel for the tenant. The event payload includes `approval_id`, `invocation_id`, `tool_name`, a truncated `tool_input` preview, `expires_at`, and `nonce`. The full SSE event schema is defined in POST-4.2 (SSE event schema versioning).

**Step 5 — Halt tool execution**

The tool call is not executed. The invocation coroutine suspends and waits for one of three outcomes: operator approval via `POST /resume`, operator denial via `POST /resume`, or timeout.

### 3.2 State Preservation Guarantee

Because `snapshot_state()` captures the full enforcement context and the `PausedInvocation` DB record persists across process restarts, the pause state is durable. If the engine process restarts while an approval is pending, the invocation can be resumed (approved or denied) via the API and the enforcement context restored from the snapshot.

This durability guarantee is why `PausedInvocation` is a DB record and not an in-memory flag — a process restart would otherwise lose all pending approvals.

### 3.3 Execution Isolation During Pause

While an invocation is in `PAUSED_FOR_APPROVAL` state:

- No further tool calls in the invocation are dispatched.
- The `RuntimeEnforcer` enforcement budget is frozen (counters do not accumulate).
- Other invocations for the same tenant are unaffected.
- The invocation's workflow DAG step is marked as blocked, preventing downstream steps from starting.

---

## 4. User-Facing Invocation States

P69b adds one new invocation state to the lifecycle:

| State | Description |
|-------|-------------|
| `RUNNING` | Invocation is executing normally. Tool calls that do not require approval proceed without interruption. |
| `PAUSED_FOR_APPROVAL` | Invocation has encountered a tool call requiring operator approval. Execution is halted. A `PausedInvocation` record exists with `status = pending`. The operator must act before `expires_at`. |
| `RUNNING` (resumed) | Operator approved the tool call. `restore_state()` has been called. The tool call is executing or has completed. Invocation continues normally. |
| `FAILED` | The invocation failed due to one of: approval denied by operator (`ToolApprovalDenied`), approval timeout (`ToolApprovalTimeout`), or any other terminal error. |

### 4.1 State Transition Diagram

```
RUNNING
  │
  │  tool call flagged for approval
  ▼
PAUSED_FOR_APPROVAL
  │    │    │
  │    │    └─── timeout elapsed (expires_at) ──────────► FAILED
  │    │                                              (ToolApprovalTimeout)
  │    │
  │    └─── POST /resume  approved=false ──────────────► FAILED
  │                                                  (ToolApprovalDenied)
  │
  └─── POST /resume  approved=true ────────────────────► RUNNING
                                                     (tool executes, continues)
```

---

## 5. Approval Flows

### 5.1 Interactive Approval

An operator reviewing a pending approval sees:

**Tool name**: The exact name of the tool being called (e.g., `shell_exec`, `file_write`).

**Tool input preview**: A truncated, syntax-highlighted view of the tool's input arguments. Truncation limit is 2,048 characters; the full input is available via `GET /v1/invocations/{id}/pending-approvals`. Sensitive fields (passwords, tokens, keys) are redacted using the existing redaction layer from `agent33.security`.

**Context**: Invocation ID, agent name, workflow step name (if applicable), timestamp of the paused call, time remaining until timeout.

**Actions**: Two buttons — Approve and Deny. Both require the operator's identity to be authenticated (Bearer token with `agents:write` scope). The operator's identity (`approved_by`) is recorded in the `PausedInvocation.approved_by` field for audit.

Clicking Approve sends `POST /v1/invocations/{id}/resume` with `approved=true`. Clicking Deny sends the same endpoint with `approved=false`.

### 5.2 Timeout Flow

The approval timeout is configurable per tenant (stored on the `AutonomyBudget` or tenant config). The system default is **5 minutes** (300 seconds).

If `expires_at` elapses without an operator action:

1. A background job (scheduled at the configured poll interval) marks the `PausedInvocation.status` as `expired`.
2. The waiting invocation receives a `ToolApprovalTimeout` error.
3. The invocation transitions to `FAILED`.
4. An SSE `tool_approval_expired` event is emitted to the operator dashboard.
5. `PausedInvocation.resolved_at` is set to the expiry timestamp; `approved_by` remains null.

Operators who attempt to act on an expired approval receive a `410 Gone` response.

### 5.3 Batch Approval

Operators can approve or deny all pending approvals for a given invocation in a single action. This is useful when an invocation has multiple tool calls queued (e.g., a parallel_group workflow step where several tools all require approval before any can execute).

Batch operations use the `GET /v1/invocations/{id}/pending-approvals` endpoint to retrieve all pending approvals, then issue individual `POST /resume` calls for each. A future batch endpoint may be added in a subsequent slice (POST-4.4 or later); for now, batch is a UI-level pattern over the existing single-approval API.

Each individual resume call validates its own nonce. Batch replay protection follows the same HMAC rules as single approvals.

---

## 6. Headless Mode

### 6.1 Environment Variable

When the engine runs in a headless context (CI pipelines, automated test suites, integration environments), there is no operator available to review tool approval requests. The `AGENT33_HEADLESS_TOOL_APPROVAL` environment variable controls how P69b behaves in these contexts.

| Value | Behaviour |
|-------|-----------|
| `deny` | All tool calls that would require approval are automatically denied. The invocation receives `ToolApprovalDenied` immediately without creating a `PausedInvocation` record or emitting an SSE event. **This is the default.** |
| `approve` | All tool calls that would require approval are automatically approved without operator review. Use only in controlled test environments where the tool calls are safe. |

If the variable is not set, the system defaults to `deny`.

### 6.2 Rationale for Default Deny

The `deny` default is a safe-fail posture. In a headless environment with no operator available, automatically approving tool calls — especially destructive ones — would be a security regression. CI pipelines that need `approve` semantics must explicitly opt in by setting `AGENT33_HEADLESS_TOOL_APPROVAL=approve`.

### 6.3 CI Usage

For integration tests that exercise the approval flow itself (e.g., testing that `ToolApprovalDenied` is returned for a denied call), tests should set `AGENT33_HEADLESS_TOOL_APPROVAL=deny` explicitly and assert on the resulting error.

For tests that need tools to execute normally without triggering the approval gate (e.g., testing tool output correctness), tests should either:
- Set `AGENT33_HEADLESS_TOOL_APPROVAL=approve`, or
- Configure the tool governance policy to `allow` for the specific tools under test, bypassing the approval trigger entirely.

Headless mode short-circuits the approval flow before any DB write or SSE emission, so headless tests do not require a live database or SSE infrastructure.

---

## 7. Replay Protection

### 7.1 Why Nonces Are Required

Without replay protection, an attacker who intercepts a valid approval request could re-submit it to approve a different (or repeated) tool call on behalf of a legitimate operator. The HMAC nonce scheme prevents this by:

1. Binding the nonce to the specific `(run_id, tool_name, timestamp_window)` tuple — a nonce for one tool call cannot be used for another.
2. Enforcing a 30-second validity window — a captured nonce is useless after the window closes.
3. Tracking consumed nonces in a `nonce_log` table — each nonce can only be used once within its window.

### 7.2 HMAC Nonce Formula

```
nonce = HMAC-SHA256(
    message = f"{run_id}:{tool_name}:{floor(unix_timestamp / 30)}",
    key     = tenant_secret
)
```

Where:
- `run_id` is the invocation's unique identifier (UUID).
- `tool_name` is the exact name of the tool being approved (string, case-sensitive).
- `unix_timestamp` is the Unix epoch timestamp (integer seconds) at the moment the pause is initiated.
- `floor(unix_timestamp / 30)` bins the timestamp into 30-second windows: all timestamps within the same 30-second interval produce the same window index, and therefore the same nonce for the same `(run_id, tool_name)` pair.
- `tenant_secret` is a per-tenant HMAC secret key (stored securely — see Section 7.4).
- The output is a hex-encoded SHA-256 digest: 64 lowercase hexadecimal characters.

### 7.3 Window Semantics

Requests initiated at Unix timestamps 1744358400 through 1744358429 all fall in the same 30-second window (window index 58145280). Requests at timestamp 1744358430 fall in the next window (58145281). This means:

- An approval pair (pause + resume) initiated and completed within the same 30-second window uses the same nonce on both sides.
- If a pause is initiated at the end of a window and the resume arrives in the next window, the nonce computed for the resume will differ from the nonce stored in `PausedInvocation`. The resume call will be rejected with `409 Conflict` (ToolApprovalNonceReplay). This is a known edge case: operators must re-initiate the approval (create a new pause request) if the window boundary is crossed.
- The 30-second window is deliberately short to limit the replay attack surface.

### 7.4 Tenant Secret Storage

The `tenant_secret` used as the HMAC key must be stored securely and must not be derivable from any public information. The implementation in POST-4.3 must define where this secret lives (likely a dedicated column on the tenant model, encrypted at rest using the existing vault integration in `agent33.security`). Rotation of the secret invalidates all in-flight nonces and should be treated as a breaking operation.

### 7.5 Nonce Enforcement

1. When a `PausedInvocation` record is created, the computed nonce is stored in `PausedInvocation.nonce`.
2. The nonce is included in the SSE event payload and in the `POST /pause` response body so the operator's client has it.
3. When `POST /resume` is called, the `nonce` field in the request body must exactly match the stored `PausedInvocation.nonce`. A mismatch returns `409 Conflict` (`ToolApprovalNonceReplay`).
4. After a successful resume, the nonce is marked as consumed in the `nonce_log` table (keyed by `(tenant_id, nonce, window_index)`). Any subsequent resume attempt with the same nonce within the same window returns `409 Conflict`.

---

## 8. Feature Flag

### 8.1 Flag Definition

| Field | Value |
|-------|-------|
| Flag name | `p69b_tool_approval_enabled` |
| Default | `false` (disabled until POST-4.3 ships and is validated) |
| Scope | Per-tenant (overridable) with a global default |
| Type | Boolean |

When `p69b_tool_approval_enabled` is `false`, all tool governance `ask` policies fall back to the previous behaviour: the existing in-memory `ToolApprovalService.request()` flow is used, or calls are auto-approved depending on the tenant's legacy configuration. No `PausedInvocation` records are written and no SSE events are emitted.

### 8.2 Flag Lifecycle

| Phase | Action |
|-------|--------|
| Pre-launch | Flag disabled globally. POST-4.3 ships behind the flag. |
| Rollout (canary) | Flag enabled for one internal tenant. Monitor SSE delivery, nonce validation rates, DB write latency. |
| Gradual rollout | Flag enabled for opt-in tenants. Disable immediately on any critical failure. |
| General availability | Flag enabled by default for all tenants. Existing opt-out tenants retain override. |
| Retirement | Flag and legacy approval path removed after one deprecation cycle (target: POST-5.x). |

### 8.3 File-Based Kill Switch

In addition to the feature flag, a file-based kill switch is available for emergency disablement without a configuration change or deployment:

```
/tmp/agent33_disable_p69b
```

If this file exists on the engine host at the time a tool call is being evaluated, P69b is disabled for the duration of that process's lifetime (checked once per startup, or on every approval trigger — POST-4.3 decides the check frequency). The kill switch takes precedence over the feature flag. When active, the system returns `ToolApprovalFeatureDisabled` (`501 Not Implemented`) for any call that would have triggered the approval flow.

The kill switch is intended for operators who need to disable P69b immediately (e.g., an SSE delivery failure causing invocations to block indefinitely) without waiting for a flag propagation cycle.

---

## 9. Error States

All P69b errors are structured errors with a machine-readable `code` field and a human-readable `message`. They appear in API responses and as the `error` field on `FAILED` invocations.

| Error Code | HTTP Status | Trigger | Description |
|------------|-------------|---------|-------------|
| `ToolApprovalTimeout` | 408 Request Timeout | Approval not received before `expires_at` | The operator did not approve or deny the tool call within the configured timeout window. The `PausedInvocation` status is set to `timed_out`. The invocation terminates as `FAILED`. |
| `ToolApprovalDenied` | 403 Forbidden | Operator sent `approved=false` | The operator explicitly denied the tool call. The invocation terminates as `FAILED`. The `PausedInvocation.approved_by` field records the denying operator's identity. |
| `ToolApprovalNonceReplay` | 409 Conflict | Nonce already consumed or window boundary crossed | The nonce in the `POST /resume` request does not match the stored nonce, or the nonce has already been used. Possible causes: replay attack, duplicate submit, or 30-second window boundary crossed between pause and resume. |
| `ToolApprovalInvalidState` | 422 Unprocessable Entity | Operation attempted on invocation in wrong state | The invocation is not in a state that allows the requested operation. Examples: attempting to resume a `RUNNING` invocation, or pausing an already-`PAUSED_FOR_APPROVAL` invocation. |
| `ToolApprovalFeatureDisabled` | 503 Service Unavailable | Kill switch file exists or feature flag disabled | P69b is disabled either via the `p69b_tool_approval_enabled` flag or the `/tmp/agent33_disable_p69b` kill switch. The tool call is handled by the legacy approval flow (or auto-approved/denied per legacy config). |

---

## 10. Open Questions (Deferred to POST-4.3)

The following questions were identified during research and spec authoring. They must be resolved before implementation begins.

1. **invocation_id vs. execution_id**: The spec uses `invocation_id` throughout. The engine's current `ExecutionContract` uses `execution_id`. POST-4.3 must clarify whether `invocation_id == execution_id` or whether a parent run record exists above the contract level.

2. **SSE event schema**: The `tool_approval_required` SSE event fields (approval_id, truncation limits, etc.) are subject to the schema defined in POST-4.2 (SSE event schema versioning). POST-4.3 must depend on POST-4.2 being merged first.

3. **Tenant secret storage**: The HMAC formula requires a `tenant_secret`. The current engine has a JWT/API-key auth layer but no explicit `tenant_secret` field on the tenant model. POST-4.3 must define storage, encryption, and rotation semantics.

4. **Concurrent tool approvals**: If a parallel_group workflow step fans out multiple tool calls simultaneously, each generating an approval request, P69b currently generates one `PausedInvocation` per tool call. POST-4.3 must confirm this is the intended behaviour, or define a grouped record model.

5. **Nonce log retention**: The `nonce_log` table grows with each approval. POST-4.3 must define a retention policy (e.g., expire nonce_log entries after 24 hours) to prevent unbounded table growth.
