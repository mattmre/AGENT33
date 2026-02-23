# Phase 28: Enterprise Security Scanning Integration

## Status: In Progress

## Overview
- **Phase**: 28 of 28+
- **Category**: Security / Product Safety / Release Readiness
- **Primary Goal**: Integrate enterprise-grade security scanning capabilities into the AGENT-33 backend and frontend, using trusted tools (Claude Code Security, Semgrep MCP, Trivy MCP, LLM Guard, Garak) to provide pre-production security validation.

## Objectives
- Add first-class AGENT-33 support for launching component security tests against local repository targets using enterprise-backed tooling.
- Provide SARIF 2.1.0 output format for CI/CD integration and GitHub Security tab upload.
- Support MCP-based security server integration for pluggable scan providers.
- Add AI/LLM-specific security scanning (prompt injection, OWASP MCP Top 10, tool poisoning detection).
- Provide a frontend security dashboard for running scans and reviewing findings.
- Gate production release flows on required component security checks.

## Trust Hierarchy
1. **Anthropic first-party** — Claude Code Security
2. **Enterprise-backed** — Snyk, Cisco, Google, AWS
3. **Established OSS** — Semgrep, Trivy, NVIDIA Garak, Protect AI LLM Guard (1000+ stars, active maintenance)
4. **Community** — Evaluate case-by-case, require code review
5. **Unknown** — DO NOT USE

## Scope

### In Scope
- Security scan service with subprocess-based tool execution (bandit, gitleaks, semgrep, pip-audit).
- SARIF 2.1.0 converter for industry-standard output format.
- MCP security server integration for pluggable scan providers.
- AI/LLM security scanning (prompt injection detection, tool poisoning, OWASP MCP Top 10).
- API routes for creating test runs, querying run status, retrieving findings, and SARIF export.
- Frontend security dashboard with scan history, findings table, and severity distribution.
- Evidence capture for release readiness (security run ID, result summary, timestamp, operator).

### Out of Scope
- Replacing existing CI SAST/DAST platforms.
- Internet-facing public scan orchestration.
- Automatic remediation code generation.
- Multi-tenant billing/usage accounting.

## Deliverables

| # | Deliverable | Target Path | Description |
|---|-------------|-------------|-------------|
| 1 | Integration analysis | `docs/research/phase28-pentagi-integration-analysis.md` | Archived analysis (superseded by enterprise security approach) |
| 2 | Security scan service | `engine/src/agent33/services/security_scan.py` | Launch, monitor, and normalize security test runs |
| 3 | SARIF converter | `engine/src/agent33/component_security/sarif.py` | SARIF 2.1.0 bidirectional conversion |
| 4 | MCP scanner | `engine/src/agent33/component_security/mcp_scanner.py` | MCP security server integration |
| 5 | LLM security scanner | `engine/src/agent33/component_security/llm_security.py` | AI-specific security scanning |
| 6 | Component security API routes | `engine/src/agent33/api/routes/component_security.py` | Authenticated endpoints for run lifecycle + findings + SARIF |
| 7 | Release gate wiring | `engine/src/agent33/release/security_gate.py` | Pre-release check against security run |
| 8 | Frontend security dashboard | `frontend/src/features/security-dashboard/` | UI for running scans and reviewing results |
| 9 | Backend tests | `engine/tests/test_*.py` | Route, service, and converter tests |
| 10 | Frontend tests | `frontend/src/features/security-dashboard/__tests__/` | Dashboard and interaction tests |
| 11 | Progress/evidence log | `docs/progress/phase-28-pentagi-component-security-log.md` | Validation commands, outputs, issues, and fixes |

Note: target paths above are planned implementation locations to be created during Phase 28 delivery.

## Acceptance Criteria
- [ ] Operators can create a component security test run from the AGENT-33 frontend dashboard.
- [ ] Test runs execute using subprocess-based tools (bandit, gitleaks, semgrep, pip-audit).
- [ ] Findings are normalized to a consistent severity model and exposed via API + UI.
- [ ] SARIF 2.1.0 export is available for any completed scan run.
- [ ] MCP security servers can be registered as pluggable scan providers.
- [ ] AI/LLM security scanning detects prompt injection and tool poisoning patterns.
- [ ] Each run stores evidence metadata suitable for release signoff.
- [ ] Release workflow can enforce a configurable policy (e.g., block on HIGH/CRITICAL findings).
- [ ] Backend and frontend tests pass for all new security scanning workflows.

## Dependencies
- Phase 14 (security hardening and policy model)
- Phase 19 (release gate and rollback automation)
- Phase 22 (website platform and authenticated frontend flows)

## Orchestration Guidance
1. **Stage 1: Rename PentAGI → SecurityScan** (zero functional changes)
2. **Stage 2: SARIF 2.1.0 + Claude Code Security integration**
3. **Stage 3: MCP security server integration**
4. **Stage 4: AI/LLM security layer**
5. **Stage 5: Frontend security dashboard**

Stages 2-4 can proceed in parallel after Stage 1. Stage 5 depends on Stages 2-4 for API endpoints.

## Review Checklist
- [ ] Security review of tool execution boundaries and subprocess sandboxing.
- [ ] API contract review for run state transitions and findings schema.
- [ ] SARIF 2.1.0 schema compliance verification.
- [ ] MCP server trust validation (enterprise-backed only).
- [ ] UX review for operator clarity (run controls, severity visibility, remediation path).
- [ ] Release workflow review for safe default gating behavior.

## References
- SARIF 2.1.0 specification: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
- Claude Code Security: Anthropic first-party AI vulnerability scanner
- OWASP MCP Top 10: Tool poisoning, supply chain attack patterns
- Semgrep MCP: semgrep/mcp — SAST via MCP
- Trivy MCP: aquasecurity/trivy-mcp — vulnerability/config/secret scanning via MCP
- LLM Guard: Protect AI (MIT, 4.5k+ stars)
- Garak: NVIDIA (Apache-2.0, 3k+ stars)
- Phase 14 spec: `docs/phases/PHASE-14-SECURITY-HARDENING-AND-PROMPT-INJECTION-DEFENSE.md`
- Phase 19 spec: `docs/phases/PHASE-19-RELEASE-AND-SYNC-AUTOMATION.md`
- Phase 22 spec: `docs/phases/PHASE-22-UNIFIED-UI-PLATFORM-AND-ACCESS-LAYER.md`
