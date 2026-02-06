# Verification Log

## Usage
Use this log for long-term evidence of test execution and validation results.
When a task closes, record the test command, outcome, and related task ID.

Purpose: Store build/test evidence per PR in a lightweight, searchable format.

## Indexing and Naming Rules
- **Entry Format**: `YYYY-MM-DD` - cycle-id - PR/branch - command - result - notes
- **Cycle ID**: Use task ID (e.g., T13) or descriptive slug (e.g., phase-7-evidence)
- **Artifact Path**: `docs/session-logs/SESSION-YYYY-MM-DD_<DESCRIPTION>.md`
- **Cross-reference**: Always link to session log containing full evidence capture

## Partial Run Guidance
When full test suite cannot run (missing deps, docs-only repo, partial environment):

1. **Document Why**: Record the reason tests cannot run (no harness, env issues, etc.)
2. **Record Attempt**: Log the commands tried and their failure output
3. **Alternative Verification**: Use available checks:
   - Link validation: `rg -n "\\[.*\\]\\(.*\\)" <file> | head -20`
   - Markdown lint: `markdownlint <file>` (if available)
   - Doc structure check: `ls -la <dir>` to confirm file presence
4. **Explicit N/A**: Mark result as "not run (reason)" not just blank
5. **Escalation**: If critical verification blocked, note in session log for follow-up

## Example Partial Run Entry
- `2026-01-16` - T13 - phase-7-branch - N/A (docs-only repo; no test harness) - not run - Verified via doc audit: `ls core/orchestrator/handoff/` confirmed templates exist; link check passed

## Current Editor Lock
- current editor:
- lock timestamp:

## Index
| date | cycle-id | PR/branch | command | result | rationale link | link |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-16 | N/A | N/A | N/A (no test suite found) | not run | Session log (removed in sanitization pass) | N/A |
| 2026-01-16 | orchestration-2 | N/A | N/A (no test suite found) | not run | Session log (removed in sanitization pass) | N/A |
| 2026-01-16 | phase-3-4 | N/A | N/A (no test suite found) | not run | Session logs for Phase 3 and Phase 4 (removed in sanitization pass) | [PR #1](https://github.com/mattmre/Agent-33/pull/1) |
| 2026-01-16 | phase-3-4-review-integration | N/A | No test suite found (repo docs-only) | not run | QA report (removed in sanitization pass) | [PR #1](https://github.com/mattmre/Agent-33/pull/1) |
| 2026-01-16 | phase-5-policy-pack | N/A | N/A (docs-only; no test harness in repo) | not run | Phase 5 session log (removed in sanitization pass) | [PR #1](https://github.com/mattmre/Agent-33/pull/1) |
| 2026-01-16 | phase-3-4-review-status | N/A | N/A (no test suite found) | not run | QA report 2 (removed in sanitization pass) | [PR #1](https://github.com/mattmre/Agent-33/pull/1) |
| 2026-01-16 | phase-6-tooling-governance | N/A | N/A (docs-only; no test harness in repo) | not run | Phase 6 session log (removed in sanitization pass) | [PR #1](https://github.com/mattmre/Agent-33/pull/1) |
| 2026-01-16 | phase-11-20-planning | N/A | N/A (docs-only; no test harness in repo) | not run | Phase 11-20 planning session log (removed in sanitization pass) | N/A |
| 2026-01-16 | phase-7-evidence | ask/T4-7-spec-first-harness | `ls core/orchestrator/handoff/EVIDENCE_CAPTURE.md` | verified (file exists, sections added) | Phase 7 session log (removed in sanitization pass) | [PR #1](https://github.com/mattmre/Agent-33/pull/1) |
| 2026-01-16 | T15-phase-8-harness | ask/phase-8-20-governance-docs | `ls core/arch/evaluation-harness.md` | verified (7 golden tasks, 4 cases, 5 metrics, playbook) | Phase 8 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T16-phase-8-eval | ask/phase-8-20-governance-docs | `ls core/arch/evaluation-report-template.md` | verified (template with all sections, M-05 added) | Phase 8 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T17-phase-11-registry | ask/phase-8-20-governance-docs | `ls core/orchestrator/AGENT_REGISTRY.md` | verified (10 agents, 25 capabilities, YAML schema, onboarding) | Phase 11 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T18-phase-11-routing | ask/phase-8-20-governance-docs | `ls core/orchestrator/AGENT_ROUTING_MAP.md` | verified (registry IDs, escalation chains, workflows) | Phase 11 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T19-phase-12-change-control | ask/phase-8-20-governance-docs | `ls core/orchestrator/TOOL_REGISTRY_CHANGE_CONTROL.md` | verified (4 checklists, 12 provenance checks, 5 MCP checks, 3 baseline tools) | Phase 12 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T20-phase-12-deprecation | ask/phase-8-20-governance-docs | `ls core/orchestrator/TOOL_DEPRECATION_ROLLBACK.md` | verified (4-phase deprecation, 3 rollback procedures) | Phase 12 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T21-phase-13-execution | ask/phase-8-20-governance-docs | `ls core/orchestrator/CODE_EXECUTION_CONTRACT.md` | verified (execution schema, sandbox limits, adapter template) | Phase 13 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T22-phase-14-security | ask/phase-8-20-governance-docs | `ls core/orchestrator/SECURITY_HARDENING.md` | verified (prompt injection defense, sandbox approvals, secrets handling) | Phase 14 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T23-phase-15-review | ask/phase-8-20-governance-docs | `ls core/orchestrator/TWO_LAYER_REVIEW.md` | verified (two-layer review, signoff flow, reviewer assignment) | Phase 15 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T24-phase-16-trace | ask/phase-8-20-governance-docs | `ls core/orchestrator/TRACE_SCHEMA.md` | verified (trace schema, failure taxonomy, artifact retention) | Phase 16 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T25-phase-17-regression | ask/phase-8-20-governance-docs | `ls core/arch/REGRESSION_GATES.md` | verified (regression gates, triage playbook, golden task tags) | Phase 17 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T26-phase-18-autonomy | ask/phase-8-20-governance-docs | `ls core/orchestrator/AUTONOMY_ENFORCEMENT.md` | verified (preflight checks, enforcement, escalation) | Phase 18 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T27-phase-19-release | ask/phase-8-20-governance-docs | `ls core/orchestrator/RELEASE_CADENCE.md` | verified (release cadence, sync automation, rollback) | Phase 19 session log (removed in sanitization pass) | N/A |
| 2026-01-16 | T28-phase-20-improvement | ask/phase-8-20-governance-docs | `ls core/orchestrator/CONTINUOUS_IMPROVEMENT.md` | verified (5 research types, intake template, 15 CI checks, lessons learned) | Phase 20 session log (removed in sanitization pass) | N/A |
