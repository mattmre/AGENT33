# Repo Dossier: Pythagora-io/gpt-pilot

**Snapshot date:** 2026-01-16

## 1) One-paragraph summary

GPT Pilot is a CLI-centric AI developer that generates real applications by iterating through planning, architecture decisions, and code implementation with human oversight. The project emphasizes role separation (e.g., product owner, architect, developer) and repeatable project scaffolding.

## 2) Core orchestration model

- **Primary primitive:** Role-based pipeline that progresses from requirements to implementation; agents collaborate through staged artifacts.
- **State model:** Project artifacts (specs, plan outputs) serve as durable state; local filesystem is the source of truth.
- **Human-in-the-loop:** User is kept in the loop; approvals and decision points are integral to its workflow.

## 3) Tooling and execution

- **Primary interfaces:** CLI + iterative project generation
- **Tool interface / protocol:** See evidence links; varies by repo.
- **Sandboxing / safety controls:** Primarily local codegen; risk governed by requiring user decisions and reviewing diffs.

## 4) Observability and evaluation

- **Observability:** CLI logs; some telemetry is documented, but treat as optional.
- **Evaluation:** Evaluation is external; success measured by generated project correctness.

## 5) Extensibility

Extensible through templates and workflow modifications.

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

- **Repo:** Pythagora-io/gpt-pilot
- **Primary language:** Python
- **Interfaces:** CLI + iterative project generation
- **Orchestration primitives:** Role-based pipeline that progresses from requirements to implementation; agents collaborate through staged artifacts.
- **State/persistence:** Project artifacts (specs, plan outputs) serve as durable state; local filesystem is the source of truth.
- **HITL controls:** User is kept in the loop; approvals and decision points are integral to its workflow.
- **Sandboxing:** Primarily local codegen; risk governed by requiring user decisions and reviewing diffs.
- **Observability:** CLI logs; some telemetry is documented, but treat as optional.
- **Evaluation:** Evaluation is external; success measured by generated project correctness.
- **Extensibility:** Extensible through templates and workflow modifications.

## 9) Evidence links

- https://github.com/Pythagora-io/gpt-pilot
- https://pypi.org/project/gpt-pilot/
