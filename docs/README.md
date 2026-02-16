# AGENT-33 Documentation

Last updated: February 16, 2026.

This `docs/` directory is the canonical documentation set for AGENT-33.

## Start Here

1. [Setup Guide](setup-guide.md)
2. [Walkthroughs](walkthroughs.md)
3. [Use Cases](use-cases.md)
4. [Functionality and Workflows](functionality-and-workflows.md)
5. [API Surface](api-surface.md)
6. [PR Review (2026-02-15)](pr-review-2026-02-15.md)
7. [Phase 22 Progress Log](progress/phase-22-ui-log.md)
8. [Phase 22 PR Checkpoints](prs/README.md)

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
| `use-cases.md` | Practical implementation patterns with module requirements and tradeoffs |
| `functionality-and-workflows.md` | Current functionality inventory, lifecycle/state flows, and persistence boundaries |
| `api-surface.md` | Complete endpoint map with auth/scope requirements |
| `pr-review-2026-02-15.md` | Review of PR #1 through PR #12 with merged/open impact assessment |

## Legacy and Supporting Material

Existing documents under `engine/docs/`, `core/`, and `docs/phases/` remain useful as deep reference material. Use this `docs/` set first when you need current runtime behavior and operational guidance.
