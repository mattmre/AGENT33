# AGENT-33

**Autonomous AI agent orchestration engine -- local-first, model-agnostic, fully open.**

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![CI](https://img.shields.io/badge/CI-passing-brightgreen)

---

## What is AGENT-33

AGENT-33 is an autonomous AI agent orchestration engine that combines a rigorous specification framework with a fully working runtime. It provides everything needed to define, deploy, and manage multi-agent workflows: from structured agent definitions and DAG-based execution to local LLM inference via Ollama and secure multi-platform messaging. The entire system runs on your own infrastructure with no external dependencies required.

The specification layer (in `core/`) captures battle-tested orchestration patterns, role definitions, handoff protocols, and governance rules extracted from real production projects. The engine layer (in `engine/`) implements those patterns as a Python runtime built on FastAPI, with multi-model routing, parallel workflow execution, RAG-powered memory, and end-to-end encryption. Together, they form a single coherent platform where the specs inform the engine and the engine validates the specs.

AGENT-33 is designed for teams that need full control over their AI infrastructure. It runs local-first with Ollama for GPU-accelerated inference, supports OpenAI-compatible cloud fallback when needed, enforces security at every layer (prompt injection defense, AES-256-GCM encryption, JWT authentication), and extends through a plugin system. Whether you are building a chatbot, automating DevOps pipelines, or orchestrating a fleet of specialized agents, AGENT-33 provides the foundation.

## Key Features

- **Local LLM inference via Ollama** with GPU acceleration -- no API keys required
- **OpenAI-compatible cloud fallback** for models not available locally
- **Multi-model routing** that selects the best model per task based on capability and cost
- **DAG workflow engine** with parallel execution, conditionals, and checkpointing
- **Agent definition system** with structured input/output schemas and capability declarations
- **Multi-platform messaging** across Telegram, Discord, Slack, and WhatsApp
- **Tool system with governance** -- shell, file, browser, and web tools gated by allowlists and permissions
- **RAG memory** with pgvector embeddings, document ingestion, and context windowing
- **AES-256-GCM encrypted sessions** for all sensitive data at rest
- **JWT and API key authentication** with role-based access control
- **Prompt injection defense** with input sanitization and output validation
- **Cron, webhook, and sensor-based automation** with dead-letter queue handling
- **Observability dashboard** with metrics, tracing, lineage tracking, and replay
- **CLI tool** for agent management, workflow execution, and system administration
- **Plugin system** via Python entry points for custom tools, actions, and integrations

## Quick Start

```bash
# 1. Start all services
cd engine && docker compose up -d

# 2. Pull a local model
docker exec agent33-ollama ollama pull llama3

# 3. Verify the engine is running
curl http://localhost:8000/health

# 4. Send a chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, AGENT-33"}'
```

## Architecture Overview

```
                         +-------------------+
                         |       CLI         |
                         +--------+----------+
                                  |
                         +--------v----------+
                         |     FastAPI        |
                         |   (REST + WS)      |
                         +--------+----------+
                                  |
                  +---------------+---------------+
                  |                               |
         +--------v----------+          +---------v---------+
         |   Agent Runtime    |          |  Workflow Engine   |
         |  (Registry, Defs)  |          |  (DAG Executor)    |
         +--------+----------+          +---------+---------+
                  |                               |
         +--------v----------+          +---------v---------+
         |    LLM Router      |          |      Actions       |
         |                    |          | (invoke, transform, |
         +----+----------+---+          |  command, validate) |
              |          |              +--------------------+
     +--------v--+  +----v-------+
     |   Ollama   |  |  OpenAI    |
     |  (local)   |  |  (cloud)   |
     +------------+  +------------+

  Infrastructure: PostgreSQL + pgvector | Redis | NATS
  Messaging:      Telegram | Discord | Slack | WhatsApp
  Security:       JWT | AES-256-GCM | Injection Defense | RBAC
```

## Project Structure

```
AGENT-33/
├── core/                        # Specification framework (canonical orchestration patterns)
│   ├── arch/                    #   Architecture decision records and templates
│   ├── agents/                  #   Agent role definitions and review frameworks
│   ├── orchestrator/            #   Orchestrator protocols and operator manual
│   ├── prompts/                 #   Reusable prompt templates
│   ├── workflows/               #   CI/CD templates, issue templates, instructions
│   └── logs/                    #   Session logs and decision history
├── engine/                      # Runtime engine (working implementation)
│   ├── src/agent33/             #   Python package root
│   │   ├── api/                 #     FastAPI routes (health, chat, agents, workflows, auth)
│   │   ├── llm/                 #     LLM providers (Ollama, OpenAI) and router
│   │   ├── agents/              #     Agent definitions, registry, and runtime
│   │   ├── workflows/           #     DAG engine, executor, actions, state machine
│   │   ├── memory/              #     Short/long-term memory, RAG, embeddings, sessions
│   │   ├── security/            #     Auth, encryption, vault, injection defense, RBAC
│   │   ├── messaging/           #     Telegram, Discord, Slack, WhatsApp adapters
│   │   ├── automation/          #     Scheduler, webhooks, sensors, dead-letter queue
│   │   ├── observability/       #     Logging, tracing, metrics, lineage, replay, alerts
│   │   ├── tools/               #     Tool system (shell, file, browser, web)
│   │   ├── cli/                 #     Command-line interface
│   │   └── testing/             #     Test utilities
│   ├── agent-definitions/       #   JSON agent definition files
│   ├── tests/                   #   Unit, integration, and benchmark tests
│   ├── docs/                    #   Engine documentation
│   ├── docker-compose.yml       #   Full stack deployment
│   ├── Dockerfile               #   Engine container image
│   └── pyproject.toml           #   Python project configuration
├── collected/                   # Raw ingested assets from source repos (immutable)
└── docs/                        # Planning artifacts and session notes
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Getting Started](engine/docs/getting-started.md) | Installation, configuration, and first run |
| [Architecture](engine/docs/architecture.md) | System design, component interactions, data flow |
| [API Reference](engine/docs/api-reference.md) | REST endpoints, request/response schemas |
| [Workflow Guide](engine/docs/workflow-guide.md) | DAG authoring, actions, parallel execution |
| [Security Guide](engine/docs/security-guide.md) | Authentication, encryption, injection defense |
| [Integration Guide](engine/docs/integration-guide.md) | Messaging platforms, webhooks, sensors |
| [Contributing](engine/docs/contributing.md) | Development setup, code standards, PR process |

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11+ |
| API Framework | FastAPI |
| Local LLM | Ollama |
| Database | PostgreSQL + pgvector |
| Cache / Short-term Memory | Redis |
| Message Broker | NATS |
| Workflow Orchestration | LangGraph |
| Containerization | Docker Compose |
| Authentication | JWT + API Keys |
| Encryption | AES-256-GCM |

## Roadmap

**Implemented (Phases 1-10):**
Core API and LLM routing, agent definition and runtime, DAG workflow engine with parallel execution, memory system with RAG and pgvector, security layer (auth, encryption, injection defense), multi-platform messaging, automation (cron, webhooks, sensors), observability and lineage tracking, CLI tooling, plugin system, and competitive feature parity.

**Planned:**
- Production hardening and stress testing
- Horizontal scaling with distributed workflow execution
- Model fine-tuning integration pipeline
- Visual workflow editor (web UI)
- Agent marketplace for sharing definitions and plugins

## Contributing

Contributions are welcome. Please read the [Contributing Guide](engine/docs/contributing.md) for development setup, coding standards, and the pull request process. All changes should include tests and follow the evidence-based review workflow described in the guide.

## License

MIT License. See [LICENSE](LICENSE) for details.
