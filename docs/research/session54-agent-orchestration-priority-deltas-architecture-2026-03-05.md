# Session 54 Architecture — Priority Delta Slices (2026-03-05)

This document captures the architecture pass run after landscape research and capability mapping.

## Slice A — Durable Orchestration State

### Objective
Persist mutable control-plane state across restarts for workflow, trace, autonomy, and release surfaces.

### Proposed touchpoints
- `engine/src/agent33/api/routes/workflows.py`
- `engine/src/agent33/observability/trace_collector.py`
- `engine/src/agent33/autonomy/service.py`
- `engine/src/agent33/release/service.py`
- new shared state store module under `engine/src/agent33/orchestration/`

### Must-not-break
- Existing API response contracts unchanged
- Memory mode preserved as fallback
- Existing transition/state-machine tests remain green

### Rollback
- Feature flag to revert to memory-only behavior

## Slice B — HITL Approval Workflow

### Objective
Introduce first-class approval records and decision lifecycle for `ask` policy paths and supervised-destructive tool/command execution.

### Proposed touchpoints
- `engine/src/agent33/security/permissions.py`
- `engine/src/agent33/tools/governance.py`
- new approval service/routes under `engine/src/agent33/security/` and `engine/src/agent33/api/routes/`

### Must-not-break
- Deny-first semantics preserved
- Existing scope checks continue functioning unchanged for non-ask flows
- No broad bypass behavior introduced

### Rollback
- Disable approval workflow via config and fall back to existing blocking behavior

## Slice C — Modular Retrieval Pipeline

### Objective
Refactor retrieval path into explicit stages (rewrite/retrieve/fuse/rerank/context-build) while preserving current RAG output contracts.

### Proposed touchpoints
- `engine/src/agent33/memory/rag.py`
- new stage pipeline module under `engine/src/agent33/memory/`
- evaluation hooks for retrieval diagnostics

### Must-not-break
- `RAGResult` shape and existing call sites remain compatible
- Hybrid/vector modes preserved under config

### Rollback
- Config switch to legacy retrieval pipeline mode

## Delivery Order

1. Slice A (persistence foundation)
2. Slice B (approval/governance lifecycle)
3. Slice C (retrieval architecture upgrade)

