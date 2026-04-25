# SSE Schema v2 Migration Path

**Document**: SSE Schema Migration Contract  
**Slice**: Session 131 T3  
**Branch**: session131-t3-sse-docs  
**Prepared**: 2026-04-20  
**Status**: Authoritative migration contract — backend foundation may proceed only behind an opt-in flag + kill switch while strict rejection remains in force

---

## Purpose

This document captures the complete upgrade contract between the current SSE schema (v1,
introduced in PR #400) and any future v2 revision. It exists so that implementers,
contributors, and client authors have a concrete, unambiguous specification before a
single line of v2 code is written.

**Gate**: v2 work is blocked until this document is reviewed. See locked decision #19 in
`docs/phases/PHASE-PLAN-POST-P72-2026.md`.

**Backend foundation note**: the initial implementation slice keeps v1 as the default, adds
`SSE_SCHEMA_V2_ENABLED=false`, honors `/tmp/agent33_disable_sse_v2` as an emergency kill switch,
and pins one schema version per workflow run so sync/replay/live/heartbeat events never mix v1
and v2 payloads within the same stream.

---

## 1. Current State (v1)

### 1.1 Schema Version Constant and Enforcement

Source file: `engine/src/agent33/workflows/events.py`

```python
# Line 15
CURRENT_SCHEMA_VERSION: int = 1
```

The constant is an `int`, not a semver string. All events emitted by the server carry this
integer in the `schema_version` field.

The strict-rejection guard (lines 33–50):

```python
def check_schema_version(
    event_dict: dict[str, Any],
    *,
    expected_version: int = CURRENT_SCHEMA_VERSION,
) -> None:
    received: int = int(event_dict.get("schema_version", 0))
    if received != expected_version:
        raise SchemaVersionMismatchError(received=received, expected=expected_version)
```

Key semantics:
- A missing `schema_version` key is treated as version `0`, which always fails validation.
- Equality check only — there is no range check, no "accept older" logic.
- Raises `SchemaVersionMismatchError` (defined at lines 24–30) on any mismatch.

```python
class SchemaVersionMismatchError(Exception):
    def __init__(self, received: int, expected: int) -> None:
        self.received = received
        self.expected = expected
        super().__init__(f"SSE schema version mismatch: expected {expected}, got {received}")
```

### 1.2 WorkflowEvent Dataclass (v1 Complete Field List)

Source: `engine/src/agent33/workflows/events.py`, lines 73–107.

```python
@dataclass(frozen=True)
class WorkflowEvent:
    event_type: WorkflowEventType   # required; one of the WorkflowEventType StrEnum values
    run_id: str                      # required; unique execution identifier
    workflow_name: str               # required; workflow definition name (shared across runs)
    timestamp: float                 # optional at construction; defaults to time.time()
    step_id: str | None = None       # optional; present only for step-scoped events
    data: dict[str, Any]             # optional at construction; defaults to {}
    event_id: str | None = None      # optional; assigned by ws_manager._assign_event_id()
    schema_version: int = CURRENT_SCHEMA_VERSION  # always 1 in v1
```

The `to_dict()` method (lines 90–103) controls exactly which fields appear in the serialized
JSON payload. Notably:

- `step_id` is omitted when `None` (not null-serialized — the key is absent entirely).
- `data` is omitted when the dict is empty.
- `event_id` is **not** included in `to_dict()` / `to_json()`. It is applied at the SSE
  transport layer as the `id:` field in the SSE frame (see section 1.3).
- `schema_version` is always present in the JSON body.

Full v1 JSON payload (all fields present):

```json
{
  "type": "step_started",
  "run_id": "abc123",
  "workflow_name": "my-workflow",
  "timestamp": 1745000000.123,
  "step_id": "step-1",
  "data": {"some_key": "some_value"},
  "schema_version": 1
}
```

Minimal v1 JSON payload (heartbeat with no step, no data):

```json
{
  "type": "heartbeat",
  "run_id": "abc123",
  "workflow_name": "my-workflow",
  "timestamp": 1745000000.123,
  "schema_version": 1
}
```

### 1.3 Event Type Enum

Source: `engine/src/agent33/workflows/events.py`, lines 58–70.

```python
class WorkflowEventType(StrEnum):
    SYNC = "sync"
    HEARTBEAT = "heartbeat"
    WORKFLOW_STARTED = "workflow_started"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_SKIPPED = "step_skipped"
    STEP_RETRYING = "step_retrying"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
```

### 1.4 SSE Wire Format

Source: `engine/src/agent33/api/routes/workflow_sse.py`, lines 86–94; and
`engine/src/agent33/workflows/transport.py`, lines 338–346.

Each event is formatted as a single SSE frame:

```
id: {event_id}\n
data: {json_payload_line_1}\n
data: {json_payload_line_2}\n
\n
```

Rules:
- The `id:` line is present only when `event.event_id` is not `None`. Event IDs are
  monotonically-incrementing integers (assigned per-run by
  `ws_manager._assign_event_id()`), serialized as strings.
- Multi-line JSON is split by newlines and each line prefixed with `data: `.
- The frame ends with a blank line (`\n\n`) as required by the SSE specification.
- `event_id` is carried in the SSE frame header (`id:`), not in the JSON body.

The SSE streaming endpoint is `GET /v1/workflows/{run_id}/events`
(source: `engine/src/agent33/api/routes/workflow_sse.py`, line 21).

On connection:
1. A `SYNC` event is sent first (current run snapshot).
2. Replay events (if `Last-Event-ID` header was provided) are sent next.
3. Live events follow as they occur.
4. Periodic `HEARTBEAT` events are emitted at configurable intervals (default: 30 seconds)
   when no other events are pending.

### 1.5 Architectural Decision: Strict Rejection

Decision #10 in `docs/phases/PHASE-PLAN-POST-P72-2026.md`:

> SSE version enforcement: Strict rejection — v1 clients reject v2 streams entirely.

There is no negotiation, no graceful downgrade, no partial compatibility. A client that
receives an event with `schema_version != 1` must immediately close the connection and
surface a clear error. See section 4.5 for the exact error behavior.

---

## 2. Why v2 Will Eventually Be Needed

v2 is not currently planned. However, the following changes would each constitute a
breaking incompatibility that requires a version bump rather than an additive change.

### 2.1 Known v2 Candidate Changes

| Change | Rationale |
|--------|-----------|
| Rename `type` → `event_type` in the JSON payload | The dataclass field is `event_type` but `to_dict()` serializes it as `"type"`. A rename to align JSON key with the Python field would be breaking. |
| Add a required `tenant_id` field to every event | Multi-tenancy improvements might require tenant context on each event for client-side filtering. A required field is a breaking addition (older clients would not know to validate or route by it). |
| Replace `timestamp: float` with `timestamp: str` (ISO 8601) | Changing the type of an existing field is a hard break for any client that reads the field as a number. |
| Remove `data: dict` in favor of typed per-event-type payloads | The current `data` field is an untyped catch-all. A v2 design might introduce typed sub-schemas (e.g., `step_data`, `workflow_data`), making `data` absent or structurally different. |
| Add `correlation_id` as a required field for distributed tracing | Clients that construct or validate events would need to produce this field; its absence in v1 payloads becomes an error. |
| Change `event_id` from transport-only (SSE `id:`) to JSON-body field | Moving `event_id` into the JSON body (it currently lives only in the SSE frame header) would change the JSON schema. |

### 2.2 Changes That Do Not Require a Version Bump

The following changes can be made without incrementing `schema_version`:

- Adding a new optional field with a default of `None` (e.g., an advisory `retry_after_ms`
  on `STEP_RETRYING` events) — as long as the field is absent when not set, existing clients
  can safely ignore it.
- Adding a new `WorkflowEventType` value — existing clients that use exhaustive match
  patterns may warn but should not crash if they use a fallback branch.
- Adding new `data` dict keys to an existing event type (the `data` dict is already
  open-ended in v1).

**Do not bump `schema_version` for purely additive, optional changes.**

---

## 3. v2 Schema Design Constraints

Any v2 implementation must conform to these constraints. They are not suggestions.

### 3.1 Client Detection and Response

Clients MUST detect `schema_version: 2` on the first event received and take one of two
actions:

1. **Upgrade path**: If the client implements the v2 contract, switch the event parser to
   the v2 model for the remainder of the stream. Do not attempt to parse v2 events with
   the v1 model.
2. **Rejection path**: If the client does not implement v2, disconnect immediately and
   display a user-visible "client requires upgrade" error (see section 4.5).

There is no "mixed mode." A client cannot parse some events as v1 and some as v2.

### 3.2 Server Stream Purity

The server MUST NOT mix v1 and v2 events in the same SSE stream. Every event in a single
stream must carry the same `schema_version`. This is guaranteed by the fact that
`schema_version` is baked into `CURRENT_SCHEMA_VERSION` at the module level; all
`WorkflowEvent` instances inherit the same value unless explicitly overridden.

If a gradual rollout requires serving v1 and v2 streams simultaneously (e.g., different
tenants on different versions), use a feature flag to switch the entire stream, not per-event
version selection.

### 3.3 New Fields Must Be Explicitly Documented

For each new field added in v2, the implementation must document:

| Attribute | Requirement |
|-----------|-------------|
| Field name | Must match the Python dataclass field name and the JSON key |
| Type | Python type annotation and JSON schema type |
| Semantics | One sentence describing what the field contains |
| Required/Optional | Whether the field may be absent in the JSON payload |
| Default | The default value if optional |

Example documentation entry (hypothetical):

| Field | `correlation_id` |
|-------|-----------------|
| Type | `str \| None` |
| Semantics | Distributed trace correlation identifier, propagated from the originating HTTP request. |
| Required | No (optional; absent when the invocation was not started with a tracing header) |
| Default | Omitted from JSON when `None` |

### 3.4 Field Removal Requires a Version Bump

Removing any field that is currently present in the v1 JSON payload (`type`, `run_id`,
`workflow_name`, `timestamp`, `schema_version`) requires a version bump to v2. There is no
grace period for field removal — the bump is the grace period.

Removing optional fields (`step_id`, `data`) also requires a version bump because clients
that rely on their occasional presence will silently break.

### 3.5 schema_version Is Present in Every Event

`schema_version` is an integer present in every event, not just the first. This is the
current v1 behavior (see `to_dict()` in `events.py`) and must be preserved in v2. Clients
that reconnect mid-stream and receive events from a newly deployed server would have no way
to detect a version mismatch if the field were omitted from subsequent events.

### 3.6 schema_version Is an Integer, Not a Semver String

`schema_version` is `int`. It will be `2` in v2, not `"2.0"` or `"2.0.0"`. This is locked
(see section 7).

---

## 4. Client Upgrade Path (Step-by-Step)

This is a concrete checklist. A client author implementing v2 support must complete every
step in order.

### Step 1: Detect schema_version on the first event

Parse the first JSON event from the stream. Before processing any fields other than
`schema_version`, extract and validate it:

```python
first_event = json.loads(first_data_line)
schema_version = first_event.get("schema_version", 0)
```

If `schema_version` is absent, treat it as `0` (pre-versioning payload). This matches the
behavior of `check_schema_version()` in `events.py` (line 48).

### Step 2: Branch on schema_version

```python
if schema_version == 1:
    parser = WorkflowEventV1Parser()
elif schema_version == 2:
    parser = WorkflowEventV2Parser()
else:
    raise SchemaVersionMismatchError(received=schema_version, expected=EXPECTED_VERSION)
```

- Use the v2 parser for all subsequent events in this stream.
- Do not re-check `schema_version` on every event (it is always the same within a stream
  per constraint 3.2), but do validate it if your implementation performs periodic
  consistency checks.

### Step 3: Handle new required fields in v2

For each field listed as "required" in the v2 specification, validate its presence and type
before processing the event. A missing required field is a malformed event and should be
treated as a stream error (disconnect and report).

Concrete check pattern:

```python
if "new_required_field" not in event_dict:
    raise MalformedEventError(
        f"v2 event missing required field 'new_required_field': {event_dict!r}"
    )
```

Do not silently default a missing required field. Silent defaults mask server-side bugs.

### Step 4: Handle removed or renamed fields

For each field that v2 removes or renames:

- **Removed field**: Remove all code that reads that field. If your logic depended on it,
  find its v2 replacement or change your logic.
- **Renamed field**: Update every read site. If the old name still appears in your parsing
  code, it will silently read `None` from a v2 event, causing downstream logic errors.

Concrete example — if v1 `"type"` is renamed to `"event_type"` in v2:

```python
# v1 client code — DO NOT use with v2 stream
event_type = event_dict["type"]

# v2 client code
event_type = event_dict["event_type"]
```

Audit your codebase for every reference to each changed field name before merging v2 client
code.

### Step 5: Handle the v1 client receiving a v2 stream (error path)

A v1 client that sees `schema_version: 2` must:

1. Immediately stop reading from the queue. Do not process any further events.
2. Close the SSE connection.
3. Display a user-visible message. The recommended message text is:

   > "This client is incompatible with the server's current event schema (v2). Please
   > upgrade the client to continue."

4. Raise `SchemaVersionMismatchError` (or equivalent) in the client's internal error
   handling so that error logs capture the received and expected versions.
5. Do not automatically reconnect. A reconnect will receive the same v2 stream and loop
   indefinitely.

Python reference implementation for the v1 client error path (using the existing
`check_schema_version()` function from `events.py`):

```python
from agent33.workflows.events import check_schema_version, SchemaVersionMismatchError

try:
    check_schema_version(event_dict)  # raises if schema_version != 1
except SchemaVersionMismatchError as exc:
    connection.close()
    display_upgrade_required_error(exc.received, exc.expected)
    raise
```

---

## 5. Server-Side Migration Steps

This section is a checklist for the server-side implementer who ships v2.

### Step 1: Bump CURRENT_SCHEMA_VERSION

In `engine/src/agent33/workflows/events.py`, line 15:

```python
# Before
CURRENT_SCHEMA_VERSION: int = 1

# After
CURRENT_SCHEMA_VERSION: int = 2
```

This single change causes every `WorkflowEvent` constructed with `schema_version=CURRENT_SCHEMA_VERSION` (the default) to emit `"schema_version": 2` in its JSON body. All existing v1 clients will immediately start receiving v2 events and will hit `SchemaVersionMismatchError`.

**This is a breaking change. Do not merge this without a coordinated rollout plan.**

### Step 2: Update WorkflowEvent Fields

In `engine/src/agent33/workflows/events.py`, update the `WorkflowEvent` dataclass:

- Add new required fields (no default value).
- Add new optional fields (with a `None` default or `field(default_factory=...)`).
- Remove fields that v2 drops.
- Rename fields that v2 renames.

Also update `to_dict()` (lines 90–103) to serialize all v2 fields correctly. Any new
optional field that should be omitted when `None` must follow the existing pattern:

```python
if self.new_optional_field is not None:
    result["new_optional_field"] = self.new_optional_field
```

Any new required field must always be present in the output dict.

### Step 3: Update check_schema_version()

#### Option A: Hard cutover (recommended for most cases)

Update `expected_version` default to `2`. v1 clients are immediately rejected.

```python
def check_schema_version(
    event_dict: dict[str, Any],
    *,
    expected_version: int = CURRENT_SCHEMA_VERSION,  # now 2
) -> None:
    ...
```

#### Option B: Grace period (accept v1 and v2 temporarily)

If the rollout requires a grace period where both v1 and v2 clients must be supported
simultaneously, update `check_schema_version()` to accept a range:

```python
SUPPORTED_SCHEMA_VERSIONS: frozenset[int] = frozenset({1, 2})

def check_schema_version(
    event_dict: dict[str, Any],
    *,
    expected_versions: frozenset[int] = SUPPORTED_SCHEMA_VERSIONS,
) -> None:
    received: int = int(event_dict.get("schema_version", 0))
    if received not in expected_versions:
        raise SchemaVersionMismatchError(received=received, expected=max(expected_versions))
```

Set a hard deadline for removing v1 support from `SUPPORTED_SCHEMA_VERSIONS`. Permanent
grace periods become permanent technical debt.

### Step 4: Add a Feature Flag for Gradual Rollout

If the rollout is gradual (not a simultaneous cutover for all tenants):

1. Add a feature flag: `sse_schema_v2_enabled: bool = False` in `engine/src/agent33/config.py`.
2. In `WorkflowEvent.__init__` (or wherever events are constructed for the new schema),
   read the flag and select the schema version:

   ```python
   schema_version = 2 if settings.sse_schema_v2_enabled else 1
   ```

3. Add a file-based kill switch: `/tmp/agent33_disable_sse_v2` (consistent with the pattern
   established in PR #406 and locked decision #13 in PHASE-PLAN-POST-P72-2026.md).
4. Set `schema_version=1` when the kill switch file exists.

Kill switch check pattern (consistent with existing infrastructure):

```python
import os
from pathlib import Path

_KILL_SWITCH = Path("/tmp/agent33_disable_sse_v2")

def get_active_schema_version() -> int:
    if _KILL_SWITCH.exists():
        return 1
    if settings.sse_schema_v2_enabled:
        return 2
    return 1
```

### Step 5: Update All Event Construction Sites

Search for every call to `WorkflowEvent(...)` in the codebase and verify they produce
correct v2 output:

```bash
grep -r "WorkflowEvent(" engine/src/ engine/tests/
```

Key locations to audit:
- `engine/src/agent33/workflows/executor.py` — step lifecycle events
- `engine/src/agent33/api/routes/workflows.py` — WORKFLOW_FAILED event on exception (line 498)
- `engine/src/agent33/workflows/ws_manager.py` — SYNC and HEARTBEAT synthetic events
  (lines 299–337)

---

## 6. Testing Requirements for v2

All three test scenarios must be present in the test suite before v2 merges.

### 6.1 Regression Test: v1 Client + v2 Stream → SchemaVersionMismatchError

Verify that `check_schema_version()` raises `SchemaVersionMismatchError` when a v2 payload
is received by code that expects v1.

```python
def test_v1_client_rejects_v2_stream() -> None:
    """A v1 client must raise SchemaVersionMismatchError on a v2 event."""
    from agent33.workflows.events import SchemaVersionMismatchError, check_schema_version

    v2_event_dict = {
        "type": "workflow_started",
        "run_id": "run-001",
        "workflow_name": "test-workflow",
        "timestamp": 1745000000.0,
        "schema_version": 2,
    }
    with pytest.raises(SchemaVersionMismatchError) as exc_info:
        check_schema_version(v2_event_dict, expected_version=1)

    assert exc_info.value.received == 2
    assert exc_info.value.expected == 1
```

### 6.2 Regression Test: v2 Client + v2 Stream → Events Received Correctly

Verify that a v2-aware client successfully parses a v2 event without error, and that all
new fields are present and typed correctly.

```python
def test_v2_client_accepts_v2_stream() -> None:
    """A v2 client must parse v2 events without error."""
    from agent33.workflows.events import check_schema_version

    v2_event_dict = {
        "type": "workflow_started",
        "run_id": "run-001",
        "workflow_name": "test-workflow",
        "timestamp": 1745000000.0,
        "schema_version": 2,
        # ... any new v2 required fields here
    }
    # Must not raise
    check_schema_version(v2_event_dict, expected_version=2)

    # Assert new fields are present and typed correctly
    # (fill in with actual v2 field assertions)
```

### 6.3 Regression Test: Existing v1 Tests Must Still Pass Unchanged

Run the entire existing test suite — specifically any tests in
`engine/tests/test_workflow_events.py` (or equivalent) — without modifying them. If v1 tests
fail after the v2 change, the v2 implementation has a backwards-compatibility bug that needs
to be fixed before merging.

This is enforced by the "no changes to existing tests" rule: if you must modify a v1 test to
make v2 work, you have introduced a regression in a locked behavior.

### 6.4 Test: Missing schema_version Treated as Version 0

```python
def test_missing_schema_version_treated_as_zero() -> None:
    """An event dict without schema_version is treated as version 0."""
    from agent33.workflows.events import SchemaVersionMismatchError, check_schema_version

    event_without_version = {
        "type": "heartbeat",
        "run_id": "run-001",
        "workflow_name": "test-workflow",
        "timestamp": 1745000000.0,
    }
    with pytest.raises(SchemaVersionMismatchError) as exc_info:
        check_schema_version(event_without_version, expected_version=2)

    assert exc_info.value.received == 0
```

### 6.5 Integration Test: SSE Stream Contains Consistent schema_version

Connect to `GET /v1/workflows/{run_id}/events` and verify every event frame in the stream
has `"schema_version": 2`. No event in a single stream may have a different version.

---

## 7. Locked Decisions (Do Not Reopen)

The following decisions are final. Reopening them requires explicit approval from the project
owner. They must not be modified as part of v2 implementation work.

### Decision #10: Strict Rejection Model

Source: `docs/phases/PHASE-PLAN-POST-P72-2026.md`, locked decision #10.

> SSE version enforcement: Strict rejection — v1 clients reject v2 streams entirely.

There is no graceful downgrade path. A client that receives a version it does not understand
must disconnect and error, not attempt to parse the stream.

This decision was made in Session 122 and implemented in PR #400. It is not subject to
revision during v2 implementation.

### Decision: schema_version Is an Integer, Not a Semver String

`schema_version` is `int`. The wire value is `2`, not `"2"`, not `"2.0"`, not `"2.0.0"`.

This is established by the `schema_version: int = CURRENT_SCHEMA_VERSION` field type in
`WorkflowEvent` and the `int(event_dict.get("schema_version", 0))` cast in
`check_schema_version()`.

Changing this to a string type would break the cast and would require a separate migration
path document.

### Decision: schema_version Is Present in Every Event, Not Just the First

Every event emitted by the server carries `schema_version` in its JSON body (see `to_dict()`
lines 90–103 in `events.py`). Clients that reconnect mid-stream or that receive replayed
events can always determine the schema version from any single event.

Removing `schema_version` from non-first events would invalidate `check_schema_version()`
for any call site that validates individual events rather than just the stream header.

---

## Appendix A: File Reference Index

All code references in this document are to files in the repository root.

| File | Purpose |
|------|---------|
| `engine/src/agent33/workflows/events.py` | `WorkflowEvent`, `CURRENT_SCHEMA_VERSION`, `SchemaVersionMismatchError`, `check_schema_version()`, `WorkflowEventType` |
| `engine/src/agent33/workflows/ws_manager.py` | `WorkflowWSManager`, SSE subscription, event publication, replay buffer, event ID assignment |
| `engine/src/agent33/workflows/transport.py` | `_format_sse_frame()`, `WorkflowTransportManager`, `TransportConfig` |
| `engine/src/agent33/api/routes/workflow_sse.py` | `GET /v1/workflows/{run_id}/events`, `_format_sse()`, connection lifecycle |
| `engine/src/agent33/api/routes/workflows.py` | `WorkflowExecutor` invocation, `WORKFLOW_FAILED` event emission on exception |
| `docs/phases/PHASE-PLAN-POST-P72-2026.md` | Locked decisions #10 and #19 governing SSE versioning |

---

## Appendix B: v1 JSON Schema (OpenAPI 3.1)

```json
{
  "type": "object",
  "required": ["type", "run_id", "workflow_name", "timestamp", "schema_version"],
  "properties": {
    "type": {
      "type": "string",
      "enum": [
        "sync", "heartbeat", "workflow_started", "step_started", "step_completed",
        "step_failed", "step_skipped", "step_retrying", "workflow_completed", "workflow_failed"
      ],
      "description": "Event type identifier. Maps to WorkflowEventType in events.py."
    },
    "run_id": {
      "type": "string",
      "description": "Unique identifier for this workflow execution run."
    },
    "workflow_name": {
      "type": "string",
      "description": "Name of the workflow definition. Shared across multiple runs."
    },
    "timestamp": {
      "type": "number",
      "format": "double",
      "description": "Unix epoch timestamp (seconds with fractional component) when the event was created."
    },
    "step_id": {
      "type": "string",
      "description": "Step identifier. Present only for step-scoped events (step_started, step_completed, step_failed, step_skipped, step_retrying). Absent for workflow-level and heartbeat events.",
      "nullable": true
    },
    "data": {
      "type": "object",
      "additionalProperties": true,
      "description": "Event-specific payload. Absent when there is no additional data."
    },
    "schema_version": {
      "type": "integer",
      "enum": [1],
      "description": "Schema version. Always 1 for v1 events."
    }
  }
}
```
