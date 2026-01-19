# Repo Dossier: microsoft/agent-framework

**Snapshot date:** 2026-01-16

## 1) One-paragraph summary

Microsoft Agent Framework (preview) focuses on building and orchestrating agentic workflows in .NET, with explicit emphasis on structured workflows, typed control flow, and checkpointing/resumability. The documentation highlights stateful workflows and mechanisms aimed at long-running, observable agent execution.

## 2) Core orchestration model

- **Primary primitive:** Workflow-first orchestration (workflow as the unit of composition), suitable for chaining agent steps and tool invocations with typed structure.
- **State model:** Documentation emphasizes state and checkpointing to support durable execution.
- **Human-in-the-loop:** Designed to support human oversight patterns through workflow control points (details depend on your integration).

## 3) Tooling and execution

- **Primary interfaces:** SDK for .NET (workflows); integrates with broader Microsoft ecosystem
- **Tool interface / protocol:** See evidence links; varies by repo.
- **Sandboxing / safety controls:** Enterprise posture; assumes integration with standard .NET security patterns (secrets, authn/z) and policy at boundaries.

## 4) Observability and evaluation

- **Observability:** Docs and launch materials position observability as a core requirement for production workflows.
- **Evaluation:** Not explicit in the overview material captured; treat eval harness as external to the framework.

## 5) Extensibility

Extensible via .NET composition and adapters; treat tools as services/clients the workflow calls.

## 6) Notable practices worth adopting in AGENT 33

1. **Make orchestration explicit.** Convert implicit “agent behavior” into explicit artifacts: plans, task lists, acceptance criteria, and evidence logs.
2. **Treat state as a first-class object.** Prefer explicit state + resumability primitives (threads/checkpoints) over ""just chat history"".
3. **Institutionalize HITL.** Use interrupts/approvals for risk triggers (secrets, network, schema migrations, large refactors).
4. **Separate tool protocol from policy.** Keep tool connectivity (MCP/JSON-RPC/function calling) separate from policy (allowlists, budgets, approvals).
5. **Benchmark regressions.** Pair unit/integration tests with agent-task eval suites (SWE-bench-like) to catch orchestration regressions.

## 7) Risks / limitations to account for

- **Doc-to-implementation drift:** Ensure features you borrow exist in code and are stable in your runtime.
- **Over-permissioned runtimes:** Any system that can execute shell/file/network operations needs least-privilege defaults.
- **Context bloat:** Without progressive disclosure (tool schemas, repo indexing), agents will thrash or hallucinate.

## 8) Feature extraction (for master matrix)

- **Repo:** microsoft/agent-framework
- **Primary language:** .NET
- **Interfaces:** SDK for .NET (workflows); integrates with broader Microsoft ecosystem
- **Orchestration primitives:** Workflow-first orchestration (workflow as the unit of composition), suitable for chaining agent steps and tool invocations with typed structure.
- **State/persistence:** Documentation emphasizes state and checkpointing to support durable execution.
- **HITL controls:** Designed to support human oversight patterns through workflow control points (details depend on your integration).
- **Sandboxing:** Enterprise posture; assumes integration with standard .NET security patterns (secrets, authn/z) and policy at boundaries.
- **Observability:** Docs and launch materials position observability as a core requirement for production workflows.
- **Evaluation:** Not explicit in the overview material captured; treat eval harness as external to the framework.
- **Extensibility:** Extensible via .NET composition and adapters; treat tools as services/clients the workflow calls.

## 9) Evidence links

- https://learn.microsoft.com/en-us/dotnet/ai/agent-framework/overview
- https://devblogs.microsoft.com/dotnet/introducing-microsoft-agent-framework/
