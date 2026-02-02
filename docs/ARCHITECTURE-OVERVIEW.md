# Architecture Overview

A high-level guide to how AGENT-33 is structured and why. For the full technical deep dive, see [engine/docs/architecture.md](../engine/docs/architecture.md).

## Two-Layer Design

AGENT-33 separates **what the system should do** from **how it does it**:

- **Specification layer** (`core/`) — 232+ documents defining agent roles, orchestration protocols, governance rules, workflow patterns, and architecture decisions. Think of this as the blueprint.
- **Runtime layer** (`engine/`) — A Python implementation built on FastAPI that brings the specifications to life. Think of this as the building constructed from the blueprint.

This separation means you can understand the system's intended behavior by reading specs, and verify the implementation matches by running tests. Specs evolve based on what the engine learns in practice.

## Components

### Agents — Your Team of Specialists

Agents are autonomous units with defined roles. Each agent has a name, a system prompt that defines its personality and expertise, a model assignment, and structured input/output schemas.

Think of agents as team members with specific job descriptions. An orchestrator decomposes complex tasks and delegates to workers. Workers execute their specialties and return results. Reviewers check quality.

- Agent definitions live in `engine/agent-definitions/` as JSON files
- The agent registry auto-discovers definitions at startup
- Agents are invoked through the REST API or within workflow steps

### Workflows — Assembly Lines with Quality Checkpoints

Workflows are directed acyclic graphs (DAGs) of steps. Each step performs an action — invoking an agent, running a command, transforming data, or validating output. Steps declare dependencies, and the engine executes independent steps in parallel.

Think of workflows as assembly lines: raw materials enter, pass through processing stations in order, get quality-checked at key points, and exit as finished products.

- Workflows support parallel execution, conditionals, retries, and timeouts
- Checkpoints persist state to PostgreSQL so workflows can resume after failure
- The expression engine allows steps to reference outputs from previous steps

### LLM Router — The Dispatcher

The LLM router selects which model handles each request based on capability requirements and cost preferences. It abstracts away the difference between local Ollama models and cloud providers.

- Primary: Ollama for local, GPU-accelerated inference (no API keys needed)
- Fallback: Any OpenAI-compatible API (OpenAI, Together, Anthropic via proxy)
- Selection is transparent — observability records which model handled each request

### Memory — Short-Term and Long-Term Brain

Memory has two layers:

- **Short-term** (Redis) — Active conversation buffers, session state, rate limiting. Fast but ephemeral.
- **Long-term** (PostgreSQL + pgvector) — Document embeddings, semantic search, conversation history. Persistent and searchable.

The RAG pipeline combines both: it retrieves relevant documents from long-term memory, assembles them with the current conversation from short-term memory, and constructs a context window for the LLM.

### Security — Guards, Vaults, and Governance

Security is not a bolt-on; it is woven through every layer:

- **Authentication** — JWT tokens and API keys with configurable expiration
- **Authorization** — Role-based access control with scoped permissions
- **Encryption** — AES-256-GCM for sensitive data at rest via a Fernet vault
- **Input defense** — Prompt injection detection and input sanitization
- **Tool governance** — Allowlists for commands, file paths, and domains that agents can access

## Request Lifecycle

```
Client Request
     │
     ▼
┌─────────────┐
│  Auth Layer  │──── JWT/API key validation, RBAC check
└──────┬──────┘
       ▼
┌─────────────┐
│  API Router  │──── Route to chat, agent, workflow, or admin endpoint
└──────┬──────┘
       ▼
┌─────────────┐
│  Context     │──── Assemble: system prompt + conversation + RAG results
│  Assembly    │
└──────┬──────┘
       ▼
┌─────────────┐
│  LLM Router  │──── Select model, send prompt, stream response
└──────┬──────┘
       ▼
┌─────────────┐
│  Output      │──── Validate, log lineage, update memory, return response
│  Pipeline    │
└─────────────┘
```

## Infrastructure

| Container | Purpose |
|-----------|---------|
| **api** | FastAPI server — handles all HTTP/WebSocket traffic |
| **ollama** | Local LLM inference — GPU-accelerated when available |
| **postgres** | PostgreSQL 16 with pgvector — persistent storage, embeddings, checkpoints |
| **redis** | Short-term memory, session cache, rate limiting |
| **nats** | Internal message bus with JetStream persistence |

All containers are defined in `engine/docker-compose.yml` and managed as a single stack.

## Data Flow

```
Workflow Execution:

Input JSON
    │
    ▼
Expression Engine
    │
    ├─→ Resolve {{ inputs.x }}, {{ steps.y.output }}
    │
    ▼
Agent Invocation
    │
    ├─→ LLM Router selects model
    │
    ├─→ Memory pipeline assembles context
    │
    ├─→ Send to selected model
    │
    ├─→ Stream response back
    │
    ▼
Output Validation
    │
    ├─→ Check response against output schema
    │
    ├─→ Persist lineage to PostgreSQL
    │
    ├─→ Update embeddings for RAG
    │
    ▼
Next Step (or complete)
```

## Concurrency and Parallelization

The workflow executor analyzes dependencies between steps and executes independent steps concurrently using async/await. PostgreSQL checkpoints ensure that even if the engine crashes mid-workflow, the system can resume from the last completed step without data loss.

```
Step A ──┐
         ├──→ Step C ──→ Step D
Step B ──┘
```

Steps A and B run in parallel. Step C waits for both. Step D waits for C. If the engine crashes after Step B completes, restarting will skip to Step C without re-running A and B.

## Storage

| Database | Purpose | Persistence |
|----------|---------|-------------|
| **PostgreSQL** | Checkpoints, agent definitions, conversation history, embeddings, workflow metadata | Disk-backed, replicated for HA |
| **Redis** | Session cache, rate limits, active message buffers | Memory-backed with optional AOF |
| **pgvector** | Semantic search on embedded documents | PostgreSQL extension |

## Further Reading

- [Full Architecture Deep Dive](../engine/docs/architecture.md) — Component interactions, data flow, sequence diagrams
- [API Reference](../engine/docs/api-reference.md) — Every endpoint documented
- [Workflow Guide](../engine/docs/workflow-guide.md) — DAG authoring, actions, parallel execution
- [Security Guide](../engine/docs/security-guide.md) — Authentication, encryption, threat model
- [Specification Framework](../core/) — The 232+ specs that define system behavior
