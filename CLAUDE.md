# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AGENT-33 is a multi-agent orchestration framework with a governance layer, evidence capture, and session-spanning workflows. The repo has two main layers:

- `core/` — Framework specifications, orchestrator rules, workflow templates (Markdown-native, no runtime)
- `engine/` — Python/FastAPI runtime engine (the actual software)

## Common Commands

All engine commands run from `engine/`:

```bash
# Tests
python -m pytest tests/ -q                          # full suite (~197 tests)
python -m pytest tests/test_execution_executor.py -q  # single test file
python -m pytest tests/ -k "test_name" -q           # single test by name
python -m pytest tests/ -x -q                       # stop on first failure

# Lint & format
python -m ruff check src/ tests/                    # lint (0 errors expected)
python -m ruff check --fix src/ tests/              # auto-fix
python -m ruff format src/ tests/                   # format
mypy src/                                           # type check (strict)

# Docker (from engine/)
docker compose up -d                                # start all services
docker compose up -d postgres redis nats ollama     # infra only (for local dev)
uvicorn agent33.main:app --reload --host 0.0.0.0 --port 8000  # local dev server

# CLI
pip install -e ".[dev]"                             # install in dev mode
agent33 status                                      # health check
```

## Architecture

### Engine Package Layout (`engine/src/agent33/`)

**Entry point**: `main.py` — FastAPI app with lifespan that initializes DB, Redis, NATS, agent registry, code executor, agent-workflow bridge, AirLLM, memory, and training subsystems.

**Config**: `config.py` — Pydantic Settings, `env_prefix=""`, loads from `.env`. Variable names map directly to uppercase env vars.

**Key subsystems**:
- `agents/` — Agent registry (`registry.py` auto-discovers JSON defs from `agent_definitions_dir`), definition model, runtime (prompt construction + LLM invocation)
- `workflows/` — DAG-based workflow engine: definition model, topological sort, step executor with retries/timeouts, expression evaluator, state machine, checkpoint persistence. Actions in `actions/` (invoke_agent, run_command, validate, transform, conditional, parallel_group, wait, execute_code)
- `execution/` — Code execution layer (Phase 13): `models.py` (SandboxConfig, ExecutionContract, ExecutionResult), `validation.py` (IV-01..05 input validation), `adapters/` (BaseAdapter, CLIAdapter with subprocess), `executor.py` (CodeExecutor pipeline), `disclosure.py` (progressive disclosure L0-L3)
- `llm/` — Provider abstraction: Ollama, OpenAI-compatible, ModelRouter
- `memory/` — Short-term buffer, pgvector long-term store, embeddings, RAG pipeline, session state, ingestion, retention
- `security/` — JWT/API-key auth, AuthMiddleware, encryption, vault, permissions, prompt injection detection, allowlists
- `tools/` — Tool framework: registry, governance/allowlist enforcement, builtins (shell, file_ops, web_fetch, browser)
- `messaging/` — External integrations (Telegram, Discord, Slack, WhatsApp) via NATS bus
- `automation/` — APScheduler, webhooks, dead-letter queue, event sensors
- `review/` — Two-layer review automation (Phase 15): risk assessment, reviewer assignment, signoff state machine, review service, API endpoints
- `observability/` — structlog, tracing, metrics, lineage, replay, alerts

### Multi-Tenancy

AuthMiddleware resolves tenant from API key or JWT. All DB models have `tenant_id`. Route tests that don't provide auth will get 401.

### Agent Definitions

6 JSON files in `engine/agent-definitions/` (orchestrator, director, code-worker, qa, researcher, browser-agent). Auto-discovered at startup via `agent_definitions_dir` config. Capability taxonomy: 25 entries across P/I/V/R/X categories in `agents/capabilities.py`.

### Agent Routes DI Pattern

Routes use `Depends(get_registry)` which reads from `app.state.agent_registry`. The workflow bridge (`invoke_agent.py`) has `set_definition_registry()` as a fallback.

## Tool Configuration

- **Build**: hatchling (`pyproject.toml`)
- **Python**: >=3.11
- **Ruff**: line-length 99, target py311, rule sets: E, F, W, I, N, UP, B, A, SIM, TCH
- **mypy**: strict mode, pydantic plugin
- **pytest**: `asyncio_mode = "auto"`, `testpaths = ["tests"]`
- **DB migrations**: Alembic in `engine/alembic/versions/`

## Development Phases

Phase plans live in `docs/phases/`. Phases 1-15 and 21 are complete. Phases 16-20 are planned. See `docs/phases/README.md` for the index and `docs/next-session.md` for current priorities.

### Phase Dependency Chain (11-20)
11 (Agent Registry) → 12 (Tool Registry) → 13 (Code Execution) → 14 (Security Hardening) → 15 (Review Automation) → 16 (Observability) → 17 (Evaluation Gates) → 18 (Autonomy Enforcement) → 19 (Release Automation) → 20 (Continuous Improvement)

## Windows Platform Notes

- `create_subprocess_shell` doesn't raise `FileNotFoundError` — detect missing commands via stderr "is not recognized" pattern
- Use `subprocess.list2cmdline()` for proper quoting
- Merge env with `os.environ` to preserve PATH when spawning subprocesses

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

### Pre-Commit Checklist Additions

Add these to your existing pre-commit checklist:

- [ ] New tests exercise real behavior (validation, response shapes, error
      paths) — not just route existence or infrastructure errors
- [ ] Any deviation from the approved plan is called out in the same message
      where it occurs, with a proposal to close the gap
- [ ] No placeholder values shipped unresolved (search for TODOs, hardcoded IDs
      used as display text, comments saying "will be resolved later")
- [ ] If the plan specified client-server wiring, verify the client actually
      calls the server endpoint (not a direct DB query or local mock)
