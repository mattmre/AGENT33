# AGENT-33

**Autonomous AI agent orchestration engine — local-first, model-agnostic, fully open.**

![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![CI](https://img.shields.io/badge/CI-passing-brightgreen)

---

## What is AGENT-33

AGENT-33 is an autonomous AI agent orchestration engine that combines a rigorous specification framework with a fully working runtime. It provides everything needed to define, deploy, and manage multi-agent workflows: from structured agent definitions and DAG-based execution to local LLM inference via Ollama and secure multi-platform messaging. The entire system runs on your own infrastructure with no external dependencies required.

AGENT-33's mission is to enable developers to build autonomous AI systems they fully control — on their own infrastructure, with their own models, under their own governance policies. No black boxes, no vendor lock-in, no data leaving your network unless you choose it. See the [Mission and Vision](docs/MISSION-AND-VISION.md) for the full philosophy.

The specification layer (in `core/`) captures battle-tested orchestration patterns, role definitions, handoff protocols, and governance rules extracted from real production projects. The engine layer (in `engine/`) implements those patterns as a Python runtime built on FastAPI, with multi-model routing, parallel workflow execution, RAG-powered memory, and end-to-end encryption. Together, they form a single coherent platform where the specs inform the engine and the engine validates the specs.

## Why AGENT-33

- **Local-first** — Run everything on your hardware with Ollama. No API keys, no cloud dependencies, no data leaving your network.
- **Model-agnostic** — Switch between Ollama models, OpenAI, or any compatible provider without changing agents or workflows.
- **Specification-driven** — 232+ specs define behavior before implementation. Review what the system will do before deploying it.
- **Production-ready** — JWT auth, AES-256-GCM encryption, RBAC, prompt injection defense, health checks, structured logging, and resource limits out of the box.

## Who is it for

- **Developers** building AI-powered applications who want full control over their stack
- **DevOps teams** automating pipelines with multi-agent workflows and governance
- **Researchers** exploring multi-agent orchestration patterns with a spec-first approach
- **Enterprises** that need auditable, secure, self-hosted AI infrastructure

## Key Features

- **Local LLM inference via Ollama** with GPU acceleration — no API keys required
- **OpenAI-compatible cloud fallback** for models not available locally
- **Multi-model routing** that selects the best model per task based on capability and cost
- **DAG workflow engine** with parallel execution, conditionals, and checkpointing
- **Agent definition system** with structured input/output schemas and capability declarations
- **Multi-platform messaging** across Telegram, Discord, Slack, and WhatsApp
- **Tool system with governance** — shell, file, browser, and web tools gated by allowlists and permissions
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
# 1. Clone and configure
git clone https://github.com/mattmre/AGENT33.git
cd AGENT33/engine
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Pull a local model
docker compose exec ollama ollama pull llama3.2

# 4. Verify the engine is running
curl http://localhost:8000/health

# 5. Send a chat message
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, AGENT-33"}'
```

For the full tutorial — including creating agents and running workflows — see the [Quick Start Guide](docs/QUICKSTART.md).

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

See the [Architecture Overview](docs/ARCHITECTURE-OVERVIEW.md) for a detailed walkthrough.

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
├── collected/                   # Dynamic intake directory (populated by agent33 intake)
└── docs/                        # Documentation, planning, and self-improvement protocols
    ├── self-improvement/        #   Continuous improvement loop, intake, testing, offline mode
    ├── phases/                  #   AGENT-33 roadmap and phase planning
    ├── competitive-analysis/    #   Autonomous competitive analysis protocol
    └── research/                #   Research templates and generated dossiers
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Documentation Hub](docs/README.md) | Navigation hub — find the right doc for your goal |
| [Quick Start](docs/QUICKSTART.md) | Clone, start, chat, create an agent, run a workflow |
| [Mission and Vision](docs/MISSION-AND-VISION.md) | Core principles, philosophy, long-term goals |
| [Architecture Overview](docs/ARCHITECTURE-OVERVIEW.md) | High-level design and component walkthrough |
| [Integration Guide](docs/INTEGRATION-GUIDE.md) | REST API, webhooks, Docker sidecar, plugins |
| [Deployment Guide](docs/DEPLOYMENT.md) | Production hardening, reverse proxy, backups, monitoring |
| [Use Cases](docs/USE-CASES.md) | Real-world scenarios and patterns |
| [Comparison](docs/COMPARISON.md) | AGENT-33 vs LangChain, CrewAI, AutoGPT, and others |
| [FAQ](docs/FAQ.md) | Frequently asked questions |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues and solutions |
| [Glossary](docs/GLOSSARY.md) | Terminology reference |
| [Roadmap](docs/ROADMAP.md) | Completed and planned work |
| [API Reference](engine/docs/api-reference.md) | REST endpoints and schemas |
| [Workflow Guide](engine/docs/workflow-guide.md) | DAG authoring and execution |
| [Security Guide](engine/docs/security-guide.md) | Authentication, encryption, threat model |

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

See the full [Roadmap](docs/ROADMAP.md) for details.

## Community

- **Contributing** — Read the [Contributing Guide](CONTRIBUTING.md) to get started
- **Issues** — Report bugs or request features at [github.com/mattmre/AGENT33/issues](https://github.com/mattmre/AGENT33/issues)
- **Discussions** — Join the conversation at [github.com/mattmre/AGENT33/discussions](https://github.com/mattmre/AGENT33/discussions)

## License

MIT License. See [LICENSE](LICENSE) for details.
