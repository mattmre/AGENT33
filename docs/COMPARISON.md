# Comparison with Alternatives

How AGENT-33 compares to other AI agent frameworks. This comparison reflects the state of these projects as of early 2026.

## Feature Matrix

| Feature | AGENT-33 | LangChain | LangGraph | CrewAI | AutoGPT | Semantic Kernel |
|---------|----------|-----------|-----------|--------|---------|-----------------|
| Local LLM inference | Yes (Ollama) | Via integration | Via integration | Via integration | Via integration | Via integration |
| No API keys required | Yes | No | No | No | No | No |
| Multi-model routing | Yes | Manual | Manual | Manual | Limited | Yes |
| DAG workflow engine | Yes | No | Yes | No | No | Limited |
| Parallel execution | Yes | Limited | Yes | Sequential | Sequential | Limited |
| Agent role system | Yes | Basic | Basic | Yes | Yes | Yes |
| Workflow checkpointing | Yes | No | Yes | No | No | No |
| Built-in security (JWT, encryption) | Yes | No | No | No | No | No |
| Prompt injection defense | Yes | No | No | No | No | No |
| Tool governance (allowlists) | Yes | No | No | No | No | No |
| RBAC | Yes | No | No | No | No | No |
| Multi-platform messaging | Yes | No | No | No | No | No |
| Observability (tracing, lineage) | Yes | Via LangSmith | Via LangSmith | Limited | Limited | Limited |
| Cron/webhook automation | Yes | No | No | No | No | No |
| Self-hosted (all components) | Yes | Partial | Partial | Partial | Partial | Partial |
| Specification framework | Yes (232+ specs) | No | No | No | No | No |
| Plugin system | Yes | Yes | Yes | Yes | Limited | Yes |
| Production Docker deployment | Yes | No | No | No | Yes | No |

## Choose AGENT-33 When You Need

- **Full local control** — Run everything on your infrastructure with no external API calls
- **Governance and compliance** — RBAC, audit trails, allowlists, and encryption are requirements
- **Multi-agent orchestration** — Complex workflows with parallel execution, conditionals, and checkpointing
- **Production security** — JWT auth, AES-256-GCM encryption, prompt injection defense out of the box
- **Specification-driven development** — You want documented, reviewable behavior before deployment
- **Multi-platform messaging** — Unified bot across Telegram, Discord, Slack, and WhatsApp

## Consider Alternatives When

- **You need a simple single-agent setup** — LangChain or CrewAI may be faster to start with for basic use cases
- **You prefer managed services** — LangSmith (LangChain) or cloud-hosted solutions reduce operational overhead
- **You only need rapid prototyping** — AutoGPT or LangChain's higher-level abstractions may be quicker for experiments
- **Your team uses .NET** — Semantic Kernel has better C#/.NET integration

## Migration from LangChain

If you have existing LangChain agents:

1. **Map chains to workflows** — Each LangChain chain becomes an AGENT-33 workflow with steps
2. **Convert agents** — LangChain agent definitions map to AGENT-33 agent JSON files with system prompts and schemas
3. **Replace tools** — LangChain tools map to AGENT-33's tool system with added governance
4. **Add memory** — Replace LangChain memory with AGENT-33's RAG pipeline for persistent, searchable context

## Migration from CrewAI

If you have existing CrewAI crews:

1. **Map crews to workflows** — Each crew becomes a workflow; crew tasks become workflow steps
2. **Convert agents** — CrewAI agent roles map directly to AGENT-33 agent definitions
3. **Add orchestration** — Replace CrewAI's sequential execution with AGENT-33's DAG engine for parallel execution
4. **Add security** — Enable JWT auth, encryption, and RBAC that CrewAI doesn't provide
