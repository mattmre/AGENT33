# Repo Dossier: crewAIInc/crewAI

**Snapshot date:** 2026-01-16

## 1) One-paragraph summary

CrewAI is a multi-agent orchestration framework centered on Crews (teams of role-based agents) and Flows (structured, event-driven orchestration with state). It targets productionization via AMP (deployable automations) and offers a broad ecosystem of tools, integrations, and observability exporters.

## 2) Core orchestration model

- **Primary primitive:** Crew (agent team) + Flow (stateful, event-driven workflow).
- **State model:** Flows manage state and execution; agents can maintain memory and enable replay depending on configuration.
- **Human-in-the-loop:** Docs enumerate human input / HITL workflows; supports gating and human feedback patterns.

## 3) Tooling and execution

- **Primary interfaces:** Python framework + CLI + hosted AMP (deployable “automations”)
- **Tool interface / protocol:** See evidence links; varies by repo.
- **Sandboxing / safety controls:** MCP security considerations are documented; hosted AMP includes RBAC and operational controls.

## 4) Observability and evaluation

- **Observability:** Extensive observability integrations listed (Langfuse, Datadog, MLflow, etc.).
- **Evaluation:** Mentions evaluation integrations (e.g., Patronus AI evaluation) and testing guidance; treat as pluggable.

## 5) Extensibility

Tooling system supports custom tools; MCP can be used as tool transport; marketplace/agent repositories in AMP.

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

- **Repo:** crewAIInc/crewAI
- **Primary language:** Python
- **Interfaces:** Python framework + CLI + hosted AMP (deployable “automations”)
- **Orchestration primitives:** Crew (agent team) + Flow (stateful, event-driven workflow).
- **State/persistence:** Flows manage state and execution; agents can maintain memory and enable replay depending on configuration.
- **HITL controls:** Docs enumerate human input / HITL workflows; supports gating and human feedback patterns.
- **Sandboxing:** MCP security considerations are documented; hosted AMP includes RBAC and operational controls.
- **Observability:** Extensive observability integrations listed (Langfuse, Datadog, MLflow, etc.).
- **Evaluation:** Mentions evaluation integrations (e.g., Patronus AI evaluation) and testing guidance; treat as pluggable.
- **Extensibility:** Tooling system supports custom tools; MCP can be used as tool transport; marketplace/agent repositories in AMP.

## 9) Evidence links

- https://docs.crewai.com/en/introduction
- https://docs.crewai.com/llms-full.txt
- https://docs.crewai.com/en/enterprise/guides/prepare-for-deployment
