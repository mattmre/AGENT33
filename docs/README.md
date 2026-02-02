# AGENT-33 Documentation

Welcome to the AGENT-33 documentation. Start with the guide that matches your goal.

## Start Here

| You want to... | Start with |
|----------------|-----------|
| **Get running quickly** | [Quick Start Guide](QUICKSTART.md) |
| **Evaluate AGENT-33 vs alternatives** | [Comparison](COMPARISON.md) and [Use Cases](USE-CASES.md) |
| **Integrate AGENT-33 into your project** | [Integration Guide](INTEGRATION-GUIDE.md) |
| **Deploy to production** | [Deployment Guide](DEPLOYMENT.md) |
| **Contribute code or docs** | [Contributing Guide](../CONTRIBUTING.md) |
| **Understand the architecture** | [Architecture Overview](ARCHITECTURE-OVERVIEW.md) |
| **Explore specifications** | [Specification Framework](../core/) |

## All Documentation

### Project-Level

| Document | Description |
|----------|-------------|
| [Mission and Vision](MISSION-AND-VISION.md) | Why AGENT-33 exists, core principles, philosophy, long-term goals |
| [Quick Start](QUICKSTART.md) | Clone, start, chat, create an agent, run a workflow |
| [Architecture Overview](ARCHITECTURE-OVERVIEW.md) | High-level design: two-layer architecture, components, request lifecycle |
| [Integration Guide](INTEGRATION-GUIDE.md) | REST API, webhooks, Docker sidecar, plugins |
| [Deployment Guide](DEPLOYMENT.md) | Production setup: hardening, reverse proxy, backups, monitoring, scaling |
| [Use Cases](USE-CASES.md) | DevOps, content generation, research, support, data processing, security |
| [Comparison](COMPARISON.md) | AGENT-33 vs LangChain, LangGraph, CrewAI, AutoGPT, Semantic Kernel |
| [Roadmap](ROADMAP.md) | Completed phases, planned work, future vision |
| [FAQ](FAQ.md) | Common questions about features, architecture, security, performance |
| [Troubleshooting](TROUBLESHOOTING.md) | Docker, Ollama, PostgreSQL, API errors, debug tools |
| [Glossary](GLOSSARY.md) | All terminology: core concepts, technical terms, framework terms |
| [Changelog](../CHANGELOG.md) | Release history in Keep-a-Changelog format |
| [Contributing](../CONTRIBUTING.md) | How to contribute code, docs, and feedback |

### Engine Technical Docs

Deep dives into the runtime engine — implementation details, API endpoints, and configuration.

| Document | Description |
|----------|-------------|
| [Getting Started](../engine/docs/getting-started.md) | Installation, configuration, first run |
| [Architecture](../engine/docs/architecture.md) | Component interactions, data flow, sequence diagrams |
| [API Reference](../engine/docs/api-reference.md) | Every REST endpoint with request/response schemas |
| [Workflow Guide](../engine/docs/workflow-guide.md) | DAG authoring, actions, parallel execution, expressions |
| [Agent Guide](../engine/docs/agent-guide.md) | Agent definitions, registry, runtime, invocation |
| [Security Guide](../engine/docs/security-guide.md) | Authentication, encryption, injection defense, RBAC |
| [Integration Guide (Engine)](../engine/docs/integration-guide.md) | Messaging platforms, webhooks, sensors |
| [CLI Reference](../engine/docs/cli-reference.md) | Command-line interface usage |
| [Use Cases (Engine)](../engine/docs/use-cases.md) | Implementation examples with code |
| [Contributing (Engine)](../engine/docs/contributing.md) | Dev setup, coding standards, PR process |
| [Feature Roadmap](../engine/docs/feature-roadmap.md) | Detailed engine feature planning |

### Specifications and Planning

| Document | Description |
|----------|-------------|
| [Specification Framework](../core/) | 232+ specs: agent roles, orchestration protocols, governance |
| [Phase History](phases/) | Detailed planning documents for Phases 1-20 |
| [Self-Improvement Protocols](self-improvement/README.md) | Continuous improvement loop, intake, testing, offline mode |
