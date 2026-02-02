# Roadmap

## Completed: v1.0.0 (Phases 1-10)

AGENT-33 v1.0.0 delivers a complete autonomous AI agent orchestration engine:

| Phase | Capability | Status |
|-------|-----------|--------|
| Phase 1 | Foundation and inventory — project structure, specifications catalog | Done |
| Phase 2 | Canonical core architecture — specification framework, architecture decisions | Done |
| Phase 3 | Spec-first orchestration workflow — workflow patterns, orchestrator protocols | Done |
| Phase 4 | Agent harness and runtime — agent definitions, registry, LLM routing, FastAPI server | Done |
| Phase 5 | Policy pack and risk triggers — security policies, allowlists, governance rules | Done |
| Phase 6 | Tooling integration — tool system, shell/file/web/browser tools, plugin entry points | Done |
| Phase 7 | Evidence and verification pipeline — observability, tracing, lineage, replay | Done |
| Phase 8 | Evaluation and benchmarking — test suites, benchmarks, regression gates | Done |
| Phase 9 | Distribution and sync — multi-platform messaging, automation, webhooks, sensors | Done |
| Phase 10 | Governance and community — RBAC, audit workflows, community improvement protocols | Done |

See the [Changelog](../CHANGELOG.md) for detailed release notes and the [Phase History](phases/) for planning documents.

## Planned: Phases 11-20

High-level items from the development roadmap:

| Phase | Capability | Description |
|-------|-----------|-------------|
| Phase 11 | Agent registry and capability catalog | Searchable registry of agent capabilities, versioned definitions |
| Phase 12 | Tool registry and change control | Tool versioning, dependency tracking, rollback |
| Phase 13 | Code execution layer | Sandboxed code execution, tools-as-code |
| Phase 14 | Security hardening | Advanced prompt injection defense, secret rotation, penetration testing |
| Phase 15 | Review automation | Two-layer automated review, quality gates |
| Phase 16 | Observability expansion | Distributed tracing, anomaly detection, SLA monitoring |
| Phase 17 | Evaluation suite expansion | Broader benchmarks, regression gates, A/B testing |
| Phase 18 | Autonomy budget enforcement | Fine-grained autonomy policies, cost tracking, approval workflows |
| Phase 19 | Release and sync automation | Automated releases, multi-environment sync |
| Phase 20 | Continuous improvement and research intake | Automated self-improvement loops, research ingestion |

See [Phase 11-20 Workflow Plan](phases/PHASE-11-20-WORKFLOW-PLAN.md) for detailed planning.

## Future Vision

Beyond Phase 20, AGENT-33 aims to deliver:

- **Agent Marketplace** — A community hub for sharing and discovering agent definitions, workflow templates, and plugins. Browse, rate, and install agents directly from the CLI or API.

- **Visual Workflow Editor** — A web-based DAG editor for building workflows by dragging and connecting steps. No JSON editing required. Real-time preview and execution.

- **Kubernetes Operator** — Native Kubernetes deployment with Custom Resource Definitions (CRDs) for agents and workflows. Automatic scaling, health management, and rolling updates.

- **Multi-Tenancy** — Isolated environments for teams and projects within a single AGENT-33 deployment. Separate agents, workflows, memory, and access policies per tenant.

- **Distributed Execution** — Horizontal scaling of workflow execution across multiple nodes. Partition workflows across a cluster for high-throughput processing.

## Community Input

AGENT-33's roadmap is shaped by community feedback. To influence what gets built next:

- **Feature requests** — Open an issue at [github.com/mattmre/AGENT33/issues](https://github.com/mattmre/AGENT33/issues) with the "enhancement" label
- **Discussions** — Join the conversation at [github.com/mattmre/AGENT33/discussions](https://github.com/mattmre/AGENT33/discussions)
- **Contributions** — See the [Contributing Guide](../CONTRIBUTING.md) for how to submit pull requests

Priorities are determined by community demand, strategic alignment with the [Mission and Vision](MISSION-AND-VISION.md), and engineering feasibility.
