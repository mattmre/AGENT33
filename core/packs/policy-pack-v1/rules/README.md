# Modular Rules Index

Purpose: Provide a modular, customizable rule set for agent behavior governance.

## Overview

Rules in this directory define specific behavioral constraints and requirements for agents operating under Policy Pack v1. Each rule file focuses on a single domain, enabling:

- **Selective adoption**: Projects can adopt rules incrementally
- **Easy customization**: Override or extend rules per project needs
- **Clear ownership**: Each domain has defined scope and maintainer
- **Audit trail**: Changes to rules are tracked and versioned

## Rule Files

| File | Domain | Description |
|------|--------|-------------|
| `security.md` | Security | Secrets handling, input validation, injection prevention |
| `testing.md` | Testing | TDD workflow, coverage requirements, verification evidence |
| `git-workflow.md` | Git | Commits, branches, PRs, reviews |
| `coding-style.md` | Code Style | File organization, immutability, documentation |

## How Rules Apply

### Default Behavior

All rules in this directory apply by default when Policy Pack v1 is active. Agents should:

1. Load all rule files at session start
2. Apply rules throughout task execution
3. Document any rule deviations with rationale

### Per-Project Customization

Projects can customize rules by:

1. **Override file**: Create `.agent-33/rules-override.md` in project root
2. **Selective disable**: List rules to skip with justification
3. **Extensions**: Add project-specific rules that augment defaults

Example override file:
```markdown
# Rules Override

## Disabled Rules
- `coding-style.md#3-file-size-limits` - Legacy codebase with large files

## Extended Rules
- Require TypeScript strict mode for all new files
```

### Rule Precedence

1. Project-specific overrides (highest)
2. Policy Pack rules (this directory)
3. AGENT-33 core principles (lowest, always apply)

## Rule Structure

Each rule file follows this structure:

```markdown
# [Domain] Rules

## Purpose
Why these rules exist.

## Rules
Numbered list of specific rules.

## Enforcement
How agents should enforce these rules.

## Exceptions
Valid reasons to deviate (with documentation requirements).

## Cross-References
Links to related AGENT-33 documents.
```

## Adding New Rules

1. Create new `.md` file in this directory
2. Follow the rule structure template above
3. Update this index with the new rule file
4. Document in `AGENTS.md` reference section

## Cross-References

- Parent policy: `core/packs/policy-pack-v1/AGENTS.md`
- Evidence requirements: `core/packs/policy-pack-v1/EVIDENCE.md`
- Risk triggers: `core/packs/policy-pack-v1/RISK_TRIGGERS.md`
- Acceptance checks: `core/packs/policy-pack-v1/ACCEPTANCE_CHECKS.md`
