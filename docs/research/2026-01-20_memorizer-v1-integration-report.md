# Memorizer-v1 Integration Report

**Date**: 2026-01-20
**Source**: petabridge/memorizer-v1 (dev branch)
**Target**: AGENT-33 documentation framework

---

## Executive Summary

This report documents the competitive research findings from petabridge/memorizer-v1 and the planned integration of applicable extensibility patterns into AGENT-33. The research focused on principles that enhance documentation workflows and artifact management—excluding service/database patterns.

---

## Research Artifacts Created

| Artifact | Location | Purpose |
|----------|----------|---------|
| Repo Dossier | `docs/research/repo_dossiers/memorizer__petabridge__memorizer-v1.md` | Full research analysis with adaptation section |
| Feature Matrix Update | `docs/research/master_feature_matrix.md` | Added memorizer-v1 to cross-repo comparison |
| Phase Plan | `docs/phases/PHASE-21-EXTENSIBILITY-PATTERNS-INTEGRATION.md` | Implementation roadmap |

---

## Key Findings from Memorizer-v1

### Patterns Identified for Adaptation

| # | Pattern | Source in Memorizer | Relevance to AGENT-33 |
|---|---------|---------------------|----------------------|
| 1 | **Event-sourced versioning** | MemoryEvent discriminated unions | Track document changes with typed events |
| 2 | **Dual embedding strategy** | Metadata vs content embeddings | Lightweight artifact indexing vs full content |
| 3 | **Lightweight search results** | IDs/titles/scores by default | Reduce context window consumption |
| 4 | **Preserve original during transformation** | ADR: Preserve-Original-During-Chunking | Immutable collected/ with relationship links |
| 5 | **Actor-based async processing** | Akka.NET chunking actors | N/A (requires service infrastructure) |
| 6 | **Autonomous agent memory protocol** | AGENT.md system prompt | Define agent autonomy for knowledge management |
| 7 | **Typed relationships** | explains, example-of, supersedes, chunk-of | Connect prompts, phases, templates, research |
| 8 | **Similarity discovery** | Vector similarity with optional persistence | Surface related artifacts |

### Patterns Excluded (Service Dependencies)

- PostgreSQL/pgvector storage layer
- MCP server endpoints and tool registration
- Akka.NET actor system
- Embedding generation and dimension management
- Web UI for memory management
- OpenTelemetry instrumentation

---

## What We Will Add

### Tier 1: Core Patterns (High Priority)

#### 1. Relationship Typing System
**New file**: `core/orchestrator/RELATIONSHIP_TYPES.md`

Defines semantic primitives for connecting artifacts:
- `depends-on` - Phase prerequisites
- `derived-from` - Template lineage
- `supersedes` - Version replacement
- `exemplifies` - Pattern instantiation
- `contextualizes` - Research → design
- `explains` - Documentation links
- `chunk-of` - Document decomposition

**Impact**: Enables knowledge graph navigation across AGENT-33 artifacts.

#### 2. Preserve-Original-During-Refinement Policy
**Updated files**: 
- `dedup-policy.md` ✅ (already updated)
- `sync-plan.md` ✅ (already updated)

Formalizes:
- `collected/` is immutable after ingest
- All refinements create new artifacts with `supersedes` relationships
- Provenance chain: collected → core → distributed

**Impact**: Maintains audit trail and enables rollback.

---

### Tier 2: Agent Protocol (Medium Priority)

#### 3. Autonomous Agent Memory Protocol
**New file**: `core/agents/AGENT_MEMORY_PROTOCOL.md`

Instructs agents to:
1. Search knowledge base before starting tasks
2. Store reusable learnings in agent-learning.md
3. Create relationships between discovered artifacts
4. Retire obsolete entries with supersedes links
5. Operate autonomously for routine memory operations

**Impact**: Reduces permission friction, improves knowledge accumulation.

---

### Tier 3: Artifact Indexing (Medium Priority)

#### 4. Lightweight Artifact Index
**New file**: `core/ARTIFACT_INDEX.md`

Metadata index for efficient discovery:
- artifact-id, title, type, tags, created, supersedes
- Enables search without loading full content
- Reduces context window consumption

**Impact**: Faster artifact discovery during agent sessions.

---

### Tier 4: Change Tracking (Lower Priority)

#### 5. Typed Change Events
**New file**: `core/arch/CHANGE_EVENT_TYPES.md`

Event types for document versioning:
- `artifact_created`, `content_updated`, `metadata_updated`
- `relationship_added`, `artifact_superseded`, `artifact_reverted`
- Human-readable display text convention

**Impact**: Richer CHANGELOG entries, better audit trail.

---

### Tier 5: Deferred

#### 6. Similarity Discovery
**Status**: Deferred until artifact count warrants it

When needed:
- Add similarity scoring guidance
- Document cross-linking discovery workflow

---

## Documentation Already Updated

| File | Change | Rationale |
|------|--------|-----------|
| `dedup-policy.md` | Added immutability principle, relationship types section | Formalize preserve-original pattern |
| `sync-plan.md` | Added relationship tracking, immutability, provenance chain | Align with new patterns |
| `docs/phases/README.md` | Added Phase 21 to index | Track new phase |
| `core/CHANGELOG.md` | Added research intake and documentation update entries | Audit trail |

---

## Implementation Priority Matrix

| Priority | Deliverable | Effort | Impact | Phase 21 Tier |
|----------|-------------|--------|--------|---------------|
| 1 | Preserve-Original Policy | Low | High | 1 ✅ Done |
| 2 | Relationship Typing System | Medium | High | 1 |
| 3 | Autonomous Agent Memory Protocol | Low | High | 2 |
| 4 | Lightweight Artifact Index | Medium | Medium | 3 |
| 5 | Typed Change Events | Medium | Medium | 4 |
| 6 | Similarity Discovery | High | Low | 5 (Deferred) |

---

## Success Criteria

- [ ] All Tier 1-2 deliverables complete and reviewed
- [ ] Relationship types used in at least 3 existing documents
- [ ] Agent memory protocol referenced in policy pack
- [ ] CHANGELOG reflects all changes with rationale
- [ ] No service/database dependencies introduced

---

## Next Steps

1. **Immediate**: Review this report and Phase 21 plan
2. **Sprint 1**: Complete Tier 1 (Relationship Types) + Tier 2 (Agent Protocol)
3. **Sprint 2**: Complete Tier 3 (Artifact Index) + Tier 4 (Change Events)
4. **Future**: Evaluate Tier 5 (Similarity Discovery) when artifact count > 100

---

## Relationships

| Type | Target | Notes |
|------|--------|-------|
| derived-from | `docs/research/repo_dossiers/memorizer__petabridge__memorizer-v1.md` | Source research dossier |
| contextualizes | `docs/phases/PHASE-21-EXTENSIBILITY-PATTERNS-INTEGRATION.md` | Informs phase planning |
| explains | `core/orchestrator/RELATIONSHIP_TYPES.md` | Pattern source for relationship typing |
| explains | `core/agents/AGENT_MEMORY_PROTOCOL.md` | Pattern source for agent autonomy |

## References

- Research Dossier: `docs/research/repo_dossiers/memorizer__petabridge__memorizer-v1.md`
- Phase Plan: `docs/phases/PHASE-21-EXTENSIBILITY-PATTERNS-INTEGRATION.md`
- Source: https://github.com/petabridge/memorizer-v1/tree/dev
