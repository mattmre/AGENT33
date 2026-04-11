# P69b Tool Approval — API Contract

**Document**: POST-4.1 API Contract
**Slice**: S2 (P69b Spec)
**Branch**: session126-s2-p69b-spec
**Prepared**: 2026-04-11
**Status**: Draft — authoritative for POST-4.3 implementation

---

## 1. POST /v1/invocations/{id}/pause

Pause an invocation at a specific tool call and register a pending approval request. This endpoint is called internally by the agent runtime when a tool call is flagged for approval. Operators do not call this endpoint directly — the runtime calls it on their behalf. It is exposed publicly to support headless orchestration scenarios where an external system needs to initiate a pause.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID (string) | The `invocation_id` of the running invocation to pause. |

### Request Body

```json
{
  "tool_name": "shell_exec",
  "tool_input": {
    "command": "rm -rf /var/data/old_reports",
    "working_dir": "/var/data"
  },
  "nonce": "3a7f2c9e4b1d8f6a2e5c0b9d3f7a1e4c8b2d5f9a3e6c0b4d7f2a9e1c4b8f5d3"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_name` | string | yes | Exact name of the tool being paused. Case-sensitive. |
| `tool_input` | object | yes | The full input object that would be passed to the tool. Stored as JSONB. |
| `nonce` | string | yes | HMAC-SHA256 hex string computed per the nonce specification (Section 8). 64 lowercase hex characters. |

### Response 200 — Approval Created

```json
{
  "approval_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "status": "PENDING",
  "expires_at": "2026-04-11T14:35:00Z",
  "nonce": "3a7f2c9e4b1d8f6a2e5c0b9d3f7a1e4c8b2d5f9a3e6c0b4d7f2a9e1c4b8f5d3"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `approval_id` | UUID (string) | Unique identifier for this approval request (the `PausedInvocation.id`). |
| `status` | string | Always `"PENDING"` on creation. |
| `expires_at` | ISO 8601 datetime | Timestamp at which the approval window closes. Computed as `created_at + timeout_seconds` (default 300 seconds). |
| `nonce` | string | The HMAC nonce echoed back for the client's use on the subsequent `/resume` call. |

### Response 409 — Nonce Already Used

Returned when the submitted nonce has already been consumed by a prior pause or resume operation, or when the nonce does not match the server's computed value for this `(invocation_id, tool_name, window)` tuple.

```json
{
  "error": "ToolApprovalNonceReplay",
  "detail": "The submitted nonce has already been consumed or does not match the expected value for this invocation and tool. The approval window may have crossed a 30-second boundary. Recompute the nonce and retry."
}
```

### Response 422 — Invalid Invocation State

Returned when the invocation identified by `id` is not in a state that permits pausing (e.g., it is already `PAUSED_FOR_APPROVAL`, `FAILED`, or `COMPLETED`).

```json
{
  "error": "ToolApprovalInvalidState",
  "detail": "Invocation f47ac10b-58cc-4372-a567-0e02b2c3d479 is in state FAILED and cannot be paused. Only RUNNING invocations may be paused for tool approval."
}
```

### Response 503 — Feature Disabled

Returned when the P69b feature flag is off or the `/tmp/agent33_disable_p69b` kill switch file is present.

```json
{
  "error": "ToolApprovalFeatureDisabled",
  "detail": "The tool approval feature (p69b_tool_approval_enabled) is currently disabled. Tool calls are proceeding without approval checks. Check the feature flag configuration or remove the kill switch file."
}
```

---

## 2. POST /v1/invocations/{id}/resume

Submit an operator decision (approve or deny) for a pending tool approval. This endpoint is called by the operator dashboard when the operator clicks Approve or Deny, or by a CI system in headless workflows.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID (string) | The `invocation_id` of the paused invocation. |

### Request Body

```json
{
  "approved": true,
  "nonce": "3a7f2c9e4b1d8f6a2e5c0b9d3f7a1e4c8b2d5f9a3e6c0b4d7f2a9e1c4b8f5d3",
  "reason": "Reviewed command — scoped to expected directory, approved for execution."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `approved` | boolean | yes | `true` to approve the tool call and resume the invocation; `false` to deny it and fail the invocation. |
| `nonce` | string | yes | The HMAC nonce from the `PausedInvocation` record, as returned by `POST /pause` or included in the SSE event. |
| `reason` | string | no | Optional human-readable reason for the decision. Stored in `PausedInvocation` for audit purposes. Especially recommended on denial. |

### Response 200 — Decision Accepted

```json
{
  "invocation_id": "e9b2f13a-4c71-4d92-b8a0-1f2c3d4e5f60",
  "status": "RUNNING",
  "resumed_at": "2026-04-11T14:32:17Z"
}
```

The `status` field reflects the new invocation state:
- `"RUNNING"` — when `approved=true`. The tool call will now execute and the invocation continues.
- `"FAILED"` — when `approved=false`. The invocation has terminated with `ToolApprovalDenied`.

| Field | Type | Description |
|-------|------|-------------|
| `invocation_id` | UUID (string) | The invocation that was resumed or failed. |
| `status` | string | Either `"RUNNING"` (approved) or `"FAILED"` (denied). |
| `resumed_at` | ISO 8601 datetime | Timestamp when the decision was recorded and acted upon. |

### Response 409 — Nonce Replay

Returned when the submitted nonce has already been consumed (i.e., `/resume` was previously called successfully for this approval), or when the nonce does not match the server's computation.

```json
{
  "error": "ToolApprovalNonceReplay",
  "detail": "This nonce has already been consumed. Each approval nonce may only be used once. If the invocation is still awaiting approval, refresh the dashboard to obtain a fresh nonce."
}
```

### Response 422 — Invocation Not Paused

Returned when the invocation is not currently in `PAUSED_FOR_APPROVAL` state. Common causes: the invocation timed out before the operator acted, or it was already resumed by another operator.

```json
{
  "error": "ToolApprovalInvalidState",
  "detail": "Invocation e9b2f13a-4c71-4d92-b8a0-1f2c3d4e5f60 is not in PAUSED_FOR_APPROVAL state (current state: FAILED). It may have timed out or been resolved by another operator."
}
```

---

## 3. GET /v1/invocations/{id}/pending-approvals

Retrieve all pending (unresolved) approval requests for a specific invocation. Used by the operator dashboard to populate the approval cards for a single invocation view.

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | UUID (string) | The `invocation_id` to query pending approvals for. |

### Response 200 — Pending Approvals List

```json
{
  "approvals": [
    {
      "approval_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "tool_name": "shell_exec",
      "tool_input": {
        "command": "rm -rf /var/data/old_reports",
        "working_dir": "/var/data"
      },
      "status": "PENDING",
      "created_at": "2026-04-11T14:30:00Z",
      "expires_at": "2026-04-11T14:35:00Z"
    }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `approvals` | array | List of pending approval objects for this invocation. May be empty if no approvals are pending. |
| `approvals[].approval_id` | UUID (string) | The `PausedInvocation.id` for this approval request. |
| `approvals[].tool_name` | string | Name of the tool awaiting approval. |
| `approvals[].tool_input` | object | Full JSONB tool input. Not truncated — use this endpoint when the dashboard needs the complete input for operator review. |
| `approvals[].status` | string | Always `"PENDING"` in this response (resolved approvals are not returned). |
| `approvals[].created_at` | ISO 8601 datetime | When the pause was initiated. |
| `approvals[].expires_at` | ISO 8601 datetime | When the approval window closes. |

Only `PENDING` approvals are returned. Approvals in `APPROVED`, `DENIED`, `TIMED_OUT`, or `CONSUMED` status are excluded from this response.

---

## 4. GET /v1/approvals/pending

Retrieve all pending approval requests across all invocations for the authenticated tenant. Used by the operator dashboard's global approval queue view and for batch denial workflows.

### Query Parameters

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | integer | 1 | — | Page number (1-indexed). |
| `page_size` | integer | 20 | 100 | Number of results per page. |

### Response 200 — Paginated Pending Approvals

```json
{
  "approvals": [
    {
      "approval_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "invocation_id": "e9b2f13a-4c71-4d92-b8a0-1f2c3d4e5f60",
      "tool_name": "shell_exec",
      "tool_input": {
        "command": "rm -rf /var/data/old_reports",
        "working_dir": "/var/data"
      },
      "status": "PENDING",
      "created_at": "2026-04-11T14:30:00Z",
      "expires_at": "2026-04-11T14:35:00Z"
    },
    {
      "approval_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "invocation_id": "c4d5e6f7-a8b9-0c1d-2e3f-4a5b6c7d8e9f",
      "tool_name": "file_write",
      "tool_input": {
        "path": "/etc/cron.d/agent33_job",
        "content": "0 * * * * /usr/bin/python3 /opt/agent33/run.py"
      },
      "status": "PENDING",
      "created_at": "2026-04-11T14:28:45Z",
      "expires_at": "2026-04-11T14:33:45Z"
    }
  ],
  "total": 2,
  "page": 1,
  "page_size": 20
}
```

| Field | Type | Description |
|-------|------|-------------|
| `approvals` | array | Page of pending approval objects. |
| `approvals[].approval_id` | UUID (string) | The `PausedInvocation.id` for this approval. |
| `approvals[].invocation_id` | UUID (string) | The invocation this approval belongs to. Present on this endpoint but not on `GET /v1/invocations/{id}/pending-approvals` (where the invocation is implied by the path). |
| `approvals[].tool_name` | string | Name of the tool awaiting approval. |
| `approvals[].tool_input` | object | Full JSONB tool input. |
| `approvals[].status` | string | Always `"PENDING"` in this response. |
| `approvals[].created_at` | ISO 8601 datetime | When the pause was initiated. |
| `approvals[].expires_at` | ISO 8601 datetime | When the approval window closes. |
| `total` | integer | Total number of pending approvals for this tenant (across all pages). |
| `page` | integer | Current page number. |
| `page_size` | integer | Number of results per page (as requested, capped at 100). |

Results are ordered by `created_at` ascending (oldest pending approvals first) to encourage FIFO review.

Approvals approaching their `expires_at` may expire between the list response and the subsequent `/resume` call. Callers should check for `408 Request Timeout` or `ToolApprovalInvalidState` when processing stale list results.

---

## 5. State Machine ASCII Diagram

The following diagram shows the complete invocation state machine as extended by P69b. States in uppercase are canonical invocation state values.

```
RUNNING
  │
  │  tool call matched by approval trigger
  │  (governance policy "ask", tenant require_approval_tools,
  │   or autonomy budget require_approval_commands)
  ▼
PAUSED_FOR_APPROVAL ──── timeout (expires_at elapsed) ────► FAILED
  │                                                     (ToolApprovalTimeout)
  │
  │ POST /resume { approved: false }
  ├──────────────────────────────────────────────────────► FAILED
  │                                                     (ToolApprovalDenied)
  │
  │ POST /resume { approved: true }
  ▼
RUNNING
  (tool executes with original inputs; invocation continues)
```

Note: The `PAUSED_FOR_APPROVAL` state is only reachable from `RUNNING`. Once an invocation is `FAILED` or `COMPLETED`, it cannot be paused.

When P69b is disabled (feature flag off or kill switch active), the `PAUSED_FOR_APPROVAL` state is never entered. Tool calls with an `"ask"` governance policy fall through to the legacy in-memory `ToolApprovalService` path or are auto-approved per tenant legacy configuration.

When headless mode is active (`AGENT33_HEADLESS_TOOL_APPROVAL=approve|deny`), the state transition happens synchronously without entering `PAUSED_FOR_APPROVAL`: the tool either executes immediately (approve mode) or the invocation transitions directly to `FAILED` (deny mode).

---

## 6. PausedInvocation DB Model

The `PausedInvocation` table is the authoritative store for tool approval state. One row is inserted per tool call that requires approval. The table is partitioned by `tenant_id` for multi-tenancy row-level isolation.

### Table: `paused_invocations`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique identifier for this approval record. Generated by the server at pause time. Used as `approval_id` in API responses. |
| `invocation_id` | UUID | NOT NULL, FK → invocations(id) | The invocation that is paused awaiting approval. One invocation may have multiple `PausedInvocation` rows over its lifetime (one per tool call that required approval). |
| `tenant_id` | VARCHAR(255) | NOT NULL, INDEX | Tenant identifier for multi-tenancy scoping. All queries against this table include a `tenant_id` predicate. |
| `tool_name` | VARCHAR(255) | NOT NULL | Exact name of the tool awaiting approval. Case-sensitive. Matches the tool registry key. |
| `tool_input` | JSONB | NOT NULL | Complete serialized input parameters that would be passed to the tool. Stored as JSONB for queryability. Sensitive fields should be redacted by the security layer before storage. |
| `nonce` | VARCHAR(64) | NOT NULL | HMAC-SHA256 hex string, 64 lowercase characters. Computed at pause time using the formula in Section 8. Used for replay protection on the `/resume` endpoint. |
| `status` | VARCHAR(16) | NOT NULL, CHECK (status IN ('PENDING', 'APPROVED', 'DENIED', 'TIMED_OUT', 'CONSUMED')) | Current status of the approval request. Only `PENDING` records are actionable. |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT now() | UTC timestamp when the `PausedInvocation` record was created (i.e., when execution paused). |
| `expires_at` | TIMESTAMPTZ | NOT NULL | UTC timestamp when the approval window closes. Computed as `created_at + timeout_seconds`. The timeout is configurable per tenant; the system default is 300 seconds (5 minutes). |
| `resolved_at` | TIMESTAMPTZ | NULL | UTC timestamp when the approval was resolved (approved, denied, or timed out). Null while status is `PENDING`. |
| `approved_by` | VARCHAR(255) | NULL | Identity of the operator who approved or denied the request (e.g., operator user ID or email). Null for timeout resolution and headless auto-approve/deny. Set by the server from the authenticated request identity on `/resume`. |

### Status Enum Values

| Value | Description |
|-------|-------------|
| `PENDING` | The approval request has been created and is awaiting operator action. The invocation is halted. |
| `APPROVED` | The operator approved the tool call. The invocation has been resumed. `resolved_at` and `approved_by` are set. |
| `DENIED` | The operator denied the tool call. The invocation has been failed with `ToolApprovalDenied`. `resolved_at` and `approved_by` are set. |
| `TIMED_OUT` | The approval window elapsed without operator action. The invocation has been failed with `ToolApprovalTimeout`. `resolved_at` is set; `approved_by` is null. |
| `CONSUMED` | The nonce associated with this record has been used (the record transitioned through APPROVED or DENIED). This terminal status prevents nonce reuse. |

### Indexes

The following indexes support the query patterns used by P69b endpoints:

```sql
-- Primary key
CREATE UNIQUE INDEX paused_invocations_pkey ON paused_invocations (id);

-- Tenant-scoped pending lookup (GET /v1/approvals/pending)
CREATE INDEX paused_invocations_tenant_status_created
  ON paused_invocations (tenant_id, status, created_at)
  WHERE status = 'PENDING';

-- Invocation-scoped pending lookup (GET /v1/invocations/{id}/pending-approvals)
CREATE INDEX paused_invocations_invocation_status
  ON paused_invocations (invocation_id, status)
  WHERE status = 'PENDING';

-- Timeout sweep (background scheduler job)
CREATE INDEX paused_invocations_expires_at
  ON paused_invocations (expires_at)
  WHERE status = 'PENDING';
```

---

## 7. Error Taxonomy

All P69b error responses follow the same JSON envelope:

```json
{
  "error": "<ErrorCode>",
  "detail": "<human-readable explanation>"
}
```

The `error` field is machine-readable and stable across versions. The `detail` field is for operator/developer consumption and may change between releases.

| Error Code | HTTP Status | Triggering Condition | Which Endpoints |
|------------|-------------|---------------------|-----------------|
| `ToolApprovalTimeout` | 408 Request Timeout | The `PausedInvocation.expires_at` timestamp has elapsed and the background sweep has failed the invocation. Returned on `/resume` if called after expiry, and emitted internally when the sweep fires. | `POST /pause`, `POST /resume` |
| `ToolApprovalDenied` | 403 Forbidden | Operator submitted `approved=false` on `/resume`, or headless deny mode is active. The invocation has been transitioned to `FAILED`. | `POST /resume` (internal propagation to caller) |
| `ToolApprovalNonceReplay` | 409 Conflict | The submitted nonce has already been consumed (status = `CONSUMED`), or the server-computed nonce does not match the submitted value (indicating a replay attempt, a duplicate submission, or a 30-second window boundary crossing). | `POST /pause`, `POST /resume` |
| `ToolApprovalInvalidState` | 422 Unprocessable Entity | The requested operation is not permitted given the invocation's current state. Examples: attempting to pause an invocation that is already `PAUSED_FOR_APPROVAL`; attempting to resume an invocation that is not in `PAUSED_FOR_APPROVAL` state. | `POST /pause`, `POST /resume` |
| `ToolApprovalFeatureDisabled` | 503 Service Unavailable | The `p69b_tool_approval_enabled` feature flag is `false`, or the file `/tmp/agent33_disable_p69b` exists on the host. P69b is entirely inactive; tool calls proceed without entering the approval flow. | `POST /pause` |

### HTTP Status Rationale

- **408** for timeout: the request could not be fulfilled because the time window for the resource to respond (operator action) has elapsed. This is semantically analogous to a client-side read timeout.
- **403** for denial: the resource (tool execution) is forbidden. The prohibition is the operator's explicit decision, not a permission check failure.
- **409** for nonce replay: the submitted state conflicts with the server's known state (nonce already consumed). Conflict is the correct status for optimistic-concurrency-style collisions.
- **422** for invalid state: the request is syntactically valid but semantically unprocessable given the current server state.
- **503** for feature disabled: the service (P69b approval gate) is temporarily or permanently unavailable. Clients should degrade gracefully.

---

## 8. HMAC Nonce Specification

### 8.1 Algorithm

```
nonce = HMAC-SHA256(
    key     = tenant_secret,
    message = f"{run_id}:{tool_name}:{floor(unix_timestamp / 30)}"
)
```

Encoded as a **lowercase hexadecimal string**, 64 characters in length (32 bytes × 2 hex chars per byte).

### 8.2 Input Components

| Component | Type | Description |
|-----------|------|-------------|
| `tenant_secret` | bytes | Per-tenant HMAC secret key. Stored encrypted at rest in the tenant configuration. Rotatable; rotation invalidates all in-flight nonces. |
| `run_id` | string | The `invocation_id` UUID in its canonical string form (e.g., `"e9b2f13a-4c71-4d92-b8a0-1f2c3d4e5f60"`). Hyphen-separated, lowercase. |
| `tool_name` | string | The exact tool name string (e.g., `"shell_exec"`). Case-sensitive. Must match the `tool_name` stored in `PausedInvocation`. |
| `floor(unix_timestamp / 30)` | integer | The Unix epoch timestamp (seconds since 1970-01-01T00:00:00Z), integer-divided by 30 (floor division). This bins all timestamps within the same 30-second interval into the same window index. |

### 8.3 Window Semantics

The `floor(timestamp / 30)` term creates a sliding 30-second validity window:

- All timestamps in the range `[30k, 30k+29]` map to window index `k`.
- The nonce for a given `(run_id, tool_name)` pair changes at every 30-second boundary.
- A pause initiated at timestamp `T` and a resume submitted at timestamp `T + 31` may fall in different windows, causing a nonce mismatch. This is a known edge case; the operator must retry (the system creates a fresh pause request with a new nonce).

### 8.4 Illustrative Example

The following values are illustrative only and do not represent real secrets or live invocations.

| Input | Value |
|-------|-------|
| `run_id` | `abc123de-f456-789a-bcde-f01234567890` |
| `tool_name` | `shell` |
| `unix_timestamp` | `1744300800` |
| `floor(1744300800 / 30)` | `58143360` |
| HMAC message | `abc123de-f456-789a-bcde-f01234567890:shell:58143360` |
| `tenant_secret` | `(not shown — stored in vault)` |
| nonce output | `3a7f2c9e4b1d8f6a2e5c0b9d3f7a1e4c8b2d5f9a3e6c0b4d7f2a9e1c4b8f5d3` |

### 8.5 Server-Side Enforcement

On `POST /resume`, the server performs the following nonce validation sequence:

1. Load the `PausedInvocation` record for the given `invocation_id`.
2. Assert `PausedInvocation.status == 'PENDING'`. If not, return `ToolApprovalInvalidState` (422).
3. Recompute the expected nonce: `HMAC-SHA256(f"{invocation_id}:{tool_name}:{floor(now() / 30)}", tenant_secret)`.
4. Assert submitted `nonce == recomputed nonce`. If not, return `ToolApprovalNonceReplay` (409).
5. Assert `PausedInvocation.nonce == submitted nonce`. If not (e.g., the stored nonce was from a different window), return `ToolApprovalNonceReplay` (409).
6. Update `PausedInvocation.status` to `APPROVED` or `DENIED` (per the `approved` field), and then to `CONSUMED`.
7. Set `PausedInvocation.resolved_at = now()` and `PausedInvocation.approved_by = <authenticated operator identity>`.
8. Proceed with invocation resumption or failure.

Steps 2–7 must execute within a single database transaction to prevent race conditions when multiple operators attempt to resolve the same approval simultaneously.

### 8.6 Secret Rotation

When `tenant_secret` is rotated:

- All `PausedInvocation` records with `status = PENDING` become unreachable: their stored nonces are computed with the old key and cannot be recomputed with the new key.
- Pending approvals must be manually resolved (denied) before rotation, or must be allowed to time out.
- POST-4.3 must document the rotation procedure and provide a migration script to drain pending approvals before key rotation.

---

## Appendix A: Full JSON Schemas (OpenAPI 3.1)

### PauseRequest

```json
{
  "type": "object",
  "required": ["tool_name", "tool_input", "nonce"],
  "properties": {
    "tool_name": {
      "type": "string",
      "description": "Exact name of the tool being paused. Case-sensitive.",
      "example": "shell_exec"
    },
    "tool_input": {
      "type": "object",
      "description": "Full tool input parameters as a JSON object.",
      "additionalProperties": true
    },
    "nonce": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$",
      "description": "HMAC-SHA256 hex string, 64 lowercase hex characters."
    }
  }
}
```

### PauseResponse

```json
{
  "type": "object",
  "required": ["approval_id", "status", "expires_at", "nonce"],
  "properties": {
    "approval_id": {
      "type": "string",
      "format": "uuid",
      "description": "Unique identifier for this approval request."
    },
    "status": {
      "type": "string",
      "enum": ["PENDING"],
      "description": "Always PENDING on creation."
    },
    "expires_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 UTC timestamp when the approval window closes."
    },
    "nonce": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$",
      "description": "Echoed nonce for use in the subsequent /resume call."
    }
  }
}
```

### ResumeRequest

```json
{
  "type": "object",
  "required": ["approved", "nonce"],
  "properties": {
    "approved": {
      "type": "boolean",
      "description": "true to approve and resume; false to deny and fail the invocation."
    },
    "nonce": {
      "type": "string",
      "pattern": "^[0-9a-f]{64}$",
      "description": "The nonce from the PausedInvocation record."
    },
    "reason": {
      "type": "string",
      "description": "Optional operator rationale for the decision. Stored for audit.",
      "maxLength": 1024
    }
  }
}
```

### ResumeResponse

```json
{
  "type": "object",
  "required": ["invocation_id", "status", "resumed_at"],
  "properties": {
    "invocation_id": {
      "type": "string",
      "format": "uuid"
    },
    "status": {
      "type": "string",
      "enum": ["RUNNING", "FAILED"],
      "description": "RUNNING if approved, FAILED if denied."
    },
    "resumed_at": {
      "type": "string",
      "format": "date-time",
      "description": "UTC timestamp when the decision was recorded."
    }
  }
}
```

### PendingApprovalItem (single invocation)

```json
{
  "type": "object",
  "required": ["approval_id", "tool_name", "tool_input", "status", "created_at", "expires_at"],
  "properties": {
    "approval_id": { "type": "string", "format": "uuid" },
    "tool_name": { "type": "string" },
    "tool_input": { "type": "object", "additionalProperties": true },
    "status": { "type": "string", "enum": ["PENDING"] },
    "created_at": { "type": "string", "format": "date-time" },
    "expires_at": { "type": "string", "format": "date-time" }
  }
}
```

### PendingApprovalItem (global list — includes invocation_id)

```json
{
  "type": "object",
  "required": ["approval_id", "invocation_id", "tool_name", "tool_input", "status", "created_at", "expires_at"],
  "properties": {
    "approval_id": { "type": "string", "format": "uuid" },
    "invocation_id": { "type": "string", "format": "uuid" },
    "tool_name": { "type": "string" },
    "tool_input": { "type": "object", "additionalProperties": true },
    "status": { "type": "string", "enum": ["PENDING"] },
    "created_at": { "type": "string", "format": "date-time" },
    "expires_at": { "type": "string", "format": "date-time" }
  }
}
```

### ErrorResponse

```json
{
  "type": "object",
  "required": ["error"],
  "properties": {
    "error": {
      "type": "string",
      "enum": [
        "ToolApprovalTimeout",
        "ToolApprovalDenied",
        "ToolApprovalNonceReplay",
        "ToolApprovalInvalidState",
        "ToolApprovalFeatureDisabled"
      ]
    },
    "detail": {
      "type": "string",
      "description": "Human-readable explanation. Not stable across releases."
    }
  }
}
```
