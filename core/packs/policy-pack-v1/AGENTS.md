# AGENTS.md (Policy Pack v1)

Purpose: Provide a model-agnostic baseline for how agents should operate in any repo.

## Core Principles
- Evidence-first: capture commands, outputs, artifacts, and review outcomes.
- Minimal diffs: keep changes scoped to the task acceptance criteria.
- Spec-first: require goals, non-goals, assumptions, and acceptance checks.
- Safe-by-default: no network or destructive actions without approval.

## Required Artifacts
- PLAN, TASKS, STATUS, DECISIONS, PRIORITIES
- Evidence capture (commands + outcomes)
- Review capture when risk triggers apply

## Autonomy Budget
- Scope: allowed files/paths and max diff size.
- Commands: explicit allowlist.
- Network: off by default; allowlist if approved.
- Stop conditions: ambiguity, failing tests, scope expansion.
