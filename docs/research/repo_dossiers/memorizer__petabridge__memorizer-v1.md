# Repo Dossier: petabridge/memorizer-v1

**Snapshot date:** 2026-01-20

## 1) One-paragraph summary

Memorizer is a .NET-based memory management service for AI agents that provides semantic storage, retrieval, versioning, and relationship management via MCP (Model Context Protocol). It enables agents to store structured memories with vector embeddings, search using semantic similarity, and build knowledge graphs through explicit relationships. The project emphasizes autonomous agent memory management with comprehensive versioning/audit trails and extensible tool interfaces.

## 2) Core orchestration model

- **Primary primitive:** Memory graph with typed relationships (explains, example-of, chunk-of, supersedes, similar-to)
- **State model:** Explicit versioned memory objects with full event audit trail; each change creates a snapshot
- **Concurrency:** Akka.NET actor model for background jobs (chunking, re-embedding); async processing with graceful degradation
- **Human-in-the-loop:** Web UI for manual memory management; agent autonomy emphasized (no permission prompts for memory operations)

## 3) Tooling and execution

- **Tool interface:** MCP (Model Context Protocol) via `[McpServerToolType]` attribute; tools exposed as: store, searchMemories, get, getMany, delete, edit, updateMetadata, createRelationship, revertToVersion
- **Runtime environment:** Docker + PostgreSQL/pgvector + Ollama; self-hosted service architecture
- **Sandboxing / safety controls:** Memory-scoped (no shell/file access); confidence scores for curation; relationship typing for traceability

## 4) Observability and evaluation

- **Tracing/logging:** OpenTelemetry instrumentation (OTLP export); ActivitySource-based spans for memory operations
- **Evaluation harness:** Integration tests with PostgreSQL containers; comparison endpoints for embedding strategy A/B testing (/search/compare)

## 5) Extensibility

- **Where extensions live:** `src/Memorizer/Tools/` (MCP tools), `src/Memorizer/Services/` (core services)
- **How to add tools/skills:** Implement class with `[McpServerToolType]` attribute; methods become MCP tools
- **Config surface:** appsettings.json for embeddings (model, dimensions), chunking (enabled, threshold, target size), similarity (thresholds), CORS

## 6) Notable practices worth adopting in AGENT 33

1. **Event-sourced versioning with discriminated union events.** Each memory change (ContentUpdated, MetadataUpdated, RelationshipAdded, MemoryReverted) is recorded with typed event data, enabling full audit trails and rollback.

2. **Dual embedding strategy for search optimization.** Metadata embeddings (title + tags) separate from content embeddings improve keyword-style query results without losing semantic depth.

3. **Lightweight search results by default.** Return IDs/titles/scores instead of full content to prevent context window bloat; agents fetch full content on demand with Get/GetMany.

4. **Preserve original during transformation.** When chunking or summarizing content, keep the original intact and create relationships to derived artifacts (chunk-of, summarizes).

5. **Actor-based async processing.** Background chunking/re-embedding with Akka.NET provides supervision, fault tolerance, and isolation without blocking request handlers.

6. **AGENT.md as autonomous memory protocol.** Define agent behavior via system prompt embedding that instructs: "search before acting, store reusable knowledge, retire obsolete entries, never ask permission."

7. **Relationship types as semantic primitives.** Typed relationships (explains, example-of, supersedes, similar-to, chunk-of) enable knowledge graph navigation and provenance tracking.

8. **Similarity discovery with optional persistence.** On-demand vector similarity queries with configurable thresholds; users can persist confirmed similarities as bidirectional relationships.

## 7) Risks / limitations to account for

- **Service-oriented architecture:** Memorizer is a running service, not a library—requires infrastructure for production use
- **Embedding model lock-in:** Dimension mismatches require migration; changing models has operational cost
- **Eventual consistency:** Background chunking means chunks aren't immediately searchable after storage
- **Storage overhead:** Preserving originals + chunks + summaries = 2-5x storage multiplier

## 8) Feature extraction (for master matrix)

- **Repo:** petabridge/memorizer-v1
- **Primary language:** C# (.NET 9/10)
- **Interfaces:** MCP server (HTTP/SSE), Web UI, REST API
- **Orchestration primitives:** Memory graph with typed relationships; no agent orchestration (memory service only)
- **State/persistence:** PostgreSQL + pgvector; full version history with event audit trail
- **HITL controls:** Web UI for manual curation; agents operate autonomously on memory
- **Sandboxing:** Memory-scoped operations; no shell/file/network access surface
- **Observability:** OpenTelemetry instrumentation with OTLP export
- **Evaluation:** Integration tests; A/B comparison endpoints for embedding strategies
- **Extensibility:** MCP tool registration via attributes; ADR-documented design decisions

## 9) Evidence links

- https://github.com/petabridge/memorizer-v1/tree/dev (dev branch)
- https://github.com/petabridge/memorizer-v1/blob/dev/README.md
- https://github.com/petabridge/memorizer-v1/blob/dev/AGENT.md
- https://github.com/petabridge/memorizer-v1/blob/dev/DEVELOPMENT.md
- https://github.com/petabridge/memorizer-v1/blob/dev/src/Memorizer/Tools/MemoryTools.cs
- https://github.com/petabridge/memorizer-v1/blob/dev/src/Memorizer/Models/MemoryEvent.cs
- https://github.com/petabridge/memorizer-v1/blob/dev/docs/adr/2025-05-23-asynchronous-memory-chunking-with-actors.md
- https://github.com/petabridge/memorizer-v1/blob/dev/docs/adr/2025-11-28-memory-similarity-discovery.md
- https://github.com/petabridge/memorizer-v1/blob/dev/docs/adr/2025-01-27-preserve-original-memories-during-chunking.md
- https://github.com/petabridge/memorizer-v1/blob/dev/docs/adr/POC_DUAL_EMBEDDINGS.md
- https://github.com/petabridge/memorizer-v1/blob/dev/RELEASE_NOTES.md

---

## 10) AGENT-33 Adaptation Analysis

> *This section focuses on principles adaptable to AGENT-33 documentation and workflow features, excluding database/service patterns.*

### Recommended Adaptations

#### A. Event-Sourced Document Versioning

**Source pattern:** MemoryEvent discriminated unions (ContentUpdated, MetadataUpdated, MemoryReverted)

**AGENT-33 application:** Apply to phase documents, prompts, and research artifacts:
- Track changes with typed events (ContentUpdated, SectionAdded, TemplateApplied)
- Enable rollback to previous document versions
- Provide human-readable change descriptions via `GetDisplayText()` pattern

#### B. Lightweight Artifact References

**Source pattern:** Search returns IDs/titles/scores; full content fetched on demand

**AGENT-33 application:** For large prompt packs and research dossiers:
- Index artifacts with metadata (title, tags, type, created)
- Return lightweight references in searches
- Load full content only when explicitly requested
- Reduces context window consumption in agent sessions

#### C. Relationship Typing for Knowledge Graphs

**Source pattern:** Typed relationships (explains, example-of, supersedes, chunk-of)

**AGENT-33 application:** Connect prompts, phases, templates, and research:
- `depends-on`: Phase → prerequisite phases
- `derived-from`: Prompt → upstream template
- `exemplifies`: Example → abstract pattern
- `supersedes`: Updated artifact → deprecated version
- `contextualizes`: Research dossier → feature being designed

#### D. Preserve-Original-During-Refinement

**Source pattern:** Keep originals intact, create relationships to derived artifacts

**AGENT-33 application:** When refining prompts or documentation:
- Store original as immutable "collected" artifact
- Create refined version with `supersedes` relationship
- Maintain provenance chain for audit and rollback

#### E. Autonomous Agent Memory Protocol (AGENT.md pattern)

**Source pattern:** System prompt defining agent autonomy for memory operations

**AGENT-33 application:** Create AGENT.md or equivalent briefing that:
- Instructs agents to search knowledge base before starting tasks
- Defines when to store reusable learnings vs. ephemeral notes
- Sets curation expectations (retire obsolete, relate related)
- Removes permission friction for routine operations

#### F. Similarity Discovery for Cross-Linking

**Source pattern:** On-demand similarity queries with persistence option

**AGENT-33 application:** For prompt and template management:
- Surface similar prompts when authoring new ones
- Suggest relationship creation when similarity exceeds threshold
- Build knowledge graph edges through discovered similarity

### Implementation Priority

| Adaptation | Impact | Effort | Priority |
|------------|--------|--------|----------|
| D. Preserve-Original-During-Refinement | High | Low | 1 |
| C. Relationship Typing | High | Medium | 2 |
| E. Autonomous Agent Memory Protocol | High | Low | 3 |
| B. Lightweight Artifact References | Medium | Medium | 4 |
| A. Event-Sourced Document Versioning | Medium | High | 5 |
| F. Similarity Discovery | Low | High | 6 |

### Non-Applicable Patterns

The following memorizer patterns are explicitly **excluded** as they require service infrastructure:

- PostgreSQL/pgvector storage layer
- MCP server endpoints and tool registration
- Akka.NET actor system for background processing
- Embedding generation and dimension management
- Web UI for memory management
- OpenTelemetry instrumentation
