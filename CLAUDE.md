# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

AGENT-33 is an autonomous AI agent orchestration engine — local-first, model-agnostic, fully open. It combines a specification framework (`core/`) with a Python runtime (`engine/`) built on FastAPI. The spec layer defines orchestration patterns, agent roles, and governance rules. The engine implements those patterns with LLM routing, DAG workflow execution, RAG memory, multi-tenant isolation, and an Observatory dashboard for real-time knowledge ingestion visualization.

## Development Commands

All engine commands run from `engine/`. Install dev dependencies first: `pip install -e ".[dev]"`

```bash
# Docker (full stack)
cd engine && docker compose up -d                    # Start all services
docker compose exec ollama ollama pull llama3.2      # Pull default model

# Local dev (infrastructure in Docker, API with hot reload)
docker compose up -d postgres redis nats ollama searxng
uvicorn agent33.main:app --reload --host 0.0.0.0 --port 8000

# Testing
pytest                                               # All unit tests
pytest tests/test_chat.py                            # Single test file
pytest tests/test_chat.py::test_chat_endpoint -v     # Single test
pytest -m integration                                # Integration tests only
pytest --cov=agent33 --cov-report=term-missing       # With coverage

# Linting and formatting
ruff check src/ tests/                               # Lint
ruff check --fix src/ tests/                         # Auto-fix
ruff format src/ tests/                              # Format
mypy src/                                            # Type check (strict mode)

# Make targets (from engine/)
make check                                           # lint + test
make fmt                                             # format + auto-fix
make dev                                             # hot-reload server
```

## Architecture

### Two-Layer Design

- **`core/`** — Specification framework: orchestrator protocols, agent role definitions, governance rules, workflow templates, architecture decision records. These are Markdown specs that inform engine behavior.
- **`engine/`** — Python runtime implementing the specs. Entry point: `engine/src/agent33/main.py` (FastAPI app with lifespan manager).

### Engine Module Map (`engine/src/agent33/`)

| Module | Purpose |
|--------|---------|
| `api/routes/` | FastAPI endpoints (health, chat, agents, workflows, auth, observatory, activity, sources, training, memory_search) |
| `llm/` | Provider abstraction with `router.py` selecting between Ollama (local), OpenAI (cloud), AirLLM (layer-sharded GPU) |
| `agents/` | Agent definition model, auto-discovery registry, prompt construction + LLM invocation runtime |
| `workflows/` | DAG engine: definition DSL, topological sort, parallel executor, state machine, checkpoint persistence, action types (invoke_agent, run_command, validate, transform, conditional, parallel_group, wait) |
| `memory/` | Short-term buffer, long-term pgvector store, RAG pipeline, progressive recall, session summarizer, embedding providers (Ollama, Jina) |
| `observatory/` | Knowledge graph service (`knowledge.py` — fact extraction, semantic search, content storage) and analytics (`stats.py`) |
| `ingestion/` | Content pipeline: abstract `BaseWorker` pattern with GDELT, RSS, YouTube workers. `IngestionCoordinator` manages lifecycle. Sources tracked with cursors for resuming |
| `db/` | SQLAlchemy async models (Tenant, ApiKey, Source, Fact, ActivityLog, IngestedContent) + session factory. All models include `tenant_id` |
| `tenancy/` | Multi-tenant middleware (resolves tenant from API key/JWT), per-tenant rate limiting (Redis token bucket), tenant CRUD service |
| `security/` | JWT + API key auth, Fernet encryption, prompt injection defense, RBAC permissions, tool allowlists |
| `messaging/` | Multi-platform adapters (Telegram, Discord, Slack, WhatsApp) + NATS internal message bus |
| `automation/` | APScheduler cron/interval, outbound webhooks, dead-letter queue, sensors (file_change, freshness, event) |
| `observability/` | structlog config, distributed tracing, Prometheus metrics, data lineage, workflow replay, alerting |
| `tools/` | Tool protocol with governance layer. Built-ins: shell, file_ops, web_fetch, browser (Playwright) |
| `training/` | Self-evolving loop: training store, evaluator, optimizer, algorithm selection, scheduling |
| `plugins/` | Python entry point discovery for extending tools, actions, and integrations |
| `cli/` | Typer-based CLI: `agent33 status`, `agent33 init`, `agent33 run` |

### Infrastructure Stack

PostgreSQL+pgvector (embeddings, checkpoints, long-term memory), Redis (session cache, rate limiting), NATS+JetStream (internal pub/sub), Ollama (local LLM), SearXNG (web search). Optional: n8n (integrations profile), AirLLM (gpu profile).

### Configuration

All settings in `engine/src/agent33/config.py` via Pydantic Settings — loaded from environment variables or `.env` file. No prefix (e.g., `OLLAMA_BASE_URL`, `DATABASE_URL`, `JWT_SECRET`).

### Database Migrations

Alembic in `engine/alembic/`. Two migrations: `001_initial.py` (base schema) and `002_observatory.py` (multi-tenant tables, knowledge graph).

### Observatory Frontend

Static HTML/JS/CSS in `engine/observatory/`. No build system — served directly by FastAPI. D3.js knowledge graph visualization, SSE-based real-time activity feed.

### Test Infrastructure

Tests in `engine/tests/`. `conftest.py` provides a `client` fixture (FastAPI TestClient). Async tests use `pytest-asyncio` with `asyncio_mode = "auto"`. Mark integration tests with `@pytest.mark.integration`. Test harnesses available in `engine/src/agent33/testing/` (agent_harness, workflow_harness, mock_llm).

## Conventions

- **Python 3.11+**, **Ruff** for linting (line length 99, rules: E/F/W/I/N/UP/B/A/SIM/TCH), **mypy strict** for type checking
- **Conventional commits**: `feat(engine):`, `fix(auth):`, `docs(readme):`, `test(workflows):`, `chore(deps):`
- **Branch naming**: `feat/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`
- Agent definitions are JSON files in `engine/agent-definitions/`, auto-discovered by the registry
- Workflow definitions in `engine/workflow-definitions/`

## Current State

- **Branch**: `feat/observatory-overhaul` — Observatory dashboard, ingestion pipeline, multi-tenancy, knowledge graph
- **Open PR #1** against `main` — reviewed by Gemini and Copilot with feedback on documentation traceability (broken file references in session logs, redundant task entries, hardcoded paths in verification log)
- **Phases 1-10** complete (core engine). **Phases 11-20** planned (see `docs/phases/` and `docs/ROADMAP.md`)

---

## Anti-Corner-Cutting Rules

These rules address a recurring pattern where AI agents silently deliver
shallow versions of planned work that appear complete (tests pass, files exist,
no errors) but don't fulfill the plan's actual intent.

### No Shallow Substitutions

When a plan specifies a deliverable, implement the actual deliverable — not a
superficially similar version that is easier to produce. Both outright omission
and quiet downgrading are forms of skipping. Common substitution patterns:

1. **Shallow tests disguised as real tests.** A plan says "test CRUD
   validation, auth flows, and error paths." The agent writes tests that only
   check routes return 503 or 401 without credentials. These tests verify
   infrastructure configuration, not feature behavior. They would not catch a
   single regression in the actual endpoint logic. **Every test must assert on
   behavior that would catch a real bug in the code under test.**

2. **Placeholder values never resolved.** A plan says "resolve article titles
   from data." The agent sets `title: articleId` with a comment "will be
   resolved by the component" — but no component ever resolves it. The feature
   ships showing raw UUIDs. **If a value needs resolution, the code that
   resolves it must exist in the same PR.**

3. **Direct calls instead of server endpoints.** A plan says "call server API
   for user list." The agent queries the database directly from the client,
   bypassing the server entirely. The server endpoint exists but is never
   called. **If the plan specifies a client-server interaction, both sides must
   be wired together.**

4. **Blocked work silently downgraded.** When a dependency is hard to mock or
   an infrastructure piece is missing, the agent quietly substitutes something
   easier instead of flagging the blocker. **If you cannot implement what the
   plan specifies, say so immediately — do not silently deliver less.**

5. **Asserting on two possible status codes.** Writing
   `assert(status === 503 || status === 401)` means the test doesn't know what
   the code actually does. This is a test that cannot fail and therefore tests
   nothing. **Each assertion must check one specific expected outcome.**

### Proactive Deviation Reporting

Any deviation from the approved plan must be called out **in the same message
where the deviation occurs**. Do not wait for the user to ask "did you cut any
corners?" — that question should never need to be asked. When a gap is created,
immediately include:

- What was specified in the plan
- What was actually delivered and why it differs
- A concrete proposal to close the gap (build mock infrastructure, split into
  follow-up task, etc.)

If you reach the end of implementation and the user has to interrogate you to
discover gaps, the process has failed regardless of whether the gaps are
eventually fixed.

### Test Quality Over Test Count

Test count is not a quality metric. Do not optimize for the number of tests
written. Do not present "X new tests" as evidence of completeness.

- A test that only verifies a route exists or returns a generic error has
  near-zero regression value
- Mock dependencies to reach the actual handler/component logic under test
- Assert on response shapes, validation errors, business rules, and state
  changes
- If mocking infrastructure doesn't exist to test something properly, you must
  either: (a) build the mock infrastructure, or (b) stop and tell the user what
  is missing before writing placeholder tests
- Never silently downgrade test quality
- When reviewing agent-written tests, verify they test what the plan specified,
  not just that they pass

### Pre-Commit Checklist

- [ ] New tests exercise real behavior (validation, response shapes, error
      paths) — not just route existence or infrastructure errors
- [ ] Any deviation from the approved plan is called out in the same message
      where it occurs, with a proposal to close the gap
- [ ] No placeholder values shipped unresolved (search for TODOs, hardcoded IDs
      used as display text, comments saying "will be resolved later")
- [ ] If the plan specified client-server wiring, verify the client actually
      calls the server endpoint (not a direct DB query or local mock)
