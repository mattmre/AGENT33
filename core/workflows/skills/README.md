# Skills Framework

Purpose: Define reusable workflow patterns and domain knowledge that agents can apply across tasks.

## What Are Skills?

Skills are structured workflow definitions and domain knowledge modules that:

- **Workflow Definitions**: Step-by-step processes for common development patterns (TDD, code review, refactoring)
- **Domain Knowledge**: Best practices, patterns, and heuristics for specific domains (security, testing, performance)
- **Integration Points**: Hooks into AGENT-33's orchestration, evidence capture, and verification systems

## How Skills Integrate with Orchestration

Skills operate within the AGENT-33 orchestration framework:

1. **Task Assignment**: Orchestrator assigns tasks that may reference one or more skills
2. **Skill Activation**: Agent loads relevant skill definitions for the task type
3. **Evidence Capture**: Each skill stage logs evidence per `EVIDENCE.md` requirements
4. **Verification**: Skill outputs feed into `verification-log.md` for audit trail
5. **Handoff**: Skill completion triggers handoff artifacts per `SESSION_WRAP.md`

### Skill-Orchestrator Contract

| Skill Phase | Orchestrator Action | Evidence Required |
|-------------|---------------------|-------------------|
| Start | Log skill activation in session | Skill name, task ID |
| Execute | Monitor progress, enforce autonomy budget | Commands, outputs |
| Complete | Verify acceptance criteria met | Pass/fail, artifacts |
| Handoff | Update task status, capture learnings | Session log entry |

## Available Skills

| Skill | File | Purpose |
|-------|------|---------|
| TDD Workflow | `tdd-workflow.md` | Test-driven development with RED/GREEN/REFACTOR stages |

## Creating New Skills

New skills should follow this structure:

```markdown
# Skill Name

## Purpose
Brief description of what the skill accomplishes.

## Stages
Ordered list of stages with clear entry/exit criteria.

## Evidence Requirements
What evidence must be captured at each stage.

## Integration Points
References to AGENT-33 orchestration documents.

## Examples
Concrete examples of skill application.
```

## Cross-References

- Evidence requirements: `core/packs/policy-pack-v1/EVIDENCE.md`
- Verification logging: `core/arch/verification-log.md`
- Test selection: `core/arch/test-matrix.md`
- Session handoff: `core/orchestrator/handoff/SESSION_WRAP.md`
- Autonomy constraints: `core/orchestrator/handoff/AUTONOMY_BUDGET.md`
