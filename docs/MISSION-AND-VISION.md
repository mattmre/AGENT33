# Mission and Vision

## Mission

Enable developers to build autonomous AI systems they fully control — on their own infrastructure, with their own models, under their own governance policies.

## Vision

AGENT-33 envisions a future where AI orchestration is transparent, controllable, and auditable. Where teams deploy multi-agent systems with the same confidence they deploy traditional software: with tests, observability, rollback, and security at every layer. No black boxes. No vendor lock-in. No data leaving your network unless you choose it.

## Core Principles

### 1. Local-First

Your infrastructure, your models, your data. AGENT-33 runs entirely on your hardware with Ollama for local LLM inference. Cloud providers are optional fallbacks, never requirements. No API keys needed to get started.

### 2. Model-Agnostic

No vendor lock-in. Switch between Ollama models, OpenAI, or any OpenAI-compatible provider without changing your agents or workflows. The LLM router selects the best model per task based on capability and cost.

### 3. Specification-Driven

The framework is defined before it is implemented. The `core/` directory contains 232+ specifications that define agent roles, orchestration protocols, governance rules, and workflow patterns. The engine implements these specs, and the specs evolve based on what the engine learns.

### 4. Evidence-Based

Every decision is backed by traces. Workflow executions produce lineage records. Agent invocations are logged with inputs, outputs, and reasoning. The observability layer provides metrics, tracing, and replay so you can audit exactly what happened and why.

### 5. Open and Transparent

No black boxes. Every component is open source, every protocol is documented, every decision is recorded. The specification layer makes the system's behavior predictable and reviewable before deployment.

### 6. Production-Ready

AGENT-33 is not a research prototype. It includes JWT authentication, AES-256-GCM encryption, role-based access control, prompt injection defense, health checks, structured logging, and resource limits. It ships with a production Docker Compose overlay and a security hardening checklist.

## Philosophy

**Spec before implementation.** We define what the system should do in human-readable specifications before writing code. This creates a shared understanding between developers, operators, and AI agents about expected behavior.

**Self-improvement over static knowledge.** The system learns *how* to analyze rather than caching *what* was analyzed. See [Self-Improvement Protocols](self-improvement/README.md) for how AGENT-33 continuously refines its own capabilities.

**Governance as a feature.** Autonomy budgets, allowlists, regression gates, and review protocols are first-class features — not afterthoughts bolted on after an incident.

**Quality over velocity.** Every change passes through regression gates. Tests assert on behavior, not just existence. Evidence is captured, not assumed.

## Long-Term Goals

- **Agent marketplace** — Share and discover agent definitions, workflow templates, and plugins
- **Visual workflow editor** — Web-based DAG editor for building workflows without writing JSON
- **Kubernetes operator** — Native K8s deployment with CRDs for agents and workflows
- **Multi-tenancy** — Isolated environments for teams and projects within a single deployment
- **Distributed execution** — Horizontal scaling of workflow execution across multiple nodes

See the [Roadmap](ROADMAP.md) for current status and planned work.
