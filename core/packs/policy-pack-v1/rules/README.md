# Rules Index

Purpose: Central index of policy rules for agent operation.

Related docs:
- `core/packs/policy-pack-v1/AGENTS.md` (agent principles)
- `core/packs/policy-pack-v1/ORCHESTRATION.md` (workflow protocol)
- `core/ORCHESTRATION_INDEX.md` (main orchestration index)

---

## Available Rules

| Rule | Purpose | Applies To |
|------|---------|------------|
| agents | Agent delegation and coordination | Multi-agent workflows |
| patterns | Common code and API patterns | All implementation |
| performance | Efficiency and context management | All agents |

---

## Rule Index

### Agent Operations

- **[agents](./agents.md)** - Agent delegation rules
  - When to delegate to subagents
  - Agent selection criteria
  - Parallel execution guidelines
  - Escalation patterns

### Code Standards

- **[patterns](./patterns.md)** - Common patterns rules
  - API response format standards
  - Error handling conventions
  - Logging patterns
  - Configuration management

### Efficiency

- **[performance](./performance.md)** - Performance rules
  - Context management (keep focused)
  - Efficient tool usage
  - Avoid redundant operations
  - Scope creep prevention

---

## Rule Application

### Hierarchy
1. **Policy Pack rules** (this directory) - baseline
2. **Project-specific overrides** - in project root
3. **Task-specific constraints** - in TASKS.md

### Enforcement
- Rules are guidance, not hard blocks
- Document deviations with rationale
- Escalate if rule conflicts with task

---

## Adding New Rules

1. Create `<rule-name>.md` in this directory
2. Follow existing rule template structure
3. Add entry to this README
4. Update ORCHESTRATION_INDEX.md if applicable

### Rule Template Structure

```markdown
# <rule-name>.md (Rules)

Purpose: <one-line description>

Related docs:
- <related-file-1>
- <related-file-2>

---

## <Section 1>
## <Section 2>
## Evidence Capture
```
