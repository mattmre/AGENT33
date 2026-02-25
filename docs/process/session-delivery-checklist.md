# Session Delivery Checklist (Operational Discipline)

Use this checklist for every delivery session to enforce CLAUDE anti-corner-cutting expectations and consistent PR hygiene.

## 1) Scope and Integrity Guardrails

1. Re-state session scope before editing; explicitly call out in-scope vs out-of-scope files.
2. Apply minimal, surgical changes only; avoid opportunistic refactors.
3. Do not claim runtime/test execution that did not occur in-session.
4. Preserve validated baselines and command groups unless fresh evidence requires updates.

## 2) Proactive Deviation Reporting

1. Report count/result drift immediately when discovered (example: 332 vs 339 aggregate mismatch).
2. Record source of truth and where drift appeared (session log, review packet, or handoff note).
3. Reconcile drift in the same wave with a clear “locked baseline” statement and follow-up action.
4. Never silently overwrite historical evidence to make counts appear consistent.

## 3) Test-Quality Strictness

1. Use the required smoke command groups as merge gates, not optional samples.
2. Treat skipped tests as explicit evidence; include them in aggregate accounting.
3. If no tests are run in the current wave, state that clearly and reference prior validated evidence.
4. Reject “looks good” validation language without command-level output alignment.

## 4) Session PR Discipline

1. Keep PR scope coherent (single objective per PR sequence position).
2. Keep merge sequencing labels and dependencies explicit (`sequence:1/2/3` when applicable).
3. Ensure each session note maps changes to files, validation evidence, and intended PR placement.
4. Block handoff if review packet updates, validation snapshot alignment, or sequencing notes are missing.

## 5) Handoff Readiness Check

- [ ] Scope respected; no unauthorized runtime/test edits.
- [ ] Deviation reporting completed and documented.
- [ ] Validation baseline reference is explicit and consistent.
- [ ] Session notes and next-session priorities are updated.
- [ ] Reviewer handoff contains file list, status, and follow-up notes.
