# Repo Dossier: All-Hands-AI/OpenHands

**Snapshot date:** 2026-01-16

## 1) One-paragraph summary

OpenHands is an open platform for coding agents, providing a production-oriented Software Agent SDK and CLI that can scale from single tasks to many parallel agent runs. It emphasizes a modular tool layer (bash, file editing, web, MCP), deployable agent server, and IDE/editor integration through the Agent Client Protocol (ACP) using JSON-RPC.

## 2) Core orchestration model

- **Primary primitive:** SDK-driven agent runs; supports multi-agent refactors and maintenance via orchestration at the app layer; skills/microagents architecture for reusable behaviors.
- **State model:** CLI/IDE integration stores settings (and supports resuming conversations); SDK + agent server imply durable state can be implemented externally; benchmarks repo indicates standardized evaluation pipelines.
- **Human-in-the-loop:** IDE integration and CLI imply interactive workflows; ACP enables editors to drive agent sessions; approval gates are implementation-dependent.

## 3) Tooling and execution

- **Primary interfaces:** CLI, SDK (Python + REST), Cloud, IDE integrations via ACP
- **Tool interface / protocol:** See evidence links; varies by repo.
- **Sandboxing / safety controls:** Docs emphasize sandboxed runtime you control (Docker/Kubernetes) and configuration reuse; treat external connectivity as governed via tool layer + runtime policy.

## 4) Observability and evaluation

- **Observability:** Evaluation harness plus unit tests; production agent server suggests logs/metrics integration via deployment platform.
- **Evaluation:** Dedicated benchmarks repo (SWE-Bench, GAIA, Commit0, OpenAgentSafety).

## 5) Extensibility

SDK exposes custom tools and custom behaviors; skills/microagents architecture for reusable patterns.

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

- **Repo:** All-Hands-AI/OpenHands
- **Primary language:** Python
- **Interfaces:** CLI, SDK (Python + REST), Cloud, IDE integrations via ACP
- **Orchestration primitives:** SDK-driven agent runs; supports multi-agent refactors and maintenance via orchestration at the app layer; skills/microagents architecture for reusable behaviors.
- **State/persistence:** CLI/IDE integration stores settings (and supports resuming conversations); SDK + agent server imply durable state can be implemented externally; benchmarks repo indicates standardized evaluation pipelines.
- **HITL controls:** IDE integration and CLI imply interactive workflows; ACP enables editors to drive agent sessions; approval gates are implementation-dependent.
- **Sandboxing:** Docs emphasize sandboxed runtime you control (Docker/Kubernetes) and configuration reuse; treat external connectivity as governed via tool layer + runtime policy.
- **Observability:** Evaluation harness plus unit tests; production agent server suggests logs/metrics integration via deployment platform.
- **Evaluation:** Dedicated benchmarks repo (SWE-Bench, GAIA, Commit0, OpenAgentSafety).
- **Extensibility:** SDK exposes custom tools and custom behaviors; skills/microagents architecture for reusable patterns.

## 9) Evidence links

- https://openhands.dev/
- https://docs.openhands.dev/sdk
- https://docs.openhands.dev/openhands/usage/cli/ide/overview
- https://docs.openhands.dev/openhands/usage/developers/development-overview
- https://github.com/OpenHands/benchmarks
