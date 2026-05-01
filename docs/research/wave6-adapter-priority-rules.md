# Wave 6 adapter priority rules

Wave 6 cockpit adapters are frontend heuristics until backend run/session metadata can provide explicit primary artifact IDs. The rules below keep review surfaces deterministic without hiding secondary evidence.

## Artifact task priority

| Artifact | Rule | Rationale |
| --- | --- | --- |
| Plan | First `todo` task in board order | A plan should explain the next unstarted task, not completed work. |
| Command | First `running` task, otherwise first `blocked` task | Active execution is the primary command story. Blocked work only becomes primary when nothing is running. Additional running/blocked tasks remain visible through command blocks and logs. |
| Log | All `running` tasks | Logs are aggregate execution evidence, so multiple active lanes are expected. |
| Test | Reviewer-owned `review` task, otherwise first `review`, then first `complete` | Validation should privilege explicit reviewer work while still supporting builder-owned review gates and completed handoffs. |
| Risk | First `blocked` task | The first blocker is the primary recovery path; future backend metadata can rank blockers by severity. |
| Approval | First `blocked` task, otherwise first `review` task | Approval copy should explain the gate currently preventing progress. |
| Activity | All tasks | Activity/mailbox is the coordination feed, not a single primary artifact. |
| Outcome | First blocked task, otherwise explicit PR-ready completed task, generic PR completed task, then first completed task | A blocked state must stop the done-state narrative. PR-ready language outranks generic artifact packages. |

## Template starter validation

Workspace template starters must:

1. Exist for every workspace template.
2. Start from a task ID that exists in the current workspace board.
3. Assign the starter to the same role that owns the starting task.

This prevents beginner-facing starter CTAs from drifting away from the task board they claim to initialize.

## Deferred backend contract

Future backend persistence should replace these frontend heuristics with explicit fields such as `primaryArtifactTaskId`, `artifactPriority`, `runTraceId`, and `starterTemplateId`. Until then, the frontend rules above are covered by unit tests in:

- `frontend/src/data/cockpitArtifacts.test.ts`
- `frontend/src/data/workspaceTemplateStarters.test.ts`
