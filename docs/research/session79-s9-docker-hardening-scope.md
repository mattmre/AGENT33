# Session 79 S9: Phase 38 Docker Kernel Hardening Scope

**Date:** 2026-03-12  
**Slice:** `S9 - Phase 38 Stage 3 Docker kernel hardening`

## Baseline

The merged baseline already includes the core Docker-backed Jupyter adapter work:

- `JupyterAdapter` is registered as a real execution adapter
- `DockerKernelSession` can build and launch container-backed kernels
- typed kernel/container config exists in `execution.models`
- targeted adapter tests already cover definition building and the basic Docker command shape

This is a hardening slice, not a first implementation slice.

## Current Gaps

1. **Sandbox resource limits are not yet reflected in Docker runtime flags.**
   - `SandboxConfig.memory_mb` and `SandboxConfig.cpu_cores` do not currently shape the `docker run` command.

2. **Container startup failure handling is still thin.**
   - the adapter waits for kernel readiness, but the container lifecycle does not yet expose an explicit post-start health check or strong assertions around cleanup on readiness failure.

3. **Direct Docker-session regression depth is still limited.**
   - current tests cover command construction, but not the harder paths around startup failure, cleanup, and hardening flags.

## Included Work

1. Wire container resource controls into the Docker kernel runtime in a way that stays compatible with stateful kernel sessions.
2. Add startup/cleanup hardening for failed or unhealthy Docker kernel launches.
3. Expand direct `DockerKernelSession` regressions for:
   - resource flags
   - readiness failure cleanup
   - health-check / lifecycle edge cases
4. Re-run focused adapter/workflow regressions on the hardened path.

## Explicit Non-Goals

- redesigning the Jupyter adapter contract
- broader Phase 42 notebook UX changes
- unrelated streaming-agent-loop work from earlier Phase 38 stages
- new operator docs unless the implementation materially changes the current runbook

## Acceptance

- Docker kernel launches honor the intended memory/CPU constraints
- failed startup paths do not leave behind stale runtime state
- direct Docker-session tests cover the hardened launch/cleanup behavior
- focused execution adapter regressions remain green from a fresh worktree

## CI Follow-up

- Full-suite CI exposed a separate determinism issue in `engine/tests/test_processes_api.py`.
- The process start route intentionally reuses shell-tool governance preflight, so a production-initialized app can require `tools:execute` in addition to `processes:manage`.
- The async API test only passed in isolation when `app.state.tool_governance` had not been initialized, which made the behavior suite-order dependent.
- The fix is to install a fresh `ToolGovernance` instance in that test module and assert the governed start behavior explicitly.
