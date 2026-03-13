# Session 54 Research — Haystack Deep-Dive Gap Analysis (2026-03-05)

## Objective
Perform a focused, code-evidence-based teardown of `deepset-ai/haystack` and map strengths/weaknesses against AGENT-33 so we can ingest the highest-value capabilities quickly.

Reference revision used for Haystack evidence: `deepset-ai/haystack@e5f5a055eba2390759ecd2ccfa2efafef2a60563`.

## Haystack capability inventory (repo evidence)

| Area | Haystack evidence | Takeaway |
| --- | --- | --- |
| Component contract + typed sockets | `haystack/core/component/component.py`, `haystack/core/component/sockets.py`, `haystack/core/component/types.py`, `haystack/core/component/__init__.py` | Strong component abstraction with typed input/output sockets and variadic semantics. |
| Sync + async orchestration engine | `haystack/core/pipeline/base.py`, `haystack/core/pipeline/async_pipeline.py`, `haystack/core/pipeline/__init__.py` | First-class sync/async execution with graph scheduling and concurrency controls. |
| Breakpoints/snapshots for runtime debugging | `haystack/core/pipeline/breakpoint.py` | Built-in pipeline/agent pause-snapshot-resume mechanics. |
| Agent runtime with tool loops and state | `haystack/components/agents/agent.py`, `haystack/components/agents/state/state.py`, `haystack/components/agents/__init__.py` | Agent loop is componentized and stateful with explicit step limits, snapshot recovery, and tool integration. |
| Tool invocation stack + toolsets | `haystack/components/tools/tool_invoker.py`, `haystack/tools/tool.py`, `haystack/tools/toolset.py`, `haystack/tools/searchable_toolset.py`, `haystack/tools/pipeline_tool.py`, `haystack/tools/component_tool.py`, `haystack/tools/__init__.py` | Rich tool abstraction layer (toolsets, wrappers, invocation orchestration, searchability). |
| HITL strategies/policies | `haystack/human_in_the_loop/__init__.py`, `haystack/human_in_the_loop/policies.py`, `haystack/human_in_the_loop/strategies.py`, `haystack/human_in_the_loop/user_interfaces.py` | Pluggable human-confirmation policies and interaction strategies beyond single approval endpoints. |
| Router library | `haystack/components/routers/__init__.py`, `haystack/components/routers/*.py` | Broad reusable router operators (conditional, metadata, language, file/doc-type, zero-shot). |
| Retrieval modularity | `haystack/components/retrievers/__init__.py`, `haystack/components/retrievers/*.py`, `haystack/components/joiners/*.py`, `haystack/components/rankers/*.py` | Retrieval is composable via retrievers + joiners + rerankers, not one fixed pipeline. |
| Evaluator components | `haystack/components/evaluators/__init__.py`, `haystack/components/evaluators/*.py`, `haystack/evaluation/eval_run_result.py` | Evaluation is expressed as reusable pipeline components and result artifacts. |
| Tracing abstraction + OTel bridge | `haystack/tracing/__init__.py`, `haystack/tracing/tracer.py`, `haystack/tracing/opentelemetry.py` | Strong tracer abstraction with backend pluggability and auto-enable behavior. |
| Super-component composition | `haystack/core/super_component/super_component.py`, `haystack/core/super_component/__init__.py` | Pipelines can be wrapped/reused as higher-level components with explicit mapping. |
| Provider/integration surface breadth | `haystack/components/generators/*.py`, `pyproject.toml` | Broad provider and integration footprint with optional extras for many workflows. |

## AGENT-33 posture vs Haystack strengths

| Topic | AGENT-33 evidence | Assessment |
| --- | --- | --- |
| MCP production readiness | `engine/src/agent33/api/routes/mcp.py` | **Gap**: route is still prototype/placeholder transport. |
| Workflow state durability | `engine/src/agent33/api/routes/workflows.py` | **Gap**: workflow registry/history still in-memory at route layer. |
| Workflow execution engine | `engine/src/agent33/workflows/executor.py` | **Strength**: robust DAG execution/retry/parallel behavior already present. |
| Hybrid retrieval baseline | `engine/src/agent33/memory/hybrid.py`, `engine/src/agent33/memory/rag.py` | **Strength**: BM25+vector fusion exists; diagnostics recently added. |
| HITL approvals/governance | `engine/src/agent33/tools/approvals.py`, `engine/src/agent33/tools/governance.py`, `engine/src/agent33/api/routes/tool_approvals.py` | **Strength**: lifecycle + one-time consumption exists; **Gap**: less policy/strategy/UI modularity than Haystack HITL stack. |
| Durable orchestration store | `engine/src/agent33/services/orchestration_state.py` | **Strength**: shared atomic JSON namespace persistence now exists. |
| Tracing integration depth | `engine/src/agent33/observability/tracing.py` | **Gap**: thin wrapper, console exporter default, limited runtime span strategy compared to Haystack tracer abstraction. |
| Plugin ecosystem controls | `engine/src/agent33/api/routes/plugins.py` | **Partial**: strong management API; still maturing persistence/governance breadth. |

## Weaknesses to prioritize (Haystack-informed)

1. **MCP runtime surface is not production-complete** (`api/routes/mcp.py`).
2. **Workflow registry/history still in-memory** (`api/routes/workflows.py`).
3. **No reusable router pack equivalent** (`workflows/actions/route.py` is single action, not router library).
4. **Retrieval graph not yet fully pluggable** (currently centered on `memory/rag.py` + `memory/hybrid.py`).
5. **Tracing architecture is thinner than Haystack's tracer abstraction** (`observability/tracing.py`).
6. **HITL is approval-centric, not strategy-centric** (`tools/approvals.py`, `tools/governance.py`).

## Candidate skill expansions (AGENT-33)

| Skill | Scope | Primary target files |
| --- | --- | --- |
| `mcp-server-hardening` | Replace placeholder MCP transport + request lifecycle handling | `engine/src/agent33/api/routes/mcp.py` |
| `workflow-durability-upgrade` | Persist workflow registry/history + restart-safe operations | `engine/src/agent33/api/routes/workflows.py`, `engine/src/agent33/services/orchestration_state.py` |
| `router-pack-authoring` | Add reusable routing operators (metadata/conditional/language/type) | `engine/src/agent33/workflows/actions/route.py`, new router module set |
| `retrieval-graph-composer` | Introduce retriever/joiner/ranker stage interfaces | `engine/src/agent33/memory/rag.py`, `engine/src/agent33/memory/hybrid.py`, new memory stage modules |
| `hitl-strategy-framework` | Add policy/strategy abstractions over approvals | `engine/src/agent33/tools/approvals.py`, `engine/src/agent33/tools/governance.py`, `engine/src/agent33/api/routes/tool_approvals.py` |
| `otel-trace-enrichment` | Expand tracing backend and span correlation | `engine/src/agent33/observability/tracing.py`, trace collector integration points |
| `workflow-supercomponents` | Wrap reusable workflow graphs as callable components/tools | new composition module + `engine/src/agent33/workflows/*`, `engine/src/agent33/tools/*` |

## Recommended execution waves

### Wave 1 (quick wins)
- MCP hardening
- Workflow registry/history persistence
- Router pack v1 (conditional + metadata + policy fallback)
- Trace enrichment baseline

### Wave 2 (modular architecture)
- Retrieval stage interfaces (retriever/joiner/ranker)
- HITL strategy/policy adapters over current approval lifecycle
- Tool invoker standardization for richer toolset composition

### Wave 3 (platform leverage)
- Super-component style workflow composition
- Typed component/socket contracts for workflow interoperability
- Evaluator-component parity for richer quality loops

## Notes
- AGENT-33 already closed three previously identified deltas (durable state, HITL lifecycle, modular retrieval diagnostics).
- This deep-dive shifts next work from baseline parity into composition maturity and operator-grade runtime surfaces.
