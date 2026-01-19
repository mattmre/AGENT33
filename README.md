# AGENT 33

AGENT 33 is the master aggregation repo for model-agnostic agentic workflows, orchestration docs, and reusable agent assets collected from active projects.

## Purpose
- Centralize orchestration patterns and agent guidance across repos.
- Normalize and de-duplicate into a canonical core.
- Keep raw ingests immutable for traceability.

## Principles
- Model-agnostic: guidance does not assume a specific model or tool.
- Evidence-first: tasks must capture commands, outcomes, and review results.
- Minimal diffs: changes stay scoped to acceptance criteria.
- Auditability: decisions and verification are logged.
- Review-driven improvement: changes are guided by PR comments from diverse AI code reviewers and humans, with agentic follow-up to adapt and refine.
- Tool-agnostic reviews: review inputs can come from any AI or human process; the system must not depend on a single vendor or API.

## Specifications (Core System)
- Handoff protocol: PLAN, TASKS, STATUS, DECISIONS, PRIORITIES.
- Roles: Director, Orchestrator, Worker (Impl/QA), Reviewer, Researcher, Documentation.
- Risk triggers: security, schema, API, CI/CD, large refactors require review.
- Evidence capture: commands, tests, artifacts, and review outcomes.
- Workflow promotion: only reusable templates move from sources to canonical.
- Review intake: PR comments and review notes feed backlog expansion and refinement workflows.

## Repo Layout
- `collected/`: raw ingest from source repos (do not edit).
- `core/`: canonical, de-duplicated system (authoritative).
- `docs/`: local planning artifacts (session notes, phase planning).
- `manifest.md`: ingest audit log.
- `dedup-policy.md`: canonicalization rules.

## How to Use
1) Start at `core/ORCHESTRATION_INDEX.md`.
2) Follow `core/orchestrator/README.md` and `core/orchestrator/OPERATOR_MANUAL.md`.
3) Use `core/arch/workflow.md` for AEP cycles.
4) Promote or archive workflow assets using `core/workflows/PROMOTION_CRITERIA.md`.
5) Use PR reviews (human + AI) as structured inputs to backlog updates and follow-up tasks.

## Review Workflow (Human + AI)
1) Open a PR with clear scope and test evidence.
2) Collect review comments from humans and multiple AI reviewers.
3) Classify findings by severity (blocker/major/minor/nit) and assign owners.
4) Convert accepted findings into backlog items with acceptance criteria.
5) Implement fixes in small, evidence-backed diffs.
6) Update verification logs and close the loop in the PR thread.

## Update Lifecycle
1) Ingest assets into `collected/`.
2) Deduplicate into `core/` with decisions logged in `core/CHANGELOG.md`.
3) Keep `core/` model-agnostic and reusable across repos.
