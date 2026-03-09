# Session 61 Phase 38 Docker Kernel Architecture

Date: 2026-03-09

## Goal

Finish the Phase 38 Stage 3 / Phase 42 follow-on work by turning Jupyter execution into a first-class execution backend and adding Docker-backed kernel sessions with explicit controls.

## Current Gaps

- `execution/adapters/jupyter.py` is not a `BaseAdapter` implementation.
- Jupyter execution bypasses `ExecutionContract` and returns ad hoc dicts.
- Workflow `execute-code` drops execution artifacts and session metadata.
- `engine/pyproject.toml` does not expose the documented `jupyter` extra.
- There is no typed configuration surface for container image, mount, or network policy.
- Startup does not register a Jupyter adapter with the shared `CodeExecutor`.

## Implementation Shape

### 1. Typed Kernel Adapter Contract

Extend execution models with:

- `OutputArtifact` as a typed execution artifact.
- `KernelContainerPolicy` for Docker controls.
- `KernelInterface` on `AdapterDefinition` for kernel config.
- `ExecutionResult.metadata` so session identifiers and backend details survive workflow execution.

### 2. Real Adapter Refactor

Refactor `JupyterAdapter` to:

- subclass `BaseAdapter`
- accept `ExecutionContract`
- read code from `contract.inputs.stdin`
- read language / session metadata from `contract.metadata`
- return `ExecutionResult`

The adapter will support both:

- local kernels via `jupyter_client.AsyncKernelManager`
- Docker kernels via a mounted Jupyter connection file plus a long-lived `docker run` container

### 3. Container Session Controls

Docker-backed kernels must expose explicit controls for:

- image selection
- allowed image allowlist
- network enabled vs `--network none`
- runtime connection-file mount
- optional working-directory mount
- container workdir
- extra `docker run` arguments for future hardening

### 4. Workflow Integration

`workflows/actions/execute_code.py` must preserve:

- `artifacts`
- `metadata`
- session identifiers

That keeps notebook outputs and stateful session handles visible to downstream workflow steps and UI/API consumers.

### 5. Runtime Registration

Add opt-in settings so startup can register a default Jupyter adapter without breaking existing environments:

- disabled by default
- configurable local vs Docker mode
- configurable tool id / adapter id
- configurable Docker image / allowlist / network policy

## Validation Plan

- Unit tests for model extensions and language mapping.
- Unit tests for session-manager reuse and one-shot cleanup.
- Unit tests for Docker command construction and allowlist enforcement.
- Unit tests for adapter execution result shaping.
- Unit tests for workflow action artifact propagation.
- Targeted executor + adapter + workflow pytest run in the feature worktree.

## Deferred Items

- End-to-end Docker integration tests are deferred until CI provides Docker-in-Docker or equivalent runtime support.
- Rich file artifact extraction from notebook cells is left for a later runtime/reporting slice; this PR focuses on in-band execution artifacts and containerized sessions.
