# Command Registry

Purpose: Central registry of all available slash commands.

Related docs:
- `core/orchestrator/OPERATOR_MANUAL.md` (operator usage guide)
- `core/packs/policy-pack-v1/ORCHESTRATION.md` (workflow protocol)

---

## Available Commands

| Command | Purpose | Skill Invoked |
|---------|---------|---------------|
| `/tdd` | Test-Driven Development workflow | tdd-workflow |
| `/build-fix` | Fix build or test failures | - |
| `/docs` | Sync documentation with code | - |
| `/e2e` | Generate or run E2E tests | - |
| `/refactor` | Clean up dead code or refactor | coding-standards |

---

## Command Index

### Development Commands

- **[/tdd](./tdd.md)** - Direct entry point for TDD workflow
  - Invoke TDD skill, track RED/GREEN/REFACTOR stages
  - Outputs: Tests, implementation, evidence

- **[/build-fix](./build-fix.md)** - Fix build or test failures
  - Analyze error output, identify root cause, apply minimal fix
  - Outputs: Fixed code, verification evidence

- **[/refactor](./refactor.md)** - Code cleanup and refactoring
  - Identify candidates, verify no behavior change
  - Outputs: Refactored code, test verification

### Testing Commands

- **[/e2e](./e2e.md)** - End-to-end testing
  - Identify critical flows, create scenarios, capture evidence
  - Outputs: E2E test files, execution results

### Documentation Commands

- **[/docs](./docs.md)** - Documentation synchronization
  - Identify affected docs, update content, verify links
  - Outputs: Updated docs, link verification

---

## Command Conventions

### Invocation
```
/<command> [required-args] [optional-args]
```

### Standard Outputs
All commands should produce:
1. Primary artifacts (code, docs, tests)
2. Evidence of execution
3. TASKS.md update

### Error Handling
- Commands should fail gracefully with clear messages
- Partial progress should be captured in STATUS.md
- Escalation path should be clear

---

## Adding New Commands

1. Create `<command-name>.md` in this directory
2. Follow existing command template structure
3. Add entry to this registry
4. Update ORCHESTRATION_INDEX.md

### Command Template Structure

```markdown
# /<command-name> Command

Purpose: <one-line description>

Related docs:
- <related-file-1>
- <related-file-2>

---

## Command Signature
## Workflow
## Inputs
## Outputs
## Evidence Capture
## Example Usage
```
