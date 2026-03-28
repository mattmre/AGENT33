# Session 116 P5 Scope Lock: Lightweight Ingestion Task Artifacts

## Objective

Add one minimal, frontmatter-backed artifact format for repo-ingestion and remediation work
without creating a new ticketing layer or replacing the root planning files.

## Included

- A small markdown artifact contract with YAML frontmatter for:
  - stable task ID
  - owner
  - status
  - acceptance criteria
  - evidence
- One Python helper for parsing, rendering, and writing the artifact.
- One example artifact showing a repo-ingestion effort tracked end to end.
- Usage guidance wired into the existing `platform-builder/repo-ingestor` skill.

## Non-goals

- No CAR-style control plane, queue, or approval system.
- No replacement of `task_plan.md`, `findings.md`, or `progress.md`.
- No ingestion dashboard, operator API, or workflow-engine persistence change.
- No attempt to generalize the artifact to every workflow in the repo.

## Relationship To Existing Planning Files

- `task_plan.md` remains the session queue and merge-order source of truth.
- `findings.md` remains the research/discovery log.
- `progress.md` remains the execution log.
- The ingestion artifact exists only to keep one repo-ingestion or remediation unit durable,
  linkable, and auditable across those files without duplicating the full queue.

## Planned Validation

- Round-trip parse/render tests for the artifact helper.
- File write/load test for the artifact helper.
- Example/template checks so the docs keep the required fields and planning references.
