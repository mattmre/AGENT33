# Phase 28: PentAGI Component Security Testing Integration

## Status: Planned

## Overview
- **Phase**: 28 of 28+
- **Category**: Security / Product Safety / Release Readiness
- **Primary Goal**: Integrate PentAGI component-level security testing capabilities into the AGENT-33 website and backend workflows so teams can run local pre-production security validation before deployment.

## Objectives
- Add first-class AGENT-33 support for launching PentAGI-backed component security tests against local repository targets.
- Provide website workflows to configure test profiles, run scans, and review actionable findings.
- Capture security test artifacts and decisions as deployment evidence.
- Gate production release flows on required component security checks.

## Scope

### In Scope
- Backend integration layer for PentAGI-triggered component security test execution.
- API routes for creating test runs, querying run status, and retrieving findings.
- Website UX for:
  - selecting a repository/component target
  - running a predefined security profile
  - viewing findings and remediation guidance
- Evidence capture for release readiness (security run ID, result summary, timestamp, operator).
- Local-first execution path for developer machines and pre-prod validation.

### Out of Scope
- Replacing existing CI SAST/DAST platforms.
- Internet-facing public scan orchestration.
- Automatic remediation code generation.
- Multi-tenant billing/usage accounting.

## Deliverables

| # | Deliverable | Target Path | Description |
|---|-------------|-------------|-------------|
| 1 | PentAGI integration spec | `docs/research/phase28-pentagi-integration-analysis.md` | Adapter contract, profiles, execution model, and risk controls |
| 2 | PentAGI integration service | `engine/src/agent33/services/pentagi_integration.py` | Launch, monitor, and normalize PentAGI security test runs |
| 3 | Component security API routes | `engine/src/agent33/api/routes/component_security.py` | Authenticated endpoints for run lifecycle + findings |
| 4 | Website component security workspace | `frontend/src/components/component-security/` | UI for running scans and viewing results |
| 5 | Release gate wiring | `engine/src/agent33/release/` | Optional/required pre-release check against latest component security run |
| 6 | Backend tests | `engine/tests/test_component_security_api.py` | Route and service behavior coverage |
| 7 | Frontend tests | `frontend/src/components/component-security/*.test.tsx` | UX and data flow validation |
| 8 | Progress/evidence log | `docs/progress/phase-28-pentagi-component-security-log.md` | Validation commands, outputs, issues, and fixes |

Note: target paths above are planned implementation locations to be created during Phase 28 delivery.

## Acceptance Criteria
- [ ] Operators can create a component security test run from the AGENT-33 website.
- [ ] Test runs execute against local/pre-production repository targets in isolated containers.
- [ ] Findings are normalized to a consistent severity model and exposed via API + UI.
- [ ] Each run stores evidence metadata suitable for release signoff.
- [ ] Release workflow can enforce a configurable policy (e.g., block on HIGH/CRITICAL findings).
- [ ] Backend and frontend tests pass for the new component security workflows.
- [ ] Documentation includes local setup, profile usage, and troubleshooting guidance.

## Dependencies
- Phase 14 (security hardening and policy model)
- Phase 19 (release gate and rollback automation)
- Phase 22 (website platform and authenticated frontend flows)

## Blocks
- PentAGI availability and stable interface for local orchestration.
- Policy agreement on severity thresholds for production gating.

## Orchestration Guidance
1. **Research and contract first**
   - Define a strict adapter contract between AGENT-33 and PentAGI.
   - Define security profile presets (quick, standard, deep).
2. **Build backend integration**
   - Implement service abstractions for run submission/status/fetch findings.
   - Normalize PentAGI output into AGENT-33 domain models.
3. **Add website workflows**
   - Add run creation, run history, and findings detail views.
   - Surface gating status clearly for release operators.
4. **Wire release gate**
   - Add policy check in release flow requiring recent passing component security run.
5. **Validate and capture evidence**
   - Run local and pre-prod smoke scenarios.
   - Record findings and remediation loop evidence in the progress log.

## Review Checklist
- [ ] Security review of PentAGI execution boundaries and sandbox model.
- [ ] API contract review for run state transitions and findings schema.
- [ ] UX review for operator clarity (run controls, severity visibility, remediation path).
- [ ] Release workflow review for safe default gating behavior.
- [ ] Documentation review for local setup and repeatable validation commands.

## References
- PentAGI repository: https://github.com/vxcontrol/pentagi
- PentAGI README features section (sandboxed execution, 20+ tools, testing workflows)
- Phase 14 spec: `docs/phases/PHASE-14-SECURITY-HARDENING-AND-PROMPT-INJECTION-DEFENSE.md`
- Phase 19 spec: `docs/phases/PHASE-19-RELEASE-AND-SYNC-AUTOMATION.md`
- Phase 22 spec: `docs/phases/PHASE-22-UNIFIED-UI-PLATFORM-AND-ACCESS-LAYER.md`
