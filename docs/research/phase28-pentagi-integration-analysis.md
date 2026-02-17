# Phase 28 Integration Analysis: PentAGI Component Security Testing (2026-02-17)

## Executive Summary

This document defines the technical integration architecture and operational patterns for embedding PentAGI component security testing capabilities into AGENT-33 workflows. Phase 28 delivers a first-class security validation surface that operators can use to run pre-deployment security scans against local repository targets, review normalized findings, and enforce release gate policies based on security run outcomes.

**Status**: Planning complete; ready for adapter contract implementation and backend service scaffolding.

---

## Context

AGENT-33's release automation (Phase 19) and security hardening (Phase 14) established deployment gating and policy enforcement patterns. Phase 28 integrates PentAGI—an LLM-powered security testing framework with sandboxed execution and 20+ security tools—as a component-level validation step in the pre-production release pipeline.

### Upstream Foundation

PentAGI (https://github.com/vxcontrol/pentagi) provides:
- Sandboxed Docker execution environment for security tools
- LLM-driven test orchestration and result interpretation
- Support for SAST, DAST, dependency scanning, secrets detection, and more
- JSON-structured findings output

Phase 28 adapts PentAGI for AGENT-33's local-first workflow validation context, ensuring security validation evidence is captured before production deployment.

---

## Architecture Blueprint

### Backend Components

```
engine/src/agent33/
├── services/
│   └── pentagi_integration.py       # Core PentAGI adapter service
├── api/routes/
│   └── component_security.py        # API routes for test run lifecycle
├── component_security/
│   └── models.py                    # SecurityRun, SecurityFinding models
└── release/
    └── security_gate.py             # Release gate policy enforcement
```

Note: paths in this blueprint are target implementation locations for Phase 28 and are created as work progresses.

**Key responsibilities**:
- **PentAGI adapter**: Launch PentAGI containers, monitor execution, parse output
- **API routes**: CRUD operations for security runs + findings retrieval
- **Models**: Domain models for run metadata and normalized findings
- **Release gate**: Policy check enforcing security run requirements before deployment

### Frontend Components

```
frontend/src/
├── components/component-security/
│   ├── SecurityRunForm.tsx          # Create new security test run
│   ├── SecurityRunList.tsx          # Browse recent runs
│   ├── SecurityRunDetail.tsx        # View run status and findings
│   └── SecurityFindingsTable.tsx    # Filterable findings display
├── data/domains/
│   └── component-security.ts        # API operation definitions
└── types/
    └── security.ts                  # TypeScript types for runs/findings
```

**Key responsibilities**:
- **Run creation**: Select target repo/commit, choose profile, submit run
- **Run monitoring**: Display run status (pending/running/completed/failed)
- **Findings review**: Severity-filtered table with remediation guidance
- **Release context**: Display gating status for release operators

---

## Adapter Contract Proposal

### PentAGI Execution Interface

**Container launch pattern**:
```python
# Simplified adapter contract
class PentAGIAdapter:
    def launch_scan(
        self,
        target_path: str,
        profile: SecurityProfile,
        timeout_seconds: int = 600
    ) -> SecurityRun:
        """Launch PentAGI security scan container."""
        
    def get_run_status(self, run_id: str) -> RunStatus:
        """Query current run state."""
        
    def fetch_findings(self, run_id: str) -> List[SecurityFinding]:
        """Retrieve normalized findings from completed run."""
        
    def cancel_run(self, run_id: str) -> None:
        """Stop running scan container."""
```

**Execution model**:
- PentAGI runs in isolated Docker container with mounted target repository
- AGENT-33 backend polls container status via Docker API
- Findings written to shared volume, parsed by adapter on completion
- Container cleanup triggered after findings retrieval or timeout

_Stage 1 implementation note_: The current Phase 28 Stage 1 backend uses direct subprocess
invocations of `bandit` and `gitleaks` for the quick profile, with target-path allowlist
validation enforced by the API service. Full Docker-orchestrated PentAGI container execution
remains the target architecture for later stages.

### API Route Structure

```
POST   /v1/component-security/runs               # Create new security test run
GET    /v1/component-security/runs               # List recent runs (filtered by status/profile)
GET    /v1/component-security/runs/{run_id}      # Get run details and metadata
GET    /v1/component-security/runs/{run_id}/findings  # Retrieve findings for run
DELETE /v1/component-security/runs/{run_id}      # Cancel/delete run
```

### Request Schema: Create Run

```json
{
  "target": {
    "repository_path": "/workspaces/agent33",
    "commit_ref": "abc123def",
    "branch": "feat/phase-28"
  },
  "profile": "standard",
  "options": {
    "timeout_seconds": 600,
    "fail_on_high": true,
    "scan_dependencies": true,
    "scan_secrets": true
  },
  "metadata": {
    "requested_by": "operator-id",
    "session_id": "session-456",
    "release_candidate_id": "rc-2026-02-20"
  }
}
```

### Response Schema: Run Details

```json
{
  "run_id": "secrun-789",
  "status": "completed",
  "profile": "standard",
  "target": {
    "repository_path": "/workspaces/agent33",
    "commit_ref": "abc123def",
    "branch": "feat/phase-28"
  },
  "started_at": "2026-02-17T14:00:00Z",
  "completed_at": "2026-02-17T14:08:32Z",
  "duration_seconds": 512,
  "findings_summary": {
    "critical": 0,
    "high": 2,
    "medium": 5,
    "low": 12,
    "info": 8
  },
  "gate_status": "failed",
  "gate_reason": "2 HIGH severity findings exceed release threshold",
  "metadata": {
    "pentagi_version": "1.2.0",
    "tools_executed": ["bandit", "semgrep", "trivy", "gitleaks"],
    "container_id": "pentagi-abc123"
  }
}
```

### Response Schema: Findings

```json
{
  "findings": [
    {
      "finding_id": "finding-001",
      "severity": "high",
      "category": "dependency-vulnerability",
      "title": "Critical CVE in requests library",
      "description": "requests==2.28.0 contains CVE-2023-32681 (CVSS 9.1)",
      "affected_component": "requirements.txt:12",
      "remediation": "Upgrade requests to >=2.31.0",
      "cwe_id": "CWE-295",
      "cvss_score": 9.1,
      "tool_source": "trivy"
    }
  ],
  "total_count": 27,
  "filters_applied": {
    "min_severity": "medium"
  }
}
```

---

## Run States and Lifecycle

### State Diagram

```
pending → queued → running → completed
                          ↘ failed
                          ↘ timeout
                          ↘ cancelled
```

**State definitions**:
- **pending**: Run created, awaiting container launch
- **queued**: Waiting for PentAGI container resource availability
- **running**: Container executing security tests
- **completed**: Scan finished successfully, findings available
- **failed**: Container error or internal PentAGI failure
- **timeout**: Exceeded configured timeout threshold
- **cancelled**: Operator-initiated cancellation

**Status transitions**:
- Operators can cancel runs in `pending`, `queued`, or `running` states
- Completed/failed/timeout/cancelled runs are immutable (read-only)
- Findings are only available for `completed` runs

---

## Security Profiles

### Profile Definitions

| Profile | Target Use Case | Duration | Tools | Depth |
|---------|----------------|----------|-------|-------|
| **quick** | Pre-commit validation | <2 min | bandit, ruff, gitleaks | Surface-level SAST + secrets |
| **standard** | Pre-PR merge gate | 5-10 min | bandit, semgrep, trivy, gitleaks, safety | SAST + dependency + secrets |
| **deep** | Pre-release validation | 15-30 min | All tools + container scan + DAST | Full coverage including runtime analysis |

**Profile selection guidance**:
- **quick**: Developer inner loop; fast feedback on obvious issues
- **standard**: Default pre-deployment gate; balances speed and coverage
- **deep**: Release candidate validation; comprehensive security audit before production

### Tool Matrix

| Tool | Category | Quick | Standard | Deep |
|------|----------|-------|----------|------|
| bandit | Python SAST | ✓ | ✓ | ✓ |
| ruff | Python linting + security rules | ✓ | ✓ | ✓ |
| gitleaks | Secrets detection | ✓ | ✓ | ✓ |
| semgrep | Multi-language SAST | - | ✓ | ✓ |
| trivy | Dependency + container scan | - | ✓ | ✓ |
| safety | Python dependency CVE check | - | ✓ | ✓ |
| OWASP ZAP | DAST | - | - | ✓ |
| container-scan | Docker image analysis | - | - | ✓ |

---

## Findings Normalization Schema

### Severity Mapping

**Normalization rules** (map PentAGI/tool-specific severities to AGENT-33 model):

| Tool Severity | PentAGI Severity | AGENT-33 Severity |
|---------------|------------------|-------------------|
| CRITICAL, 9.0+ CVSS | critical | critical |
| HIGH, 7.0-8.9 CVSS | high | high |
| MEDIUM, 4.0-6.9 CVSS | medium | medium |
| LOW, 0.1-3.9 CVSS | low | low |
| INFO, 0.0 CVSS | info | info |

**Category taxonomy**:
- `dependency-vulnerability`: Known CVE in third-party package
- `secrets-exposure`: Hardcoded credential or API key detected
- `injection-risk`: SQL injection, command injection, XSS vulnerability
- `authentication-weakness`: Weak auth patterns or missing enforcement
- `authorization-bypass`: IDOR, privilege escalation, access control issues
- `cryptography-weakness`: Weak algorithms, insecure random, broken TLS
- `configuration-issue`: Insecure defaults, exposed debug endpoints
- `code-quality`: Potential bug or maintainability issue (low security impact)

**Deduplication strategy**:
- Hash finding by (file_path, line_number, rule_id, description)
- Suppress duplicate findings across multiple tools
- Preserve tool attribution in metadata for cross-validation

---

## Release Gate Policy Proposal

### Policy Model

```python
class SecurityGatePolicy:
    """Configurable security gate enforcement for release workflows."""
    
    require_recent_run: bool = True           # Must have run within N days
    max_run_age_days: int = 7                 # Stale run threshold
    
    block_on_critical: bool = True            # Always block on CRITICAL findings
    block_on_high: bool = True                # Block on HIGH findings by default
    max_allowed_high: int = 0                 # Allow N HIGH findings (0 = strict)
    
    block_on_medium: bool = False             # Don't block on MEDIUM by default
    max_allowed_medium: int = 10              # Warn threshold for MEDIUM findings
    
    require_profile: SecurityProfile = "standard"  # Minimum profile depth
    allow_override: bool = False              # Can operator override gate failure?
```

**Gate evaluation logic**:
1. Check if security run exists for target commit/branch
2. Verify run completed within `max_run_age_days`
3. Verify run used required profile or deeper
4. Count findings by severity tier
5. Apply blocking rules per severity tier
6. Return `gate_status` (passed/failed/warning) + `gate_reason`

**Example scenarios**:

| Findings | Policy | Gate Status | Reason |
|----------|--------|-------------|--------|
| 0C, 0H, 5M | Default | **passed** | No HIGH+ findings |
| 0C, 1H, 0M | Default | **failed** | 1 HIGH finding exceeds threshold (0) |
| 0C, 0H, 15M | Default | **warning** | 15 MEDIUM findings exceed warning (10) |
| 1C, 0H, 0M | Default | **failed** | 1 CRITICAL finding (always blocks) |

**Override mechanism**:
- If `allow_override=True`, operator can acknowledge gate failure with justification
- Override recorded in release metadata for audit trail
- Override requires elevated permission scope (e.g., `release:override`)

---

## Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| PentAGI container escapes sandbox | High | Low | Run containers with minimal privileges, no network access; enforce AppArmor/SELinux profiles |
| Malicious scan target injects code into PentAGI | High | Low | Mount target as read-only volume; validate target path against allowed workspace prefixes |
| Long-running scans block release pipeline | Medium | Medium | Enforce strict timeouts (default 10min); allow async run submission with polling |
| False positive findings block valid releases | Medium | High | Tune profile tool selection; allow finding suppression with justification; provide override path |
| PentAGI version drift breaks adapter | Medium | Low | Pin PentAGI container version; add version compatibility check at runtime |
| Findings storage grows unbounded | Low | Medium | Implement 90-day retention policy with archive/purge background task |
| Operator confusion about severity thresholds | Low | High | Provide clear release gate documentation; show gate policy in UI before run submission |

---

## Implementation Stages

### Stage 1: MVP (Backend + API)
**Target**: 1-2 weeks

**Deliverables**:
- [ ] Implement `PentAGIAdapter` service with Docker SDK integration
- [ ] Add `SecurityRun` and `SecurityFinding` models with SQLite persistence
- [ ] Create `/v1/component-security/runs` API routes (create, get, list, findings)
- [ ] Implement quick profile with bandit + gitleaks
- [ ] Add basic run status polling and findings parsing
- [ ] Write unit tests for adapter service and API routes

**Acceptance**:
- Operators can submit security run via API and retrieve findings JSON
- Quick profile completes in <2 minutes for AGENT-33 codebase
- Backend tests pass with >80% coverage for new code

### Stage 2: Hardening (Profiles + Gate)
**Target**: 1 week

**Deliverables**:
- [ ] Implement standard and deep profiles with full tool matrix
- [ ] Add `SecurityGatePolicy` model with configurable thresholds
- [ ] Wire security gate into Phase 19 release workflow
- [ ] Implement finding deduplication and normalization
- [ ] Add background cleanup task for expired runs
- [ ] Write integration tests for release gate enforcement

**Acceptance**:
- Standard profile executes 6+ tools and completes in <10 minutes
- Release workflow blocks deployment on HIGH findings per policy
- Gate policy is configurable via environment variables

### Stage 3: Scale (Frontend + Observability)
**Target**: 1 week

**Deliverables**:
- [ ] Build `SecurityRunForm`, `SecurityRunList`, `SecurityRunDetail` React components
- [ ] Add component-security domain operations to frontend
- [ ] Implement findings table with severity filtering and sorting
- [ ] Add release gate status display to existing release UI
- [ ] Wire real-time run status updates (polling or WebSocket)
- [ ] Document operator workflows and troubleshooting guidance

**Acceptance**:
- Operators can create, monitor, and review security runs from AGENT-33 UI
- Findings table renders 50+ findings without performance issues
- Frontend tests pass for all component-security workflows

---

## Validation Checklist

### Functional Validation
- [ ] Quick profile scan completes successfully on AGENT-33 codebase
- [ ] Standard profile scan detects known test vulnerabilities (seeded intentionally)
- [ ] Deep profile scan includes container image scanning
- [ ] PentAGI version is pinned and compatibility check passes for the configured image tag
- [ ] Run status transitions correctly through all lifecycle states
- [ ] Findings are normalized consistently across different tools
- [ ] Duplicate findings are suppressed across tool boundaries
- [ ] Release gate correctly blocks deployment on HIGH findings
- [ ] Release gate allows deployment when findings are below thresholds
- [ ] Operators can view findings detail including remediation guidance

### Security Validation
- [ ] PentAGI containers run with read-only target mounts
- [ ] PentAGI containers have no network access (unless DAST profile)
- [ ] PentAGI containers use non-root user inside container
- [ ] Operator cannot specify arbitrary container images (version pinned)
- [ ] API routes enforce `component-security:write` scope for run creation
- [ ] API routes enforce `component-security:read` scope for findings retrieval
- [ ] Findings do not expose sensitive data (secrets redacted in output)

### Performance Validation
- [ ] Quick profile completes in <2 minutes for typical repository size
- [ ] Standard profile completes in <10 minutes for typical repository size
- [ ] Deep profile completes in <30 minutes for typical repository size
- [ ] Findings retrieval returns <1000 findings in <2 seconds
- [ ] Backend can handle 5 concurrent security runs without resource exhaustion
- [ ] Frontend findings table renders smoothly with 100+ findings

### Documentation Validation
- [ ] `docs/walkthroughs.md` includes security run example with API curl commands
- [ ] `docs/research/phase28-pentagi-integration-analysis.md` captures design decisions
- [ ] `docs/progress/phase-28-pentagi-component-security-log.md` tracks validation evidence
- [ ] Inline code comments explain PentAGI adapter integration patterns
- [ ] Release gate policy configuration is documented with examples
- [ ] Troubleshooting guide covers common scan failures and remediations

---

## Open Questions and Decisions

### Resolved Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| PentAGI execution model | Local Docker container with volume mounts | Simplifies deployment; no remote orchestration dependency |
| Findings storage | SQLite with 90-day retention | Consistent with existing AGENT-33 persistence patterns |
| Severity model | 5-tier (critical/high/medium/low/info) | Standard industry practice; aligns with CVE CVSS |
| Release gate default | Block on HIGH+ findings | Conservative safety default; can be relaxed per team policy |
| Profile selection | 3 presets (quick/standard/deep) | Balance between simplicity and flexibility for operators |

### Open Questions

1. **PentAGI version pinning**: Should we pin to specific PentAGI version or track latest?
   - **Recommendation**: Pin to tested version; provide upgrade path in Phase 28.1
   
2. **Findings export**: Should findings be exportable as SARIF for CI integration?
   - **Recommendation**: Defer to post-MVP; focus on native UI first
   
3. **Multi-repository support**: Should single run scan multiple repos in monorepo setup?
   - **Recommendation**: Start with single-repo; extend in future iteration if needed
   
4. **Real-time status**: Polling vs WebSocket for run status updates?
   - **Recommendation**: Start with polling (5s interval); add WebSocket in Stage 3 if latency issues

5. **Finding remediation**: Should AGENT-33 attempt auto-remediation code generation?
   - **Recommendation**: Out of scope for Phase 28; defer to future research phase

---

## Success Criteria (Phase 28 MVP)

- [ ] Operators can create quick/standard/deep security test runs via API and UI
- [ ] Security runs execute in isolated PentAGI containers with <10min median latency
- [ ] Findings are normalized to AGENT-33 severity model with consistent categorization
- [ ] Release workflow enforces configurable security gate policy
- [ ] Security gate blocks deployment on CRITICAL/HIGH findings per default policy
- [ ] All Phase 28 backend tests pass (unit + integration)
- [ ] All Phase 28 frontend tests pass (component + integration)
- [ ] Documentation includes end-to-end examples and troubleshooting guidance
- [ ] Security review confirms sandbox isolation and access control enforcement

---

## References

- Phase 28 spec: `docs/phases/PHASE-28-PENTAGI-COMPONENT-SECURITY-TESTING-INTEGRATION.md`
- Phase 14 security patterns: `docs/phases/PHASE-14-SECURITY-HARDENING-AND-PROMPT-INJECTION-DEFENSE.md`
- Phase 19 release automation: `docs/phases/PHASE-19-RELEASE-AND-SYNC-AUTOMATION.md`
- Phase 22 UI platform: `docs/phases/PHASE-22-UNIFIED-UI-PLATFORM-AND-ACCESS-LAYER.md`
- PentAGI repository: https://github.com/vxcontrol/pentagi
- PentAGI documentation: https://github.com/vxcontrol/pentagi/blob/main/README.md
