# Repo Dossier: microsoft/autogen

**Snapshot date:** 2026-01-16

## 1) One-paragraph summary

AutoGen is a framework for building multi-agent systems via conversational abstractions (agents that exchange messages) with support for tool use, group chats, and structured coordination. Documentation also covers memory patterns, allowing agent state to persist across interactions.

## 2) Core orchestration model

- **Primary primitive:** Conversation-driven (AgentChat / GroupChat) orchestration; routing and delegation are expressed through messaging patterns.
- **State model:** Memory support is documented as a first-class concern; state is often represented as message history plus memory stores.
- **Human-in-the-loop:** Human proxy patterns are commonly used; gating depends on how you implement tools and approvals.

## 3) Tooling and execution

- **Primary interfaces:** Python library + Studio (UI) + patterns for multi-agent chat
- **Tool interface / protocol:** See evidence links; varies by repo.
- **Sandboxing / safety controls:** Safety posture depends on tool permissions and runtime; framework provides building blocks rather than an opinionated sandbox.

## 4) Observability and evaluation

- **Observability:** Can be instrumented; Studio provides UI-centric operation.
- **Evaluation:** Evaluation is external; the framework focuses on agent composition.

## 5) Extensibility

Extensible via custom agents/tools; integrates with many model backends.

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

- **Repo:** microsoft/autogen
- **Primary language:** Python
- **Interfaces:** Python library + Studio (UI) + patterns for multi-agent chat
- **Orchestration primitives:** Conversation-driven (AgentChat / GroupChat) orchestration; routing and delegation are expressed through messaging patterns.
- **State/persistence:** Memory support is documented as a first-class concern; state is often represented as message history plus memory stores.
- **HITL controls:** Human proxy patterns are commonly used; gating depends on how you implement tools and approvals.
- **Sandboxing:** Safety posture depends on tool permissions and runtime; framework provides building blocks rather than an opinionated sandbox.
- **Observability:** Can be instrumented; Studio provides UI-centric operation.
- **Evaluation:** Evaluation is external; the framework focuses on agent composition.
- **Extensibility:** Extensible via custom agents/tools; integrates with many model backends.

## 9) Evidence links

- https://raw.githubusercontent.com/microsoft/autogen/main/README.md
- https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory/
