# Hook Registry

This document defines the schema and registry of available hooks for AGENT-33 orchestration.

## Hook Definition Schema

```yaml
hook:
  id: string          # Unique identifier (HOOK-NNN format)
  name: string        # Human-readable name
  trigger: enum       # PreTask | PostTask | SessionStart | SessionEnd | PreCommit | PostVerify
  scope: enum         # task | session | commit | verification
  action: string      # Description of what the hook does
  evidence_capture:
    enabled: boolean  # Whether this hook produces evidence
    target: string    # Where evidence is recorded (e.g., verification-log.md)
    format: string    # Evidence format (text, json, structured)
  blocking: boolean   # Whether failure blocks execution
  severity: enum      # error | warning | info
  references:         # Related documents
    - path: string
      purpose: string
```

## Registered Hooks

### HOOK-001: PreTask Validation

```yaml
hook:
  id: HOOK-001
  name: PreTask Validation
  trigger: PreTask
  scope: task
  action: Verify task has acceptance criteria before execution begins
  evidence_capture:
    enabled: true
    target: core/orchestrator/handoff/TASKS.md
    format: structured
  blocking: true
  severity: error
  references:
    - path: core/orchestrator/OPERATOR_MANUAL.md
      purpose: Defines task acceptance criteria requirements
    - path: core/orchestrator/handoff/SPEC_FIRST_CHECKLIST.md
      purpose: Pre-implementation validation checklist
```

**Validation Rules**:
1. Task must have explicit acceptance criteria section
2. Acceptance criteria must be testable (not vague)
3. Task must have assigned owner
4. Branch name must be specified for code tasks

**Failure Response**: Block task execution, prompt for missing criteria.

---

### HOOK-002: PostTask Evidence Capture

```yaml
hook:
  id: HOOK-002
  name: PostTask Evidence Capture
  trigger: PostTask
  scope: task
  action: Auto-log commands and outcomes to verification log
  evidence_capture:
    enabled: true
    target: core/arch/verification-log.md
    format: structured
  blocking: false
  severity: warning
  references:
    - path: core/arch/verification-log.md
      purpose: Long-term evidence storage
    - path: core/orchestrator/handoff/EVIDENCE_CAPTURE.md
      purpose: Evidence capture specification
```

**Capture Rules**:
1. Record all commands executed during task
2. Capture command output (success or failure)
3. Link to task ID and session log
4. Timestamp all entries

**Failure Response**: Warn if evidence capture fails, allow task completion.

---

### HOOK-003: SessionStart Status Check

```yaml
hook:
  id: HOOK-003
  name: SessionStart Status Check
  trigger: SessionStart
  scope: session
  action: Verify STATUS.md is current before session begins
  evidence_capture:
    enabled: true
    target: core/orchestrator/handoff/STATUS.md
    format: text
  blocking: true
  severity: error
  references:
    - path: core/orchestrator/handoff/STATUS.md
      purpose: Current orchestration state
    - path: core/orchestrator/OPERATOR_MANUAL.md
      purpose: Session start procedure
```

**Validation Rules**:
1. STATUS.md exists and is readable
2. Last-updated timestamp is within 24 hours (or previous session)
3. Current phase matches expected state
4. No unresolved blockers marked as critical

**Failure Response**: Block session start, require STATUS.md update.

---

### HOOK-004: SessionEnd Handoff

```yaml
hook:
  id: HOOK-004
  name: SessionEnd Handoff
  trigger: SessionEnd
  scope: session
  action: Generate session wrap summary for next session
  evidence_capture:
    enabled: true
    target: core/arch/next-session.md
    format: structured
  blocking: false
  severity: info
  references:
    - path: core/arch/next-session.md
      purpose: Next session context
    - path: docs/session-logs/
      purpose: Session log archive
```

**Generation Rules**:
1. Summarize completed tasks with outcomes
2. List pending tasks with current state
3. Note any blockers or decisions needed
4. Reference session log location

**Failure Response**: Warn if summary incomplete, allow session end.

---

### HOOK-005: PreCommit Security Scan

```yaml
hook:
  id: HOOK-005
  name: PreCommit Security Scan
  trigger: PreCommit
  scope: commit
  action: Check for secrets and credentials before commit
  evidence_capture:
    enabled: true
    target: core/arch/verification-log.md
    format: structured
  blocking: true
  severity: error
  references:
    - path: core/orchestrator/SECURITY_HARDENING.md
      purpose: Security requirements
    - path: core/orchestrator/handoff/EVIDENCE_CAPTURE.md
      purpose: Security scan evidence
```

**Scan Rules**:
1. Check for API keys, tokens, passwords
2. Scan for private key patterns
3. Detect hardcoded credentials
4. Flag environment-specific paths

**Patterns Checked**:
- `(?i)(api[_-]?key|apikey)\s*[:=]\s*['"]?[a-zA-Z0-9]{16,}`
- `(?i)(password|passwd|pwd)\s*[:=]\s*['"]?[^\s'"]+`
- `(?i)(secret|token)\s*[:=]\s*['"]?[a-zA-Z0-9]{16,}`
- `-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----`

**Failure Response**: Block commit, report findings, require remediation.

---

### HOOK-006: PostVerify Log Update

```yaml
hook:
  id: HOOK-006
  name: PostVerify Log Update
  trigger: PostVerify
  scope: verification
  action: Update verification-log.md with verification results
  evidence_capture:
    enabled: true
    target: core/arch/verification-log.md
    format: structured
  blocking: false
  severity: info
  references:
    - path: core/arch/verification-log.md
      purpose: Verification evidence index
    - path: core/arch/REGRESSION_GATES.md
      purpose: Regression gate definitions
```

**Update Rules**:
1. Add entry to verification log index
2. Include date, cycle-id, branch, command, result
3. Link to session log and PR if applicable
4. Mark partial runs with explicit "not run (reason)"

**Failure Response**: Warn if update fails, log to session for manual follow-up.

---

## Hook Execution Order

When multiple hooks apply to the same trigger point, they execute in this order:

1. **Validation hooks** (blocking checks)
2. **Security hooks** (blocking scans)
3. **Evidence hooks** (non-blocking capture)
4. **Notification hooks** (non-blocking alerts)

## Adding New Hooks

1. Assign next available HOOK-NNN identifier
2. Define using the schema above
3. Add to this registry with full documentation
4. Update `core/workflows/hooks/README.md` if new trigger point
5. Create example in `core/workflows/hooks/examples/` if complex

## Related Documents

- `core/workflows/hooks/README.md` - Hooks system overview
- `core/orchestrator/OPERATOR_MANUAL.md` - Orchestration entrypoint
- `core/arch/verification-log.md` - Verification evidence log
