# Command Registry

This registry defines all available commands in the AGENT-33 orchestration framework.

## Schema

Each command definition follows this schema:

```yaml
id: string           # Unique identifier (lowercase, no prefix)
name: string         # Display name with / prefix
description: string  # Brief purpose statement
workflow: string     # Path to workflow specification
triggers:            # What invokes this command
  - manual           # Operator-initiated
  - scheduled        # Time-based
  - event            # Triggered by system event
inputs:              # Required context documents
  - document: string # Handoff doc path
    required: bool   # Whether mandatory
outputs:             # Produced artifacts
  - document: string # Output path or pattern
    action: string   # create | update | append
```

---

## Registered Commands

### /status

| Field | Value |
|-------|-------|
| id | `status` |
| name | `/status` |
| description | Review current STATUS.md and surface blockers |
| workflow | `commands/status.md` |
| triggers | manual |
| inputs | `handoff/STATUS.md`, `handoff/TASKS.md`, `handoff/PLAN.md` |
| outputs | Summary report (stdout) |

---

### /tasks

| Field | Value |
|-------|-------|
| id | `tasks` |
| name | `/tasks` |
| description | List open tasks from TASKS.md with priorities |
| workflow | `commands/tasks.md` |
| triggers | manual |
| inputs | `handoff/TASKS.md`, `handoff/PRIORITIES.md` |
| outputs | Task list (stdout) |

---

### /verify

| Field | Value |
|-------|-------|
| id | `verify` |
| name | `/verify` |
| description | Capture verification evidence for current task |
| workflow | `commands/verify.md` |
| triggers | manual |
| inputs | Current task context, test commands |
| outputs | `verification-log.md` (append) |

---

### /handoff

| Field | Value |
|-------|-------|
| id | `handoff` |
| name | `/handoff` |
| description | Generate session wrap summary for next session |
| workflow | `commands/handoff.md` |
| triggers | manual |
| inputs | `handoff/STATUS.md`, `handoff/TASKS.md`, `handoff/DECISIONS.md` |
| outputs | `handoff/SESSION_WRAP.md` (append) |

---

### /plan

| Field | Value |
|-------|-------|
| id | `plan` |
| name | `/plan` |
| description | Create implementation plan with confirmation wait |
| workflow | `commands/plan.md` |
| triggers | manual |
| inputs | User request, `handoff/TASKS.md` |
| outputs | `handoff/PLAN.md` (update) |

---

### /review

| Field | Value |
|-------|-------|
| id | `review` |
| name | `/review` |
| description | Trigger code review workflow |
| workflow | `commands/review.md` |
| triggers | manual, event (PR opened) |
| inputs | Code diff, `RISK_TRIGGERS.md` |
| outputs | `handoff/REVIEW_CAPTURE.md` (append) |

---

## Adding New Commands

1. Create command specification in `commands/<id>.md`
2. Add entry to this registry following the schema
3. Update `core/ORCHESTRATION_INDEX.md` if command affects orchestration flow
4. Document any new handoff artifacts in `core/orchestrator/handoff/`

## Related Documents

- `commands/README.md`: Commands specification
- `core/ORCHESTRATION_INDEX.md`: Orchestration index
- `core/orchestrator/AGENT_ROUTING_MAP.md`: Role routing
