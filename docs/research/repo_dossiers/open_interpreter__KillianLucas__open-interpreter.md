# Repo Dossier: KillianLucas/open-interpreter

**Snapshot date:** 2026-01-16

## 1) One-paragraph summary

Open Interpreter is a local-first agentic assistant focused on executing code on the user’s machine, with configuration options that govern autonomy (looping, auto-run), safety mechanisms (safe mode), and offline operation. It uses a model-agnostic backend via LiteLLM and supports multiple model providers.

## 2) Core orchestration model

- **Primary primitive:** Interactive execution loop where the model proposes code; interpreter executes and returns outputs; optional forced-completion loop.
- **State model:** Conversation/messages can be restored; profiles can capture configuration; persistence is primarily session-level.
- **Human-in-the-loop:** Supports explicit user confirmation modes and safe mode options; auto-run allows bypass (use cautiously).

## 3) Tooling and execution

- **Primary interfaces:** CLI + Python API; local execution focus
- **Tool interface / protocol:** See evidence links; varies by repo.
- **Sandboxing / safety controls:** Safe mode options (off/ask/auto) and isolation guidance; offline mode; telemetry disable.

## 4) Observability and evaluation

- **Observability:** Verbose mode; telemetry controls; output streaming.
- **Evaluation:** Not positioned as a benchmark-first system; evaluation typically done externally.

## 5) Extensibility

Supports custom models and execution environments (e.g., Docker, E2B) and configuration profiles.

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

- **Repo:** KillianLucas/open-interpreter
- **Primary language:** Python
- **Interfaces:** CLI + Python API; local execution focus
- **Orchestration primitives:** Interactive execution loop where the model proposes code; interpreter executes and returns outputs; optional forced-completion loop.
- **State/persistence:** Conversation/messages can be restored; profiles can capture configuration; persistence is primarily session-level.
- **HITL controls:** Supports explicit user confirmation modes and safe mode options; auto-run allows bypass (use cautiously).
- **Sandboxing:** Safe mode options (off/ask/auto) and isolation guidance; offline mode; telemetry disable.
- **Observability:** Verbose mode; telemetry controls; output streaming.
- **Evaluation:** Not positioned as a benchmark-first system; evaluation typically done externally.
- **Extensibility:** Supports custom models and execution environments (e.g., Docker, E2B) and configuration profiles.

## 9) Evidence links

- https://docs.openinterpreter.com/settings/all-settings
- https://docs.openinterpreter.com/safety/safe-mode
