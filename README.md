# AGENT-33

Autonomous AI agent orchestration engine with a local-first runtime, explicit governance, and extensible workflow automation.

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

## Repository Layout

- `engine/`: FastAPI runtime, API routes, orchestration services, tests
- `frontend/`: first-party AGENT-33 control plane UI
- `core/`: orchestration specifications, protocol references, policy packs
- `docs/`: canonical operational documentation for current runtime behavior

## Quick Start

```bash
cd engine
cp .env.example .env
docker compose up -d
curl http://localhost:8000/health
```

If reusing an Ollama container from another compose project (no host port mapping),
start with the shared-network override:

```bash
docker compose -f docker-compose.yml -f docker-compose.shared-ollama.yml up -d
```

Open the control plane UI:

- `http://localhost:3000`

Default local credentials (from `.env.example`):
- username: `admin`
- password: `admin`

**⚠️ Security Warning:** The bootstrap authentication (`admin/admin`) is for local development only and must not be used in production environments. For production or VPS deployments, disable bootstrap auth (`AUTH_BOOTSTRAP_ENABLED=false`) and configure a proper identity provider or token issuing mechanism.

Generate a local development JWT (1 hour):

```bash
docker compose exec -T api python -c "import os,time,jwt; now=int(time.time()); payload={'sub':'local-admin','scopes':['admin','agents:read','agents:write','agents:invoke','workflows:read','workflows:write','workflows:execute','tools:execute'],'iat':now,'exp':now+3600}; print(jwt.encode(payload, os.getenv('JWT_SECRET','change-me-in-production'), algorithm=os.getenv('JWT_ALGORITHM','HS256')))"
```

Call a protected endpoint:

```bash
export TOKEN="<paste-token-here>"
curl http://localhost:8000/v1/agents/ -H "Authorization: Bearer $TOKEN"
```

## Documentation

Start here:

- [Documentation Index](docs/README.md)
- [Setup Guide](docs/setup-guide.md)
- [Walkthroughs](docs/walkthroughs.md)
- [Use Cases](docs/use-cases.md)
- [Functionality and Workflows](docs/functionality-and-workflows.md)
- [API Surface](docs/api-surface.md)
- [PR Review (2026-02-15)](docs/pr-review-2026-02-15.md)

Reference material:

- `engine/docs/`
- `core/`
- `docs/phases/`

## Current Status

The project is under active development on the unified UI platform branch. Core capabilities include agent orchestration, workflow execution, memory/RAG, and operational automation (reviews, releases, evaluations, autonomy budgets, improvements).

For a historical snapshot of PR review activity as of February 15, 2026, see `docs/pr-review-2026-02-15.md`.

## License

MIT. See [LICENSE](LICENSE).
