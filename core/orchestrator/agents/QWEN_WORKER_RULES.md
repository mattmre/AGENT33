# Worker Rules (Model-Agnostic)

## Default Output Format
1) Plan (3-6 bullets max)
2) Commands to run
3) Unified diff (or explicit file edits)
4) Verification results (tests/build) + short status

## Boundaries
- Do NOT rewrite unrelated files.
- Do NOT reformat the whole codebase.
- Keep diffs tight and scoped to the task.

## When blocked
Write:
- BLOCKED: <why>
- NEED: <what is required>
- NEXT: <specific next action>

## Git
- Always use a branch per task: ask/T#-short-name
- Commit messages: T#: <summary>
- Update orchestrator/handoff/TASKS.md after each milestone.
