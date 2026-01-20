# Skills Index

Purpose: Central index of all available skills for workflow automation.

Related docs:
- `core/workflows/commands/COMMAND_REGISTRY.md` (commands that invoke skills)
- `core/ORCHESTRATION_INDEX.md` (main orchestration index)

---

## Available Skills

| Skill | Purpose | Invoked By |
|-------|---------|------------|
| security-review | Comprehensive security checklist | Manual, pre-merge hooks |
| coding-standards | Coding standards and best practices | /refactor command |
| backend-patterns | Backend development patterns | Manual |
| tdd-workflow | Test-Driven Development workflow | /tdd command |

---

## Skill Index

### Security & Quality

- **[security-review](./security-review.md)** - Security review checklist
  - Input validation patterns
  - Authentication/authorization checks
  - Common vulnerability patterns (injection, XSS, CSRF)
  - Secrets management

- **[coding-standards](./coding-standards.md)** - Coding standards skill
  - File organization principles
  - Naming conventions
  - Error handling patterns
  - Code review checklist

### Development Patterns

- **[backend-patterns](./backend-patterns.md)** - Backend patterns skill
  - API design patterns (REST, error responses)
  - Database access patterns (repository pattern)
  - Caching strategies
  - Authentication patterns

### Workflows

- **[tdd-workflow](./tdd-workflow.md)** - TDD workflow skill
  - RED/GREEN/REFACTOR cycle
  - Evidence capture per stage

---

## Skill Conventions

### Signature Format
```
invoke: <skill-name>
inputs: <comma-separated inputs>
outputs: <comma-separated outputs>
```

### Integration with Evidence
All skills should integrate with evidence capture:
1. Document scope of skill application
2. Capture results/findings
3. Note compliance status

---

## Adding New Skills

1. Create `<skill-name>.md` in this directory
2. Follow existing skill template structure
3. Add entry to this README
4. Update ORCHESTRATION_INDEX.md if applicable

### Skill Template Structure

```markdown
# <skill-name> Skill

Purpose: <one-line description>

Related docs:
- <related-file-1>
- <related-file-2>

---

## Skill Signature
## Checklist/Patterns
## Evidence Capture
```
