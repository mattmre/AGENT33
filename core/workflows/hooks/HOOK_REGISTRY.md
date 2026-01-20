# Hook Registry

Purpose: Central registry of available hooks for workflow automation.

Related docs:
- `core/packs/policy-pack-v1/ORCHESTRATION.md` (workflow protocol)
- `core/ORCHESTRATION_INDEX.md` (main orchestration index)

---

## Available Hooks

| Hook | Trigger | Purpose | Blocking |
|------|---------|---------|----------|
| pre-commit-security | pre-commit | Scan for secrets/sensitive data | Yes |
| session-end-handoff | session-end | Auto-generate handoff docs | No |
| scope-validation | pre-commit | Validate changes against scope | No |

---

## Hook Index

### Pre-Commit Hooks

- **[pre-commit-security-hook](./examples/pre-commit-security-hook.md)**
  - Trigger: pre-commit
  - Purpose: Check for hardcoded secrets, validate no sensitive files staged
  - Blocking: Yes (on critical/high findings)

- **[scope-validation-hook](./examples/scope-validation-hook.md)**
  - Trigger: pre-commit
  - Purpose: Validate changes against PLAN.md scope
  - Blocking: No (warning only)

### Session Hooks

- **[session-end-handoff-hook](./examples/session-end-handoff-hook.md)**
  - Trigger: session-end
  - Purpose: Auto-generate SESSION_WRAP summary
  - Blocking: No

---

## Hook Configuration Schema

```yaml
hook:
  name: string          # Unique identifier
  trigger: enum         # pre-commit, post-commit, session-start, session-end
  scope: enum           # staged-files, workspace, all
  blocking: boolean     # Block action on findings
  severity-threshold: enum  # critical, high, medium, low (for blocking)
  auto-commit: boolean  # Auto-commit generated files
```

---

## Trigger Types

| Trigger | When Fired | Common Uses |
|---------|------------|-------------|
| pre-commit | Before commit is created | Validation, security scans |
| post-commit | After commit is created | Notifications, logging |
| session-start | When agent session begins | Context loading, state restore |
| session-end | When agent session ends | Handoff docs, state save |

---

## Hook Execution Order

When multiple hooks share a trigger:
1. Blocking hooks run first
2. Non-blocking hooks run after
3. Within category: alphabetical order
4. Any blocking hook failure stops chain

---

## Adding New Hooks

1. Create `<hook-name>.md` in `examples/` directory
2. Include hook configuration YAML
3. Document checks performed
4. Provide pseudo-code implementation
5. Add entry to this registry

### Hook Template Structure

```markdown
# <hook-name>

Purpose: <one-line description>

Related docs:
- <related-file-1>
- <related-file-2>

---

## Hook Configuration
## Checks Performed
## Pseudo-code Implementation
## Output Format
## Integration Notes
```

---

## Evidence Capture

Document hook executions:
```markdown
## Hook Execution Evidence

### Hook: <hook-name>
### Trigger: <trigger-type>
### Timestamp: <datetime>

### Result
- Status: PASS / FAIL / WARN
- Findings: X critical, Y high, Z medium
- Action: ALLOWED / BLOCKED

### Findings Detail
- <finding-1>
- <finding-2>
```
