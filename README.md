# AGENT 33

AGENT 33 is the master aggregation repo for agentic workflows, orchestration docs, and agent assets harvested from active projects.

## Layout
- `collected/`: Raw ingest of docs/agent folders from each repo.
- `manifest.md`: Audit log of what was collected and where it lives.

## Purpose
- Centralize agentic workflows and orchestration patterns.
- Normalize and de-duplicate across projects.
- Publish a stable, reusable 'queen bee' workflow system.

## Update Strategy
1) Ingest new/updated agent assets from repos.
2) De-duplicate into a canonical `core/` area (to be created).
3) Update downstream repos from `core/` via controlled sync.

## Notes
- Raw ingest remains untouched for traceability.
- Canonical content lives outside `collected/`.
