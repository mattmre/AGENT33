# Competitive Analysis: everything-claude-code

**Date**: 2026-01-20  
**Repository**: https://github.com/anthropics/claude-code (reference implementation)
**Analyst**: Automated Competitive Analysis  
**Status**: Complete

---

## Executive Summary

The `everything-claude-code` repository is a comprehensive collection of production-ready Claude Code configurations developed over 10+ months of intensive use. It won the Anthropic x Forum Ventures hackathon (Sep 2025) and represents a mature, battle-tested approach to AI-assisted development.

The repository focuses on **individual developer productivity** with an emphasis on execution-time automation through hooks, slash commands, and specialized agents. In contrast, AGENT-33 focuses on **cross-repository orchestration governance** with emphasis on evidence capture, multi-agent coordination, and session-spanning workflows.

**Key Insight**: These repositories are complementary rather than competitive. AGENT-33 provides the governance layer and orchestration backbone, while everything-claude-code offers concrete execution-level configurations that could be incorporated as "packs" within AGENT-33's framework.

---

## Repository Overview

### Purpose
A curated collection of Claude Code configurations for daily development work, including:
- Specialized subagents for specific tasks
- Workflow definitions (skills) for common patterns
- Slash commands for quick execution
- Automation hooks for tool events
- MCP server configurations

### Structure

```
everything-claude-code/
├── agents/           # 9 specialized subagent definitions
├── commands/         # 9 slash commands
├── examples/         # Sample CLAUDE.md files
├── hooks/            # Event-driven automation (PreToolUse, PostToolUse, Stop)
├── mcp-configs/      # MCP server configurations
├── plugins/          # Plugin ecosystem guide
├── rules/            # 8 modular rule files
└── skills/           # Workflow definitions + domain knowledge
```

### Philosophy
1. **Modular Configuration**: Small, focused files over monolithic configs
2. **Agent Delegation**: Specialized agents for complex tasks
3. **Parallel Execution**: Multiple agents working simultaneously
4. **Plan Before Execute**: Explicit planning phase with user confirmation
5. **Test-Driven**: Comprehensive testing as first-class citizen
6. **Security-First**: Mandatory security checks before commits

---

## Feature Inventory

### Agents (9 Specialized Subagents)

| Agent | Purpose | Model | Tools |
|-------|---------|-------|-------|
| planner.md | Implementation planning | opus | Read, Grep, Glob |
| architect.md | System design & architecture | opus | Read, Grep, Glob |
| tdd-guide.md | Test-driven development | - | - |
| code-reviewer.md | Quality & security review | opus | Read, Grep, Glob, Bash |
| security-reviewer.md | Vulnerability analysis | opus | Read, Grep, Glob |
| build-error-resolver.md | Fix build/test failures | - | Bash |
| e2e-runner.md | Playwright E2E testing | - | Bash |
| refactor-cleaner.md | Dead code cleanup | - | Read, Grep, Glob |
| doc-updater.md | Documentation sync | - | Read, Write |

### Commands (9 Slash Commands)

| Command | Purpose |
|---------|---------|
| /tdd | Test-driven development workflow |
| /plan | Create implementation plan (requires confirmation) |
| /e2e | Generate E2E tests |
| /code-review | Quality and security review |
| /build-fix | Fix build errors |
| /refactor-clean | Remove dead code |
| /test-coverage | Coverage analysis |
| /update-codemaps | Refresh documentation |
| /update-docs | Sync documentation |

### Rules (8 Modular Rule Files)

| Rule | Focus |
|------|-------|
| security.md | No secrets, input validation, parameterized queries |
| coding-style.md | Immutability, file organization, max 800 lines |
| testing.md | TDD, 80% coverage minimum |
| git-workflow.md | Conventional commits, PR process |
| agents.md | When to delegate to subagents |
| patterns.md | API response formats, hooks |
| performance.md | Model selection, context management |
| hooks.md | Hook documentation |

### Hooks (Event-Driven Automation)

| Hook Type | Trigger | Examples |
|-----------|---------|----------|
| PreToolUse | Before tool execution | Block dev servers outside tmux; pause before git push |
| PostToolUse | After tool execution | Auto-format with Prettier; TypeScript check; console.log warnings |
| Stop | Session end | Audit for console.log in modified files |

**Notable Hook Capabilities**:
- Block creation of arbitrary .md files (enforce consolidated docs)
- Auto-run Prettier after JS/TS edits
- TypeScript checks after .ts/.tsx edits
- PR creation logging with review commands
- Final console.log audit before session ends

### Skills (Workflow Definitions)

| Skill | Purpose |
|-------|---------|
| tdd-workflow/ | Comprehensive TDD methodology with patterns |
| security-review/ | Security checklist and validation |
| coding-standards.md | Language best practices |
| backend-patterns.md | API, database, caching patterns |
| frontend-patterns.md | React, Next.js patterns |
| project-guidelines-example.md | Example project-specific skill |
| clickhouse-io.md | ClickHouse analytics patterns |

### MCP Configurations
- GitHub integration
- Supabase
- Vercel
- Railway
- Various development tools

### Plugin Ecosystem
- Marketplace integration (Anthropic official, community)
- Recommended plugins for development, code quality, search, workflow
- Installation and management guidance

---

## Comparative Analysis

### Structural Comparison

| Aspect | everything-claude-code | AGENT-33 |
|--------|------------------------|----------|
| **Focus** | Individual developer productivity | Cross-repo orchestration governance |
| **Scope** | Single-session execution | Multi-session, multi-repo coordination |
| **Model** | Claude Code specific | Model-agnostic |
| **Agents** | 9 specialized execution agents | 10 governance-focused roles |
| **Orchestration** | Implicit (user-driven) | Explicit (Director → Orchestrator → Worker) |
| **Evidence** | Minimal (hooks capture some) | Comprehensive (commands, outcomes, artifacts) |
| **Session Continuity** | Limited (user-level CLAUDE.md) | Built-in (handoff protocols, status docs) |
| **Testing** | TDD workflow emphasis | Verification evidence emphasis |
| **Automation** | Hooks (PreToolUse, PostToolUse, Stop) | None (manual workflows) |

### Agent Comparison

| everything-claude-code | AGENT-33 Equivalent | Gap |
|------------------------|---------------------|-----|
| planner | AGT-001 Orchestrator (P-01, P-02) | Similar capability |
| architect | AGT-009 Architect | Similar capability |
| code-reviewer | AGT-005 Reviewer (R-01) | Similar capability |
| security-reviewer | AGT-008 Security | Similar capability |
| tdd-guide | AGT-010 Test Engineer | More detailed workflow |
| build-error-resolver | AGT-003 Implementer | More specific focus |
| e2e-runner | AGT-004 QA (V-01) | More specific focus |
| refactor-cleaner | AGT-003 Implementer (I-05) | More specific focus |
| doc-updater | AGT-007 Documentation | Similar capability |

### Workflow Comparison

| Workflow Aspect | everything-claude-code | AGENT-33 |
|-----------------|------------------------|----------|
| **Planning** | /plan command with confirmation wait | PLAN.md + acceptance criteria |
| **Implementation** | /tdd workflow | TASKS.md queue + minimal diffs |
| **Review** | /code-review command | TWO_LAYER_REVIEW.md + risk triggers |
| **Verification** | Test coverage requirements | Verification log with evidence |
| **Documentation** | /update-docs command | Session wrap context capture |

### Automation Comparison

| Automation | everything-claude-code | AGENT-33 |
|------------|------------------------|----------|
| **Pre-execution checks** | Hooks (PreToolUse) | Manual (AUTONOMY_ENFORCEMENT.md) |
| **Post-execution actions** | Hooks (PostToolUse) | Manual evidence capture |
| **Session end** | Hooks (Stop) | SESSION_WRAP.md manual checklist |
| **Auto-formatting** | Prettier hook | None |
| **Type checking** | TypeScript hook | None |
| **Security gates** | Security hook warnings | RISK_TRIGGERS.md manual |

---

## Gap Analysis

### Features AGENT-33 Lacks

#### 1. **Hooks System** (HIGH PRIORITY)
AGENT-33 has no automated hooks for tool events. Benefits if added:
- Auto-capture evidence after command execution
- Enforce security checks before commits
- Auto-update STATUS.md on session stop
- Validate diffs against acceptance criteria

#### 2. **Slash Commands** (MEDIUM PRIORITY)
AGENT-33 relies on navigating documentation. Benefits if added:
- Quick access to workflows: /plan, /review, /verify
- Consistent entry points for common operations
- Reduced onboarding friction

#### 3. **Modular Rule Files** (MEDIUM PRIORITY)
AGENT-33 has policy-pack-v1 but less granular. Benefits if improved:
- Easier customization per project
- Clearer separation of concerns
- Simpler inheritance and override

#### 4. **TDD-Specific Workflow** (LOW-MEDIUM PRIORITY)
AGENT-33 has verification emphasis but no structured TDD. Benefits if added:
- Explicit RED-GREEN-REFACTOR cycle
- Coverage requirements built into workflow
- Test patterns library

#### 5. **Specific Agent Personas** (LOW PRIORITY)
AGENT-33 has roles but less detailed personas. Everything-claude-code agents have:
- Detailed prompts with examples
- Model recommendations
- Tool restrictions per agent

### Features everything-claude-code Lacks

#### 1. **Cross-Session Continuity** (PRESENT IN AGENT-33)
- No handoff protocols
- No STATUS.md/PLAN.md/TASKS.md structure
- Relies on user-level CLAUDE.md only

#### 2. **Multi-Agent Coordination** (PRESENT IN AGENT-33)
- No explicit orchestration hierarchy
- No routing maps
- No conflict resolution

#### 3. **Evidence Capture** (PRESENT IN AGENT-33)
- Minimal evidence requirements
- No verification logs
- No audit trail

#### 4. **Cross-Repository Governance** (PRESENT IN AGENT-33)
- Single-repo focus
- No ingest/normalize/distribute pattern
- No deduplication strategy

#### 5. **Formal Workflow Specification** (PRESENT IN AGENT-33)
- No ARCH-AEP equivalent
- No tier-based remediation
- No scope locking

---

## Recommendations

### HIGH PRIORITY

#### R-01: Implement Hooks System
**Action**: Create a hooks specification for AGENT-33
- Define hook points: PreTask, PostTask, SessionStart, SessionEnd
- Integrate with evidence capture
- Auto-update handoff documents

**Effort**: Medium  
**Impact**: High (automation reduces manual overhead)

#### R-02: Create Slash Command Registry
**Action**: Define standard commands for AGENT-33 workflows
- /status - Review current STATUS.md
- /tasks - List open tasks from TASKS.md
- /verify - Capture verification evidence
- /handoff - Generate session wrap summary

**Effort**: Low  
**Impact**: Medium (improved UX)

### MEDIUM PRIORITY

#### R-03: Adopt TDD Workflow Skill
**Action**: Adapt everything-claude-code's TDD skill for AGENT-33
- Integrate with verification log
- Add evidence capture at each TDD stage
- Link coverage to acceptance criteria

**Effort**: Low  
**Impact**: Medium (structured testing)

#### R-04: Modularize Policy Pack
**Action**: Split policy-pack-v1 into granular rule files
- security.md
- evidence.md
- orchestration.md
- testing.md
- git-workflow.md

**Effort**: Low  
**Impact**: Medium (easier customization)

### LOW PRIORITY

#### R-05: Agent Persona Enhancement
**Action**: Add detailed prompts to AGENT_REGISTRY entries
- Include example outputs
- Add model recommendations
- Define tool restrictions

**Effort**: Medium  
**Impact**: Low (already functional)

#### R-06: Plugin/Marketplace Guidance
**Action**: Document recommended plugins for AGENT-33 workflows
- Search enhancement
- Type checking
- Code quality

**Effort**: Low  
**Impact**: Low (optional enhancement)

---

## Integration Opportunities

### Direct Adoption Candidates

| Asset | Source | Target | Notes |
|-------|--------|--------|-------|
| TDD Workflow | skills/tdd-workflow/SKILL.md | core/workflows/skills/ | Adapt evidence capture |
| Security Rules | rules/security.md | core/packs/policy-pack-v1/ | Merge with existing |
| Coding Standards | skills/coding-standards.md | core/workflows/skills/ | Adapt to model-agnostic |
| Planner Agent | agents/planner.md | core/orchestrator/prompts/ | Reference for enhancement |
| Architect Agent | agents/architect.md | core/orchestrator/agents/ | Reference for enhancement |
| Hooks Examples | hooks/hooks.json | core/workflows/hooks/ | New capability |

### Adaptation Required

| Asset | Adaptation Needed |
|-------|-------------------|
| MCP Configs | Remove Claude-specific; document as optional |
| Commands | Translate to AGENT-33 workflow entry points |
| Frontend/Backend Patterns | Make model-agnostic; add to skills library |

### Not Applicable

| Asset | Reason |
|-------|--------|
| Plugin marketplace | Claude Code specific |
| statusline.json | Editor-specific |
| user-CLAUDE.md | User-level Claude config |

---

## Backlog Items Generated

| ID | Title | Priority | Source |
|----|-------|----------|--------|
| CA-001 | Design hooks system specification | High | R-01 |
| CA-002 | Create slash command registry | Medium | R-02 |
| CA-003 | Adapt TDD workflow skill | Medium | R-03 |
| CA-004 | Modularize policy-pack-v1 | Medium | R-04 |
| CA-005 | Enhance agent personas | Low | R-05 |
| CA-006 | Document plugin recommendations | Low | R-06 |

---

## Summary Matrix

| Category | everything-claude-code | AGENT-33 | Winner |
|----------|------------------------|----------|--------|
| Developer UX | ★★★★★ | ★★★☆☆ | everything-claude-code |
| Automation | ★★★★☆ | ★★☆☆☆ | everything-claude-code |
| Session Continuity | ★★☆☆☆ | ★★★★★ | AGENT-33 |
| Cross-Repo Governance | ★☆☆☆☆ | ★★★★★ | AGENT-33 |
| Evidence Capture | ★★☆☆☆ | ★★★★★ | AGENT-33 |
| Multi-Agent Coordination | ★★☆☆☆ | ★★★★★ | AGENT-33 |
| Testing Workflow | ★★★★★ | ★★★☆☆ | everything-claude-code |
| Documentation | ★★★★☆ | ★★★★☆ | Tie |
| Model Agnostic | ★☆☆☆☆ | ★★★★★ | AGENT-33 |
| Production Ready | ★★★★★ | ★★★☆☆ | everything-claude-code |

---

## Conclusion

AGENT-33 and everything-claude-code serve different but complementary purposes:

- **everything-claude-code**: Best for individual developer productivity within Claude Code sessions. Provides excellent execution-level automation and structured workflows.

- **AGENT-33**: Best for organizational governance, cross-repository coordination, and session-spanning orchestration. Provides audit trails, evidence capture, and model-agnostic guidance.

**Strategic Recommendation**: Integrate everything-claude-code's execution-level assets (TDD workflow, security rules, hooks patterns) into AGENT-33 as a "Claude Code Execution Pack" while maintaining AGENT-33's governance and orchestration backbone.

---

## References

- Source Repository: (public GitHub repository)
- Commit Analyzed: (redacted)

- AGENT-33 Documentation: core/INDEX.md, core/ORCHESTRATION_INDEX.md
