# Session 64 Docs Refresh — Operator Guide Gap

## Gap

The repo had the underlying implementation and validation evidence for:

- the improvement-cycle wizard
- canonical workflow presets
- Docker-backed Jupyter kernels

But the user-facing docs were still split across:

- Phase 25/26 live-review walkthroughs
- validation notes
- the Jupyter kernel runbook
- research documents and session logs

That made the merged operator experience hard to discover from `docs/README.md`.

## Decision

Add a single operator-facing guide that connects the UI entry point, preset catalog, and Docker kernel execution path, then surface it from the docs index and walkthrough map.

## Output

- `docs/operator-improvement-cycle-and-jupyter.md`
- `docs/README.md` index refresh
- `docs/walkthroughs.md` cross-link refresh
- `docs/runbooks/jupyter-kernel-containers.md` quick smoke workflow example
