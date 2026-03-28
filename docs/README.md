# AGENT-33 Documentation

Last updated: March 28, 2026.

This `docs/` directory is the canonical documentation set for AGENT-33.

## Start Here

1. [Setup Guide](setup-guide.md)
2. [Walkthroughs](walkthroughs.md)
3. [Phase 25/26 Live Review Walkthrough](phase25-26-live-review-walkthrough.md)
4. [Operator Guide: Improvement Cycles and Docker Kernels](operator-improvement-cycle-and-jupyter.md)
5. [Production Deployment Runbook](operators/production-deployment-runbook.md)
6. [Operator Verification Runbook](operators/operator-verification-runbook.md)
7. [Process Registry Runbook](operators/process-registry-runbook.md)
8. [Horizontal Scaling Architecture](operators/horizontal-scaling-architecture.md)
9. [Incident Response Playbooks](operators/incident-response-playbooks.md)
10. [Service Level Objectives](operators/service-level-objectives.md)
11. [Phase 22 Surface Validation](validation/phase22-phase25-27-surface-validation.md)
12. [Use Cases](use-cases.md)
13. [Functionality and Workflows](functionality-and-workflows.md)
14. [API Surface](api-surface.md)
15. [PR Review (2026-02-15)](pr-review-2026-02-15.md)
16. [Phase 22 Progress Log](progress/phase-22-ui-log.md)
17. [Phase 22 PR Checkpoints](prs/README.md)

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
| `operators/production-deployment-runbook.md` | Current Kubernetes production rollout, verification, monitoring, and rollback guidance for the shipped deploy baseline |
| `operators/operator-verification-runbook.md` | Canonical authenticated verification order for operator status, doctor, process inventory, and backup safety checks |
| `operators/process-registry-runbook.md` | Current `/v1/processes` contract, restart-to-`interrupted` recovery path, and bounded cleanup guidance |
| `operators/horizontal-scaling-architecture.md` | Current replica-safety contract, state-boundary map, blocking globals, and `P1.2` migration sequence for multi-replica rollout |
| `operators/incident-response-playbooks.md` | First incident-response playbooks for API outages, degraded dependencies, evaluation regressions, and webhook backlog incidents |
| `operators/service-level-objectives.md` | Current internal SLO baseline, error-budget policy, guardrail mapping, and deferred-objective inventory |
| `validation/phase22-phase25-27-surface-validation.md` | Evidence-backed validation record for the Phase 22 extension surfaces introduced by the Phase 25-27 stack |
| `use-cases.md` | Practical implementation patterns with module requirements and tradeoffs |
| `functionality-and-workflows.md` | Current functionality inventory, lifecycle/state flows, and persistence boundaries |
| `api-surface.md` | Complete endpoint map with auth/scope requirements |
| `pr-review-2026-02-15.md` | Review of PR #1 through PR #12 with merged/open impact assessment |

## Legacy and Supporting Material

Existing documents under `engine/docs/`, `core/`, and `docs/phases/` remain useful as deep reference material. Use this `docs/` set first when you need current runtime behavior and operational guidance.
