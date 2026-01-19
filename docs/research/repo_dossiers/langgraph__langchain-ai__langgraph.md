# Repo Dossier: langchain-ai/langgraph

**Snapshot date:** 2026-01-16

## 1) One-paragraph summary

LangGraph provides a graph-based orchestration model for agentic systems with first-class state, persistence, streaming, and interrupts for human-in-the-loop. Its documentation emphasizes durable execution through checkpointers and threads, enabling pause/resume, time travel, and fault tolerance.

## 2) Core orchestration model

- **Primary primitive:** StateGraph / compiled graphs; nodes and edges encode control flow.
- **State model:** Built-in persistence layer via checkpointers; checkpoints stored in threads; enables memory, time travel, and fault tolerance.
- **Human-in-the-loop:** Interrupts pause execution, persist state, and resume upon external input.

## 3) Tooling and execution

- **Primary interfaces:** Python/JS libraries; deployment via LangSmith Agent Server/SDK
- **Tool interface / protocol:** See evidence links; varies by repo.
- **Sandboxing / safety controls:** HITL middleware and policies can gate tool calls; persistence enables audit and rollback.

## 4) Observability and evaluation

- **Observability:** Streaming and debug stream modes surface execution events; integrates with LangSmith ecosystem.
- **Evaluation:** Evaluation is typically done via LangSmith or external harnesses; docs focus on runtime primitives.

## 5) Extensibility

Custom checkpointers supported; nodes are arbitrary code; tool policies can be layered.

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

- **Repo:** langchain-ai/langgraph
- **Primary language:** Python (also JS ecosystem)
- **Interfaces:** Python/JS libraries; deployment via LangSmith Agent Server/SDK
- **Orchestration primitives:** StateGraph / compiled graphs; nodes and edges encode control flow.
- **State/persistence:** Built-in persistence layer via checkpointers; checkpoints stored in threads; enables memory, time travel, and fault tolerance.
- **HITL controls:** Interrupts pause execution, persist state, and resume upon external input.
- **Sandboxing:** HITL middleware and policies can gate tool calls; persistence enables audit and rollback.
- **Observability:** Streaming and debug stream modes surface execution events; integrates with LangSmith ecosystem.
- **Evaluation:** Evaluation is typically done via LangSmith or external harnesses; docs focus on runtime primitives.
- **Extensibility:** Custom checkpointers supported; nodes are arbitrary code; tool policies can be layered.

## 9) Evidence links

- https://docs.langchain.com/oss/python/langgraph/persistence
- https://docs.langchain.com/oss/python/langgraph/durable-execution
- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/streaming
- https://reference.langchain.com/python/langgraph/checkpoints/
