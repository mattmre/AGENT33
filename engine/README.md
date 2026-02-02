# AGENT-33 Engine

> **Looking for project-level docs?** See the [Documentation Hub](../docs/README.md) for quickstart, integration, deployment, and architecture guides. Key links: [Quick Start](../docs/QUICKSTART.md) | [Integration Guide](../docs/INTEGRATION-GUIDE.md) | [Deployment Guide](../docs/DEPLOYMENT.md)

The runtime engine for AGENT-33 -- an autonomous AI agent orchestration platform. This component provides the FastAPI server, workflow executor, agent runtime, LLM routing, memory/RAG pipeline, security layer, messaging integrations, and CLI tooling.

## Directory Structure

```
engine/
├── agent-definitions/         # JSON agent definition files (auto-discovered)
│   ├── orchestrator.json
│   └── worker.json
├── workflow-definitions/      # JSON/YAML workflow definition files
├── tool-definitions/          # External tool definition files
├── templates/                 # Jinja2 HTML templates (dashboard)
│   └── dashboard.html
├── src/agent33/               # Main Python package
│   ├── __init__.py
│   ├── config.py              # Pydantic Settings (all env vars)
│   ├── main.py                # FastAPI application entry point
│   ├── api/                   # HTTP layer
│   │   └── routes/
│   │       ├── health.py      # GET /health  (aggregate service checks)
│   │       ├── chat.py        # POST /api/v1/chat
│   │       ├── agents.py      # CRUD for agent definitions
│   │       ├── workflows.py   # CRUD + execute for workflows
│   │       ├── auth.py        # Login / token / API-key endpoints
│   │       ├── webhooks.py    # Inbound webhook receiver
│   │       └── dashboard.py   # HTML dashboard
│   ├── agents/                # Agent runtime
│   │   ├── definition.py      # AgentDefinition Pydantic model
│   │   ├── runtime.py         # Prompt construction + LLM invocation
│   │   └── registry.py        # Auto-discovery of agent JSON files
│   ├── workflows/             # Workflow engine
│   │   ├── definition.py      # WorkflowDefinition Pydantic model
│   │   ├── dag.py             # DAG builder + topological sort
│   │   ├── executor.py        # Step execution, retries, timeouts
│   │   ├── expressions.py     # Jinja-style expression evaluator
│   │   ├── state_machine.py   # Workflow state transitions
│   │   ├── checkpoint.py      # Checkpoint persistence (PostgreSQL)
│   │   └── actions/           # Built-in step actions
│   │       ├── invoke_agent.py
│   │       ├── run_command.py
│   │       ├── validate.py
│   │       ├── transform.py
│   │       ├── conditional.py
│   │       ├── parallel_group.py
│   │       └── wait.py
│   ├── llm/                   # LLM provider abstraction
│   │   ├── base.py            # LLMProvider protocol, ChatMessage, LLMResponse
│   │   ├── ollama.py          # Ollama HTTP provider
│   │   ├── openai.py          # OpenAI-compatible provider
│   │   └── router.py          # ModelRouter (selects provider per request)
│   ├── memory/                # Memory and RAG
│   │   ├── short_term.py      # In-process conversation buffer
│   │   ├── long_term.py       # pgvector-backed vector store
│   │   ├── embeddings.py      # Embedding provider abstraction
│   │   ├── rag.py             # Retrieval-Augmented Generation pipeline
│   │   ├── session.py         # Session state management
│   │   ├── context.py         # Context window assembly
│   │   ├── ingestion.py       # Document chunking + ingestion
│   │   └── retention.py       # TTL and eviction policies
│   ├── security/              # Auth, encryption, and policy
│   │   ├── auth.py            # JWT creation/verification, API keys
│   │   ├── middleware.py      # AuthMiddleware (Bearer + X-API-Key)
│   │   ├── encryption.py      # Fernet encryption at rest
│   │   ├── vault.py           # Secret management
│   │   ├── permissions.py     # Scope-based access control
│   │   ├── injection.py       # Prompt injection detection
│   │   └── allowlists.py      # Command/path/domain allowlists
│   ├── messaging/             # External messaging integrations
│   │   ├── base.py            # Messaging protocol
│   │   ├── models.py          # Shared message models
│   │   ├── bus.py             # NATSMessageBus (internal pub/sub)
│   │   ├── telegram.py
│   │   ├── discord.py
│   │   ├── slack.py
│   │   ├── whatsapp.py
│   │   └── pairing.py         # Channel pairing logic
│   ├── automation/            # Scheduling, webhooks, sensors
│   │   ├── scheduler.py       # APScheduler-based cron/interval
│   │   ├── webhooks.py        # Outbound webhook dispatch
│   │   ├── dead_letter.py     # Dead-letter queue handling
│   │   └── sensors/           # Event sensors
│   │       ├── file_change.py
│   │       ├── freshness.py
│   │       ├── event.py
│   │       └── registry.py
│   ├── tools/                 # Agent tool framework
│   │   ├── base.py            # Tool protocol, ToolContext, ToolResult
│   │   ├── registry.py        # Tool discovery and registration
│   │   ├── governance.py      # Allowlist enforcement
│   │   └── builtin/
│   │       ├── shell.py
│   │       ├── file_ops.py
│   │       ├── web_fetch.py
│   │       └── browser.py     # Playwright-based browser tool
│   ├── observability/         # Logging, tracing, metrics
│   │   ├── logging.py         # structlog configuration
│   │   ├── tracing.py         # Distributed trace propagation
│   │   ├── metrics.py         # Prometheus-style metrics
│   │   ├── lineage.py         # Data lineage tracking
│   │   ├── replay.py          # Workflow replay from events
│   │   └── alerts.py          # Alerting rules and dispatch
│   ├── testing/               # Test harnesses and mocks
│   │   └── __init__.py
│   └── cli/                   # Typer-based CLI
│       └── __init__.py
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── test_chat.py
│   ├── integration/
│   └── benchmarks/
├── docs/
│   ├── getting-started.md
│   ├── architecture.md
│   ├── contributing.md
│   └── api-reference.md
├── docker-compose.yml         # Development compose (all services)
├── docker-compose.prod.yml    # Production overlay (resource limits, no exposed ports)
├── Dockerfile                 # Multi-stage Python 3.11 image
├── Makefile                   # Developer convenience targets
├── pyproject.toml             # Build config, dependencies, tool settings
└── .env.example               # Template for environment variables
```

## Quick Start

```bash
# 1. Clone and enter the engine directory
git clone https://github.com/<owner>/agent-33.git
cd agent-33/engine

# 2. Create your environment file
cp .env.example .env

# 3. Start all services
docker compose up -d

# 4. Pull a default model into Ollama
docker compose exec ollama ollama pull llama3.2

# 5. Verify everything is running
curl http://localhost:8000/health
# {"status": "healthy", "services": {"ollama": "ok", "redis": "ok", "postgres": "ok", "nats": "ok"}}

# 6. Send your first chat message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, Agent-33!"}'
```

### Install the CLI

```bash
pip install -e ".[dev]"

agent33 status              # Check system health
agent33 init my-agent --kind agent      # Scaffold agent definition
agent33 init my-flow  --kind workflow   # Scaffold workflow definition
agent33 run my-flow --inputs '{"query": "test"}'  # Execute workflow
```

## Configuration

All settings are loaded from environment variables (or a `.env` file) via `src/agent33/config.py`. The `env_prefix` is empty, so variable names map directly to the field names in uppercase.

| Variable | Type | Default | Description |
|---|---|---|---|
| `API_PORT` | int | `8000` | Port the FastAPI server listens on |
| `API_LOG_LEVEL` | str | `info` | Uvicorn/structlog log level (`debug`, `info`, `warning`, `error`) |
| `API_SECRET_KEY` | str | `change-me-in-production` | Secret used for session signing |
| `OLLAMA_BASE_URL` | str | `http://ollama:11434` | Ollama API endpoint. Use `http://localhost:11434` outside Docker |
| `OLLAMA_DEFAULT_MODEL` | str | `llama3.2` | Default model for chat and agent invocations |
| `DATABASE_URL` | str | `postgresql+asyncpg://agent33:agent33@postgres:5432/agent33` | PostgreSQL connection string (asyncpg dialect) |
| `REDIS_URL` | str | `redis://redis:6379/0` | Redis connection URL |
| `NATS_URL` | str | `nats://nats:4222` | NATS server URL |
| `JWT_SECRET` | str | `change-me-in-production` | HMAC secret for JWT signing |
| `JWT_ALGORITHM` | str | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | int | `60` | JWT token lifetime in minutes |
| `ENCRYPTION_KEY` | str | `""` (empty) | Fernet key for encrypting data at rest. Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `OPENAI_API_KEY` | str | `""` (empty) | OpenAI (or compatible) API key. Leave empty to use Ollama only |
| `OPENAI_BASE_URL` | str | `""` (empty) | Custom base URL for OpenAI-compatible providers (e.g., `https://api.together.xyz/v1`) |

Additional variables used by `docker-compose.yml` for port mapping:

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_PORT` | `5432` | Host port for PostgreSQL |
| `REDIS_PORT` | `6379` | Host port for Redis |
| `NATS_PORT` | `4222` | Host port for NATS client connections |
| `OLLAMA_PORT` | `11434` | Host port for Ollama API |

## Docker Services

| Service | Image | Default Port | Purpose |
|---|---|---|---|
| **api** | Custom (`Dockerfile`) | `8000` | FastAPI application server. Runs Uvicorn with the `agent33.main:app` ASGI application |
| **ollama** | `ollama/ollama:latest` | `11434` | Local LLM inference server. GPU-accelerated when NVIDIA drivers are available |
| **postgres** | `pgvector/pgvector:pg16` | `5432` | PostgreSQL 16 with the pgvector extension for embedding storage, workflow checkpoints, and long-term memory |
| **redis** | `redis:7-alpine` | `6379` | Short-term memory cache, session state, rate limiting |
| **nats** | `nats:2-alpine` | `4222` (client), `8222` (monitoring) | NATS with JetStream for internal event bus, pub/sub, and request/reply messaging |

### Volumes

| Volume | Mounted To | Purpose |
|---|---|---|
| `ollama_data` | `/root/.ollama` | Persists downloaded LLM model weights |
| `postgres_data` | `/var/lib/postgresql/data` | Persists database files |
| `redis_data` | `/data` | Persists Redis RDB snapshots |
| `./agent-definitions` | `/app/agent-definitions` (read-only) | Agent JSON definitions mounted into the API container |
| `./workflow-definitions` | `/app/workflow-definitions` (read-only) | Workflow JSON/YAML definitions |
| `./tool-definitions` | `/app/tool-definitions` (read-only) | Tool definitions |

## Development

### Running without Docker

Start only the infrastructure services and run the API locally with hot reload:

```bash
# Start infrastructure
docker compose up -d postgres redis nats ollama

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
.venv\Scripts\activate          # Windows

# Install in development mode
pip install -e ".[dev]"

# Point to localhost services
export OLLAMA_BASE_URL=http://localhost:11434
export DATABASE_URL=postgresql+asyncpg://agent33:agent33@localhost:5432/agent33
export REDIS_URL=redis://localhost:6379/0
export NATS_URL=nats://localhost:4222

# Run with hot reload
uvicorn agent33.main:app --reload --host 0.0.0.0 --port 8000
```

### Linting and formatting

```bash
ruff check src/ tests/           # Lint
ruff check --fix src/ tests/     # Auto-fix
ruff format src/ tests/          # Format
mypy src/                        # Type check (strict mode)
```

### Testing

```bash
pytest                                          # All unit tests
pytest --cov=agent33 --cov-report=term-missing  # With coverage
pytest -m integration                           # Integration tests only
pytest tests/benchmarks/                        # Benchmarks
```

## Make Targets

| Target | Command | Description |
|---|---|---|
| `make up` | `docker compose up -d` | Start all services in detached mode |
| `make down` | `docker compose down` | Stop and remove all containers |
| `make build` | `docker compose build` | Rebuild the API Docker image |
| `make test` | `pytest tests/ -v` | Run the test suite with verbose output |
| `make lint` | `ruff check` + `mypy` | Run linting and type checking |
| `make fmt` | `ruff format` + `ruff check --fix` | Auto-format and fix lint issues |
| `make check` | `make lint` + `make test` | Full CI check (lint then test) |
| `make dev` | `uvicorn ... --reload` | Start local dev server with hot reload |
| `make pull-model MODEL=<name>` | `docker compose exec ollama ollama pull` | Pull an LLM model into Ollama (e.g., `make pull-model MODEL=llama3.2`) |

## Production Deployment

Use the production overlay to apply resource limits, disable exposed ports, and add health checks:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### What the production overlay changes

- **api**: Restart policy `always`, CPU limit 2 cores / 2 GB RAM, no host-exposed ports (use a reverse proxy), log level set to `warning`, health check every 30 seconds.
- **ollama**: Restart policy `always`, 8 GB RAM limit, GPU reservation, health check on `/api/tags`.
- **postgres**: Restart policy `always`, 1 core / 1 GB RAM, no host-exposed ports.
- **redis**: Restart policy `always`, 0.5 core / 256 MB RAM, no host-exposed ports.
- **nats**: Restart policy `always`, 0.5 core / 256 MB RAM, no host-exposed ports, health check on `/healthz`.

### Security hardening checklist

1. **Change all secrets** -- set `API_SECRET_KEY`, `JWT_SECRET`, and `ENCRYPTION_KEY` to strong random values in your `.env` file.
2. **Set database credentials** -- change the default `agent33`/`agent33` PostgreSQL user and password.
3. **Use a reverse proxy** -- place Nginx, Caddy, or Traefik in front of the API container for TLS termination.
4. **Restrict network access** -- the production overlay removes host port bindings; only the reverse proxy should reach the API.
5. **Enable encryption at rest** -- generate a Fernet key and set `ENCRYPTION_KEY`.
6. **Rotate JWT secrets** periodically and keep `JWT_EXPIRE_MINUTES` low.
7. **Review allowlists** -- configure command, path, and domain allowlists in the security module before enabling tools.
