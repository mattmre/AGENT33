# TASKS

## Queue (unassigned)
- [ ] T1: Create/update orchestration protocol files in repo and validate Qwen Code tool usage.
- [ ] T2: Add warmup/pin script and confirm model stays hot for 30+ minutes.
- [ ] T3: Run a small “real task” in this repo (e.g., improve scripts, README, add diagnostics).

## In Progress
- [ ] (agent) T#: status / notes / blockers

## Done
- [x] Bootstrap orchestration files created (this commit)

## Task Template
When you pick a task:
1) Create branch: 	ask/T#-short-name
2) Update TASKS.md In Progress line with your agent name + timestamp
3) Implement minimal changes
4) Run checks/tests (or explain why not possible)
5) Capture reviewer output (if risk triggers apply) using `handoff/REVIEW_CAPTURE.md`
6) Confirm Definition of Done checklist: `handoff/DEFINITION_OF_DONE.md`
7) Commit with message: T#: <summary>
8) Update TASKS Done with summary + commit hash + verification evidence

## Minimum Task Payload
- ID and title
- Owner and start date
- Acceptance criteria
- Verification steps
- Reviewer required (yes/no)

## Acceptance Criteria Examples
- "CLI command exits 0 and produces expected output file."
- "Unit tests for module X pass; new test covers edge case Y."
- "Documentation updated for new flag; examples added."

## Status Update Template
- Status:
- Progress:
- Blockers:
- Next action:
