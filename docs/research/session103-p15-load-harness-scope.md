# P1.5 Load-Test Harness -- Research Scope Memo

**Session**: 103
**Date**: 2026-03-21
**Slice**: P1.5
**Author**: Implementer Agent

## Summary

Design and implement a repeatable load-test harness for the AGENT-33
single-instance production baseline. This is the first implementation gap
after the P1.1 horizontal-scaling architecture document and provides the
quantitative performance data needed for P1.2 (multi-replica migration)
and P1.7 (CI load-gate automation).

## Traffic Profile Rationale

### Why These Four Scenarios

The AGENT-33 API surface has hundreds of endpoints, but load testing all
of them in the first harness would produce noise without actionable signal.
The four selected scenarios cover the critical performance boundaries:

1. **Health check flood** -- the lightest endpoints. If these degrade under
   load, the deployment has a fundamental resource problem (event loop
   saturation, GC pressure, or infrastructure failure).

2. **Agent invoke chain** -- the heaviest single-request endpoint. Agent
   invocations are the primary workload and the only endpoint that blocks
   on LLM inference. This scenario establishes the end-to-end latency
   ceiling and identifies how LLM saturation affects co-located endpoints.

3. **Metrics scrape simulation** -- Prometheus scraping is a constant
   background load in production. If the `/metrics` endpoint becomes slow
   or unreliable under load, monitoring data gaps will hide real issues.

4. **Session lifecycle** -- exercises the file-backed state layer that is
   documented as a scaling blocker in `horizontal-scaling-architecture.md`.
   Measuring session contention under load provides the first empirical data
   for the P1.2 migration priority.

### User Weight Distribution

Weights (3:2:1:1) reflect realistic production traffic patterns where
monitoring probes are the highest-volume requests, agent invocations are
the primary workload, and metrics scraping plus session management are
lower-frequency background operations.

### Scenario Tiers

Three tiers (light/standard/stress) provide a progression from smoke
validation to capacity discovery:

- **Light (10 users)**: "Does the API work after deploy?" Zero failures
  expected. Suitable for post-deploy checks and local development.
- **Standard (50 users)**: "Can the API handle sustained normal load?"
  Establishes the SLO-adjacent performance baseline for the single-instance
  deployment.
- **Stress (200 users)**: "Where does the single instance break?" Identifies
  the capacity ceiling and failure modes that inform the scaling architecture.

## Tool Choice Rationale: Locust vs k6

### Evaluated Options

| Tool | Language | Protocol | Scripting | Distribution |
| --- | --- | --- | --- | --- |
| Locust | Python | HTTP | Python classes | Built-in distributed mode |
| k6 | Go | HTTP, WS, gRPC | JavaScript | k6 Cloud or xk6 extensions |
| Artillery | Node.js | HTTP, WS | YAML + JS | Artillery Cloud |
| wrk/wrk2 | C | HTTP | Lua | Single-machine only |

### Decision: Locust

Locust was selected for the following reasons:

1. **Language alignment**: AGENT-33 is a Python project. Locust scenarios
   are Python classes, which means the load test can import project modules
   (e.g., for model construction or config reading) and the team does not
   need a separate JavaScript or Lua runtime.

2. **Dev dependency simplicity**: Locust installs via pip and is added to
   the existing `[project.optional-dependencies] dev` group in
   `engine/pyproject.toml`. No additional runtimes, binaries, or package
   managers are needed.

3. **Scenario expressiveness**: The session lifecycle scenario requires
   chaining multiple HTTP requests with state carried between steps (the
   created session ID is used in subsequent GET and POST requests). Locust
   supports this natively with Python control flow. k6 can do this in
   JavaScript, but the Python implementation is more natural for this team.

4. **Distributed mode**: Locust supports distributed load generation
   with `--master` / `--worker` flags, which is sufficient for the P1.7
   CI load-gate use case without requiring cloud infrastructure.

5. **Web UI**: Locust provides a built-in web dashboard for interactive
   exploration during development, which is useful for ad-hoc tuning before
   committing to scenario parameters.

### Why Not k6

k6 is a strong tool with excellent performance characteristics (Go-based,
low resource overhead per virtual user). It was not selected because:

- JavaScript scenario authoring adds a language boundary to a Python-only
  project
- k6 binary distribution requires separate installation (not pip-native)
- The session lifecycle scenario's stateful chaining is slightly more
  verbose in k6's JavaScript API
- k6 Prometheus integration requires xk6-prometheus-rw extension, adding
  build complexity

k6 remains a valid alternative if Locust's Python GIL becomes a bottleneck
at very high user counts (>1000). For the current single-instance baseline
with up to 200 users, Locust is sufficient.

## Acceptance Criteria

### Harness Structure

- [ ] `load-tests/locustfile.py` exists and is importable
- [ ] `load-tests/locustfile.py` defines all four user classes
- [ ] Each scenario YAML exists in `load-tests/scenarios/`
- [ ] Each scenario YAML contains `users`, `spawn-rate`, and `run-time`
- [ ] README documents how to run, configure auth, and interpret results
- [ ] Single-instance baseline profile documents traffic assumptions

### Functional Acceptance

- [ ] Light scenario completes with 0 failures against a healthy instance
- [ ] Standard scenario failure rate < 1% against a healthy instance
- [ ] Stress scenario identifies the failure ceiling (expected to degrade)
- [ ] Health endpoints remain responsive under all scenarios

### Performance Targets (Single Instance)

| Endpoint | Light p95 | Standard p95 | Stress p95 |
| --- | --- | --- | --- |
| `GET /healthz` | < 50ms | < 50ms | < 200ms |
| `GET /health` | < 100ms | < 100ms | Best effort |
| `GET /metrics` | < 100ms | < 200ms | < 500ms |
| Agent invoke | < 5s | < 5s | Degraded expected |

### Non-Goals

- No new deployment infrastructure
- No premature shared-state rewrites (P1.2 scope)
- No cloud provider integrations
- No CI load-gate automation (P1.7 scope)
- No custom Locust plugins or extensions

## Dependencies

| Dependency | Version | Purpose |
| --- | --- | --- |
| `locust` | >= 2.29, < 3 | Load test framework |
| Running AGENT-33 instance | Current `main` | Target under test |
| Valid JWT token | N/A | Auth for agent invoke and session endpoints |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| Locust GIL limits at 200 users | Low | Low | Use distributed mode or accept approximate RPS |
| LLM inference dominates latency | High | Medium | Document as known limitation; propose stub backend later |
| File-backed session contention | Medium | Medium | Capture as empirical data for P1.2 migration |
| Auth token expiry during stress | Low | Low | Document long-lived token requirement |
