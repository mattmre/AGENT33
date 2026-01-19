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

## Entries
Format:
- `YYYY-MM-DD` - cycle-id - PR/branch - command - result - notes
Default location for per-cycle logs:
- `docs/ARCH AGENTIC ENGINEERING AND PLANNING/cycles/YYYY-MM-DD/verification-log.md`
- `2026-01-16` - N/A - N/A - N/A (no test suite found) - not run - documented in session log
- `2026-01-16` - orchestration-2 - N/A - N/A (no test suite found) - not run - documented in session log
- `2026-01-16` - phase-3-4 - N/A - N/A (no test suite found) - not run - documented in phase logs
- `2026-01-16` - phase-3-4-review-integration - N/A - `Get-ChildItem -Recurse -Force -File -Include *.ps1,*.sh,*.cmd,*.bat,package.json,pyproject.toml,pytest.ini,go.mod,Cargo.toml,Makefile -ErrorAction SilentlyContinue`; `rg -n "pytest|npm test|go test|dotnet test|cargo test|mix test|ctest|ruff|mypy|eslint|flake8|black" -S .`; `Get-ChildItem -Force .github` - not run (no test suite found) - documented in session log
- `2026-01-16` - phase-5-policy-pack - N/A - N/A (docs-only; no test harness in repo) - not run - documented in phase log
- `2026-01-16` - phase-3-4-review-status - N/A - `Get-ChildItem -Recurse -File -Include *.ps1,*.sh,*.cmd,*.bat,package.json,pyproject.toml,pytest.ini,go.mod,Cargo.toml,Makefile,*.csproj,*.sln -ErrorAction SilentlyContinue`; `Get-ChildItem -Force <repo-root>/.github -ErrorAction SilentlyContinue` - not run (no test suite found) - documented in session log
- `2026-01-16` - phase-6-tooling-governance - N/A - N/A (docs-only; no test harness in repo) - not run - documented in phase log
- `2026-01-16` - phase-11-20-planning - N/A - N/A (docs-only; no test harness in repo) - not run - documented in phase log
## Index
| date | cycle-id | PR/branch | command | result | rationale link | link |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-01-16 | N/A | N/A | N/A (no test suite found) | not run | `docs/session-logs/SESSION-2026-01-16_AGENT-33-ORCHESTRATION.md` | N/A |
| 2026-01-16 | orchestration-2 | N/A | N/A (no test suite found) | not run | `docs/session-logs/SESSION-2026-01-16_AGENT-33-ORCHESTRATION-2.md` | N/A |
| 2026-01-16 | phase-3-4 | N/A | N/A (no test suite found) | not run | `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-3.md`, `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-4.md` | [PR #1](https://github.com/mattmre/AGENT-33/pull/1) |
| 2026-01-16 | phase-3-4-review-integration | N/A | No test suite found (repo docs-only) | not run | `docs/session-logs/SESSION-2026-01-16_AGENT-33-QA-REPORT.md` | [PR #1](https://github.com/mattmre/AGENT-33/pull/1) |
| 2026-01-16 | phase-5-policy-pack | N/A | N/A (docs-only; no test harness in repo) | not run | `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-5.md` | [PR #1](https://github.com/mattmre/AGENT-33/pull/1) |
| 2026-01-16 | phase-3-4-review-status | N/A | N/A (no test suite found) | not run | `docs/session-logs/SESSION-2026-01-16_AGENT-33-QA-REPORT-2.md` | [PR #1](https://github.com/mattmre/AGENT-33/pull/1) |
| 2026-01-16 | phase-6-tooling-governance | N/A | N/A (docs-only; no test harness in repo) | not run | `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-6.md` | [PR #1](https://github.com/mattmre/AGENT-33/pull/1) |
| 2026-01-16 | phase-11-20-planning | N/A | N/A (docs-only; no test harness in repo) | not run | `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-11-20-PLANNING.md` | [PR #2](https://github.com/mattmre/AGENT-33/pull/2) |
| 2026-01-16 | phase-7-evidence | ask/T4-7-spec-first-harness | `ls core/orchestrator/handoff/EVIDENCE_CAPTURE.md` | verified (file exists, sections added) | `docs/session-logs/SESSION-2026-01-16_AGENT-33_PHASE-7.md` | [PR #1](https://github.com/mattmre/AGENT-33/pull/1) |

