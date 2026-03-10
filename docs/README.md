# AGENT-33 Documentation

Last updated: March 9, 2026.

This `docs/` directory is the canonical documentation set for AGENT-33.

## Start Here

1. [Setup Guide](setup-guide.md)
2. [Walkthroughs](walkthroughs.md)
3. [Phase 25/26 Live Review Walkthrough](phase25-26-live-review-walkthrough.md)
4. [Operator Guide: Improvement Cycles and Docker Kernels](operator-improvement-cycle-and-jupyter.md)
5. [Phase 22 Surface Validation](validation/phase22-phase25-27-surface-validation.md)
6. [Use Cases](use-cases.md)
7. [Functionality and Workflows](functionality-and-workflows.md)
8. [API Surface](api-surface.md)
9. [PR Review (2026-02-15)](pr-review-2026-02-15.md)
10. [Phase 22 Progress Log](progress/phase-22-ui-log.md)
11. [Phase 22 PR Checkpoints](prs/README.md)

## Runtime Snapshot

- Runtime entry point: `engine/src/agent33/main.py`
- API prefixes: `/health`, `/v1/*`
- Auth model: middleware-enforced auth + scope checks on selected endpoints (dashboard routes are public for local operator visibility)
- Data stores: PostgreSQL/pgvector, Redis, NATS, plus several in-memory services
- Default deployment: Docker Compose stack in `engine/docker-compose.yml`
- Frontend control plane: `frontend/` (served by compose at `http://localhost:3000`)

## Guide Map

| Document | Purpose |
| --- | --- |
| `setup-guide.md` | End-to-end environment setup, auth bootstrap, and first successful requests |
| `walkthroughs.md` | Task-oriented walkthroughs across agents, workflows, memory, review, release, evaluation, autonomy, and improvement APIs |
| `phase25-26-live-review-walkthrough.md` | Operator guide for live workflow execution, review artifact generation, signoff, and tool approvals |
| `operator-improvement-cycle-and-jupyter.md` | Current operator path for the improvement-cycle wizard, canonical presets, and Docker-backed Jupyter execution |
| `validation/phase22-phase25-27-surface-validation.md` | Evidence-backed validation record for the Phase 22 extension surfaces introduced by the Phase 25-27 stack |
| `use-cases.md` | Practical implementation patterns with module requirements and tradeoffs |
| `functionality-and-workflows.md` | Current functionality inventory, lifecycle/state flows, and persistence boundaries |
| `api-surface.md` | Complete endpoint map with auth/scope requirements |
| `pr-review-2026-02-15.md` | Review of PR #1 through PR #12 with merged/open impact assessment |

## Legacy and Supporting Material

Existing documents under `engine/docs/`, `core/`, and `docs/phases/` remain useful as deep reference material. Use this `docs/` set first when you need current runtime behavior and operational guidance.
