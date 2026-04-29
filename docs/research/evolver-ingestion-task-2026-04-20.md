---
task_id: ING-20260420-evolver-adaptation
kind: ingestion
title: Adapt Evolver patterns into AGENT33 clean-room workflows
owner: codex
status: completed
target: EvoMap/evolver
summary: >
  Compare EvoMap/evolver against AGENT33 and define a clean-room adaptation
  boundary that captures the best architectural and workflow ideas without
  ingesting GPL-governed code or collapsing AGENT33 into Evolver's monolithic
  runtime shape.
acceptance_criteria:
  - Publish the comparison report and explicit adoption boundary.
  - Record the direct-code prohibition and identified non-goals.
  - Convert the best findings into a phased sprint plan for future AGENT33 work.
evidence:
  - docs/research/evolver-adaptive-ingestion-2026-04-20.md
planning_refs:
  - task_plan.md
  - findings.md
  - progress.md
research_refs:
  - docs/research/evolver-adaptive-ingestion-2026-04-20.md
  - docs/research/session116-p5-ingestion-artifacts-scope.md
created_at: 2026-04-20T21:13:16-04:00
updated_at: 2026-04-21T23:59:00-04:00
---

# Outcome

AGENT33 should adopt Evolver’s best ideas only as **clean-room concepts**:
candidate intake with confidence downgrading for imported material, append-only
operational journals, heartbeat/task metrics, a thin proxy/mailbox seam, and
clear lifecycle verbs. The deeper code round confirmed these are the real
transferable strengths; direct runtime adoption is out of bounds because
Evolver presents conflicting license signals, committed obfuscated source, and
self-mutating repair behavior that do not fit AGENT33’s governance model.

## Notes

- AGENT33 is already stronger in modularity, durable planning, and operator/UI
  structure; the plan intentionally preserves those strengths.
- The recommended first implementation slice is governed external-asset
  candidate intake plus publication gating and evidence journaling; the next
  slice after that is a narrow mailbox/heartbeat pilot rather than a
  self-modifying runtime or hub-dependent architecture.

## Deferred Follow-ups

- Revisit direct reuse only if Evolver’s licensing becomes unambiguous and
  AGENT33 still needs code-level parity after the clean-room adaptation wave.
- Do not revisit any direct runtime reuse while obfuscated committed source or
  self-mutating repair patterns remain part of the upstream implementation.
