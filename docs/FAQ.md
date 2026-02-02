# Frequently Asked Questions

## General

### What is AGENT-33?

AGENT-33 is an autonomous AI agent orchestration engine. It lets you define, deploy, and manage multi-agent workflows on your own infrastructure with local LLM inference, built-in security, and a specification-driven architecture. See the [Architecture Overview](ARCHITECTURE-OVERVIEW.md) for how it works.

### How is AGENT-33 different from LangChain or CrewAI?

AGENT-33 is local-first (no API keys required), includes production security features (JWT, encryption, RBAC, prompt injection defense), has a DAG workflow engine with parallel execution and checkpointing, and is backed by 232+ specifications that define expected behavior. See the [Comparison](COMPARISON.md) for a detailed feature matrix.

### Is AGENT-33 production-ready?

Yes. It includes JWT authentication, AES-256-GCM encryption, role-based access control, prompt injection defense, health checks, structured logging, resource limits, and a production Docker Compose overlay. See the [Deployment Guide](DEPLOYMENT.md).

### What license is AGENT-33 under?

MIT License. You can use it freely for personal and commercial projects. See [LICENSE](../LICENSE).

### Can I use AGENT-33 commercially?

Yes. The MIT license allows commercial use, modification, and distribution with no restrictions beyond preserving the copyright notice.

## Technical

### What LLM models does AGENT-33 support?

Any model available through Ollama (Llama, Mistral, Gemma, Phi, CodeLlama, and many more) plus any OpenAI-compatible API provider. The LLM router selects the best model per request.

### Does AGENT-33 work with OpenAI?

Yes. Set `OPENAI_API_KEY` and optionally `OPENAI_BASE_URL` in your `.env` file. The LLM router can use OpenAI as a fallback or primary provider. Any OpenAI-compatible API works (Together, Groq, etc.).

### Can AGENT-33 run fully offline?

Yes. With Ollama for local inference and all services self-hosted, AGENT-33 runs without any internet connection. See the [offline mode protocol](self-improvement/offline-mode.md).

### Is a GPU required?

No, but strongly recommended. Ollama runs on CPU but inference is significantly slower. A CUDA-capable NVIDIA GPU dramatically improves performance. See [Troubleshooting](TROUBLESHOOTING.md) for model memory requirements.

### Does AGENT-33 work on Windows?

Yes. AGENT-33 runs via Docker, which works on Windows with Docker Desktop. The engine can also run natively on Windows with Python 3.11+ and local services.

### What databases does AGENT-33 use?

PostgreSQL 16 with pgvector for persistent storage and embeddings, Redis for short-term memory and caching, and NATS with JetStream for internal messaging. All run as Docker containers.

### What Python version is required?

Python 3.11 or later. The engine uses modern Python features including `asyncio`, type hints, and Pydantic v2.

## Features

### Can I create custom tools for agents?

Yes. AGENT-33 has a plugin system using Python entry points. Create a tool class, register it in your `pyproject.toml`, and it becomes available to agents. See the [Integration Guide](INTEGRATION-GUIDE.md).

### Can workflows call other workflows?

Workflow nesting is on the roadmap. Currently, workflows can invoke agents and run commands as steps. Complex pipelines can be built by chaining workflow executions via the API.

### How does memory work?

Short-term memory (Redis) holds active conversations and session state. Long-term memory (PostgreSQL + pgvector) stores document embeddings for semantic retrieval. The RAG pipeline combines both to assemble context for LLM requests. See [Architecture Overview](ARCHITECTURE-OVERVIEW.md).

### Can I connect messaging platforms?

Yes. AGENT-33 supports Telegram, Discord, Slack, and WhatsApp. Channel pairing routes conversations to specific agents. See the [engine integration guide](../engine/docs/integration-guide.md).

### Does AGENT-33 support scheduled tasks?

Yes. The automation module supports cron schedules, interval triggers, webhook-triggered workflows, and event sensors (file changes, freshness checks). Failed deliveries go to a dead-letter queue.

### Can agents use external tools?

Yes. Built-in tools include shell commands, file operations, web fetching, and browser automation (via Playwright). All tools are gated by governance allowlists. You can add custom tools via the plugin system.

### Can I train or fine-tune models through AGENT-33?

Not yet. Model fine-tuning integration is on the [Roadmap](ROADMAP.md). Currently, you fine-tune models externally and load them into Ollama.

## Architecture

### What is the `core/` directory?

The specification framework — 232+ documents defining agent roles, orchestration protocols, governance rules, workflow patterns, and architecture decisions. It is the canonical reference for how the system should behave. See [Architecture Overview](ARCHITECTURE-OVERVIEW.md).

### How do agents communicate?

Agents communicate through the workflow engine (passing outputs between steps), the NATS message bus (internal pub/sub), and shared memory (session state in Redis, long-term context in PostgreSQL).

### What is the difference between specs and engine?

Specs (`core/`) define *what* the system should do — roles, protocols, rules. The engine (`engine/`) implements *how* — Python code, API endpoints, Docker services. Specs are the blueprint; the engine is the building.

### What are orchestrator protocols?

Documented procedures for how the orchestrator agent decomposes tasks, assigns work, manages handoffs, and handles failures. Defined in `core/orchestrator/`. They ensure consistent, predictable multi-agent behavior.

## Security

### Is data encrypted?

Yes. AGENT-33 uses AES-256-GCM (via Fernet) for encrypting sensitive data at rest. TLS encryption in transit is handled by your reverse proxy. See the [Security Guide](../engine/docs/security-guide.md).

### How does AGENT-33 defend against prompt injection?

The security module includes input sanitization and prompt injection detection that analyzes inputs before they reach the LLM. Combined with tool allowlists and governance policies, this limits the attack surface.

### Does AGENT-33 have audit logging?

Yes. The observability module provides structured logging, distributed tracing, lineage tracking, and replay. Every agent invocation and workflow execution produces auditable records.

### Does AGENT-33 support RBAC?

Yes. Role-based access control with scoped permissions. Users have roles, roles have permission scopes, and API endpoints enforce scope requirements. See the [Security Guide](../engine/docs/security-guide.md).

## Performance

### How fast is local inference?

Depends on your hardware and model size. With a modern NVIDIA GPU, expect 20-60 tokens/second for 7B models. CPU inference is 5-15x slower. Smaller models (3B) are faster.

### How many concurrent workflows can AGENT-33 handle?

Depends on your hardware. The async architecture handles many concurrent requests efficiently. Bottleneck is typically LLM inference throughput. With a GPU, expect 5-10 concurrent agent invocations.

### What are the minimum system requirements?

16 GB RAM, 4 CPU cores, 20 GB disk. A CUDA-capable NVIDIA GPU is strongly recommended. For large models (70B+), 64+ GB RAM and a high-VRAM GPU are needed.
