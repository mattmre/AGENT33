# Retrospective Improvement Workflow Template

> **Intended location**: `core/workflows/improvement-cycle/template-retrospective.md`
> Move this file once the `improvement-cycle/` directory is created.

## Purpose

Structured template for conducting a retrospective improvement cycle after a session, sprint, or release. Captures what went well, what didn't, and produces concrete action items for the next iteration.

## Invocation

Run this workflow at the end of each session or milestone boundary.

## Inputs

| Input | Required | Description |
|-------|----------|-------------|
| session_id | Yes | Session or sprint identifier being reviewed |
| scope | No | Subset of work to focus on (e.g., "frontend", "backend", "operations") |
| participants | No | Agents or roles involved in the retrospective |

## Workflow

### 1. Gather Evidence

Collect artifacts from the completed session:
- Commits and PRs merged
- Issues resolved vs. remaining
- Test results and coverage deltas
- Build/deploy outcomes
- Any incident or regression reports

### 2. Assess What Went Well

Identify positive patterns worth reinforcing:
- [ ] Smooth handoffs between agents
- [ ] Effective test coverage
- [ ] Clean PR reviews with minimal rework
- [ ] On-time delivery against plan
- [ ] Good domain config / backend alignment

### 3. Assess What Needs Improvement

Identify friction points and failures:
- [ ] Stale code or dead imports discovered late
- [ ] API path mismatches between frontend and backend
- [ ] Missing or inadequate tests
- [ ] Unclear ownership of files or features
- [ ] Excessive rework during review

### 4. Root Cause Analysis

For each improvement area, document:

| Issue | Root Cause | Severity | Recurrence Risk |
|-------|-----------|----------|-----------------|
| [description] | [why it happened] | Low/Medium/High | Low/Medium/High |

### 5. Generate Action Items

Produce concrete, assignable actions:

| Action | Owner | Priority | Target Session |
|--------|-------|----------|----------------|
| [action description] | [agent/role] | P0/P1/P2 | [session id] |

### 6. Update Process Docs

If the retrospective reveals a systemic issue, update the relevant process document:
- Workflow templates
- Review checklists
- Agent routing maps
- Risk trigger definitions

## Outputs

| Output | Destination | Action |
|--------|-------------|--------|
| Retrospective summary | `docs/session-logs/` | Create session retro doc |
| Action items | `TASKS.md` or issue tracker | Append as new tasks |
| Process updates | Relevant `core/` docs | Edit in place |

## Completion Criteria

- All sections filled in with specific observations (no generic placeholders)
- At least one concrete action item per improvement area
- Action items have owners and target sessions assigned
- Any process doc updates committed

## Related Documents

- `core/workflows/commands/review.md` — Review workflow
- `core/workflows/commands/status.md` — Status tracking
- `core/workflows/improvement-cycle-metrics-review.md` — Metrics-focused review
