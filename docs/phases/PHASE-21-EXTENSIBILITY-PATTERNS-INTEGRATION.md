# Phase 21: Extensibility Patterns Integration (Memorizer-v1 Adaptations)

## Overview
- **Phase**: 21 of 21+
- **Category**: Research / Core Enhancement
- **Release Target**: TBD
- **Estimated Sprints**: 2-3
- **Source Research**: `docs/research/repo_dossiers/memorizer__petabridge__memorizer-v1.md`

## Objectives
- Integrate extensibility patterns from memorizer-v1 competitive research.
- Enhance AGENT-33 core with relationship typing, versioning concepts, and autonomous agent protocols.
- Keep focus on documentation-native patterns (no database/service dependencies).

## Scope Outline

### In Scope
1. **Relationship Typing System** - Add typed relationships between artifacts
2. **Preserve-Original-During-Refinement** - Establish immutable collected → refined workflow
3. **Autonomous Agent Memory Protocol** - Create AGENT.md-style briefing for agent autonomy
4. **Lightweight Artifact References** - Index artifacts with metadata for efficient retrieval
5. **Event-Based Change Tracking** - Typed change events for document versioning

### Out of Scope
- Database storage (PostgreSQL/pgvector)
- MCP server endpoints
- Actor-based async processing
- Embedding generation
- Web UI components

---

## Deliverables

### Tier 1: Core Patterns (Priority 1-2)

#### 1.1 Relationship Typing System
**File**: `core/orchestrator/RELATIONSHIP_TYPES.md`

Define semantic relationship primitives for connecting AGENT-33 artifacts:

| Relationship | Meaning | Example |
|--------------|---------|---------|
| `depends-on` | Phase → prerequisite phases | Phase-05 depends-on Phase-03 |
| `derived-from` | Artifact → source template | canonical-doc derived-from collected/source.md |
| `supersedes` | Updated artifact → deprecated version | CLAUDE-v2.md supersedes CLAUDE-v1.md |
| `exemplifies` | Concrete example → abstract pattern | tdd-workflow.md exemplifies workflow-template.md |
| `contextualizes` | Research → feature being designed | memorizer-dossier contextualizes Phase-21 |
| `explains` | Documentation → concept | GLOSSARY.md explains orchestrator-role |
| `chunk-of` | Section → parent document | For large document decomposition |

**Acceptance Criteria**:
- [x] Relationship types documented with examples
- [x] Usage guidance added to `core/arch/templates.md`
- [x] CHANGELOG updated

#### 1.2 Preserve-Original-During-Refinement Policy
**Files**: 
- Update `dedup-policy.md`
- Update `sync-plan.md`

Formalize the rule that originals in `collected/` are never modified:
- All refinements create new artifacts with `supersedes` relationships
- Provenance chain maintained from collected → core → distributed

**Acceptance Criteria**:
- [x] Policy explicitly states immutability of collected/
- [x] Relationship links documented in canonicalization workflow
- [x] CHANGELOG updated

---

### Tier 2: Agent Protocol (Priority 3)

#### 2.1 Autonomous Agent Memory Protocol
**File**: `core/agents/AGENT_MEMORY_PROTOCOL.md`

Create AGENT.md-style briefing instructing agents on knowledge management:

```markdown
## Agent Memory Protocol

1. **Search before acting** - At session start, query relevant artifacts
2. **Store reusable knowledge** - Persist insights in agent-learning.md
3. **Relate what you find** - Add relationships between discovered artifacts
4. **Retire obsolete entries** - Mark deprecated items with supersedes links
5. **Never ask permission** for routine memory operations
```

**Acceptance Criteria**:
- [x] Protocol document created
- [x] Linked from ORCHESTRATION_INDEX.md
- [x] Integrated with policy-pack-v1/AGENTS.md
- [x] CHANGELOG updated

---

### Tier 3: Artifact Indexing (Priority 4)

#### 3.1 Lightweight Artifact Index
**File**: `core/ARTIFACT_INDEX.md`

Create metadata index for efficient artifact discovery:

| artifact-id | title | type | tags | created | supersedes |
|-------------|-------|------|------|---------|------------|
| prompt-pack-v1 | Policy Pack v1 | pack | governance, agents | 2026-01-16 | - |
| phase-21 | Extensibility Integration | phase | research, core | 2026-01-20 | - |

**Acceptance Criteria**:
- [x] Index format documented
- [x] Initial population with core artifacts
- [x] Search/filter guidance added
- [x] CHANGELOG updated

---

### Tier 4: Change Tracking (Priority 5)

#### 4.1 Typed Change Events
**File**: `core/arch/CHANGE_EVENT_TYPES.md`

Define event types for document versioning (inspired by MemoryEvent pattern):

| Event Type | Description | Display Text Example |
|------------|-------------|---------------------|
| `artifact_created` | New artifact added | "Created prompt-pack-v1" |
| `content_updated` | Content modified | "+15 -3 lines changed" |
| `metadata_updated` | Tags/title changed | "Updated tags: +governance" |
| `relationship_added` | Link created | "Added depends-on → Phase-03" |
| `artifact_superseded` | Replaced by newer | "Superseded by prompt-pack-v2" |
| `artifact_reverted` | Rollback | "Reverted to v2" |

**Acceptance Criteria**:
- [x] Event types documented
- [x] Integration with CHANGELOG.md format
- [x] Human-readable display text convention
- [x] CHANGELOG updated

---

### Tier 5: Similarity Discovery (Priority 6 - Deferred)

#### 5.1 Artifact Similarity Discovery
**Status**: Deferred to future phase

When artifact count warrants it:
- Add similarity scoring guidance
- Document cross-linking discovery workflow
- Consider tooling integration

---

## Dependencies
- Phase 20 (Continuous Improvement)
- Phase 02 (Canonical Core Architecture)

## Blocks
- None

## Orchestration Guidance
- Research agent validates patterns against current AGENT-33 structure
- Documentation agent creates new artifacts
- Orchestrator reviews for consistency with existing conventions
- Reviewer validates no service/database dependencies introduced

## Coding Direction
- All deliverables are documentation-only (Markdown)
- Prefer structured templates over narrative
- Use existing AGENT-33 conventions for file naming and location
- Keep artifacts composable and model-agnostic

## Review Checklist
- [x] Patterns adapted correctly from memorizer-v1 research
- [x] No service/database dependencies introduced
- [x] Consistent with existing AGENT-33 conventions
- [x] Documentation clear and actionable
- [x] CHANGELOG entries complete
- [x] ORCHESTRATION_INDEX.md updated with new links

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Over-engineering documentation patterns | Medium | Keep initial implementation minimal |
| Inconsistency with existing conventions | Low | Review against policy-pack-v1 |
| Scope creep into service patterns | High | Strict exclusion list in scope |

## Success Metrics
- All Tier 1-2 deliverables complete and reviewed
- Relationship types used in at least 3 existing documents
- Agent memory protocol referenced in policy pack
- CHANGELOG reflects all changes with rationale

## Relationships

| Type | Target | Notes |
|------|--------|-------|
| derived-from | `docs/research/repo_dossiers/memorizer__petabridge__memorizer-v1.md` | Source research dossier (Section 10) |
| derived-from | `docs/research/2026-01-20_memorizer-v1-integration-report.md` | Integration analysis |
| depends-on | Phase-02 (Canonical Core Architecture) | Requires established core structure |
| depends-on | Phase-20 (Continuous Improvement) | Builds on improvement patterns |
| contextualizes | `core/orchestrator/RELATIONSHIP_TYPES.md` | Deliverable from this phase |
| contextualizes | `core/agents/AGENT_MEMORY_PROTOCOL.md` | Deliverable from this phase |
| contextualizes | `core/ARTIFACT_INDEX.md` | Deliverable from this phase |
| contextualizes | `core/arch/CHANGE_EVENT_TYPES.md` | Deliverable from this phase |
