# Orchestrator Start Here

This directory defines a model-agnostic orchestration system. Any LLM or human agent can follow the same protocol.

## Entry Points
- `handoff/STATUS.md`: quick repo context and runtime notes.
- `handoff/PLAN.md`: goals, constraints, and success criteria.
- `handoff/TASKS.md`: task queue and status.
- `handoff/DECISIONS.md`: architectural decisions.
- `handoff/PRIORITIES.md`: rolling priorities view.
- `OPERATOR_MANUAL.md`: step-by-step operating guide.
- `AGENT_ROUTING_MAP.md`: which roles to invoke by task type.
- `CHEAT_SHEET.md`: one-page quick reference.
- `analysis/ORCHESTRATION_META_ANALYSIS.md`: system health and improvement plan.

## Core Rules
- `prompts/SYSTEM.md`: global rules for all agents.
- `prompts/WORKER_RULES.md`: implementation worker behavior.
- `PROMPT_PACK.md`: copy/paste prompts for orchestrator, workers, and reviewer.
- `agents/*.md`: agent role rules (orchestrator, director, reviewer, worker).

## Workflow
1) Read STATUS → PLAN → TASKS.
2) Pick or create a task with explicit acceptance criteria.
3) Implement minimal changes; run tests or document why not.
4) Capture review output and verification evidence in TASKS.
5) Log decisions in DECISIONS when needed.

## Quickstart
1) Open `handoff/STATUS.md` to confirm runtime assumptions.
2) Read `handoff/PLAN.md` for objectives and constraints.
3) Check `handoff/PRIORITIES.md` and pick a task from `handoff/TASKS.md`.
4) If risk triggers apply, use `handoff/REVIEW_CAPTURE.md` and `handoff/REVIEW_CHECKLIST.md`.
5) Capture evidence with `handoff/EVIDENCE_CAPTURE.md`.
6) Close the task using `handoff/DEFINITION_OF_DONE.md`.

## Task Evidence Quick Checklist
- Commands recorded
- Tests recorded
- Artifacts linked
- Review outcomes captured (if applicable)

## Model-Agnostic Principle
All guidance here avoids model-specific assumptions. If a tool or model is required for a task, document it in TASKS.

## Review Capture vs Evidence Capture
- Use `handoff/REVIEW_CAPTURE.md` for reviewer findings and required changes.
- Use `handoff/EVIDENCE_CAPTURE.md` for commands, test results, and artifacts.

## Session Logs
- Store orchestration session wraps in `core/orchestrator/handoff/SESSION_WRAP.md`.
- If using repo-specific session logs, document the path in STATUS.md.
