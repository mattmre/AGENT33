# P2.3: Shared Conversation-Memory Design

## Purpose

Define how multiple agents within a single workflow DAG share a common
conversation-memory space while preserving tenant isolation, session scoping,
and cross-instance safety.

This is an architecture-only document. It does not propose runtime code
changes. The first safe shared-memory write path will be implemented in P2.4.

## Related Documents

- [`horizontal-scaling-architecture.md`](../operators/horizontal-scaling-architecture.md) -- P1.1 state boundary model
- P1.2 scaling module (`engine/src/agent33/scaling/`) -- distributed lock primitives, instance registry, state guards
- Memory module (`engine/src/agent33/memory/`) -- current memory architecture

---

## 1. Current Memory Model

### 1.1 Short-Term Buffer (`short_term.py`)

`ShortTermMemory` is an in-process dataclass that holds a list of `Message`
objects (role + content). It is scoped to a single `AgentRuntime` invocation
and is never shared across agents or persisted. Token-aware trimming
(`get_context(max_tokens)`) discards the oldest messages first to stay within
context window limits.

Each `AgentRuntime.invoke()` call constructs its own message history from
scratch (system prompt + user content). There is no mechanism today for one
agent's short-term buffer to be visible to another agent.

### 1.2 Long-Term Memory (`long_term.py`)

`LongTermMemory` is backed by PostgreSQL with the pgvector extension. It
stores `MemoryRecord` rows with:

- `id` (auto-increment integer primary key)
- `content` (text)
- `embedding` (vector of 1536 floats, configurable)
- `metadata` (JSONB)
- `created_at` (timestamp)

**Critical gap: there is no `tenant_id` column on `MemoryRecord`.** The JSONB
`metadata` field sometimes contains `session_id` and `agent_name` (set by
`ObservationCapture.record()`), but these are unindexed advisory fields, not
enforced filters. All queries (`search`, `scan`, `count`) operate over the
entire table without any tenant or session predicate.

This means the long-term memory store is currently a single global pool. Any
agent from any tenant can, in principle, retrieve any other tenant's
observations if their embeddings happen to be semantically close.

### 1.3 Observation Capture (`observation.py`)

`ObservationCapture` is the write path into long-term memory. When an agent
produces output, `AgentRuntime` creates an `Observation` with:

- `session_id` -- the session the agent is running within
- `agent_name` -- the agent that produced the observation
- `event_type` -- `llm_response`, `iterative_completion`, `tool_call`, etc.
- `content` -- truncated to 2000 chars of the LLM response
- `metadata` -- model, token count, routing decision
- `tags` -- privacy tags (`sensitive`, `pii`, `secret` suppress LTM storage)

The observation is embedded via the `EmbeddingProvider` and stored in
`LongTermMemory.store()`. It is also published to NATS on subject
`agent.observation` if the NATS bus is wired.

**Important:** `session_id` and `agent_name` are stored inside the JSONB
metadata, not as first-class indexed columns. The observation buffer itself
(`_buffer`) is in-process and per-`ObservationCapture` instance.

### 1.4 Progressive Recall (`progressive_recall.py`)

`ProgressiveRecall` is the read path from long-term memory. It provides
three-layer token-efficient retrieval:

- **L1 (index)**: compact topic list (~50 tokens/result)
- **L2 (timeline)**: chronological context (~200 tokens/result)
- **L3 (full)**: complete observation details (~1000 tokens/result)

During `AgentRuntime.invoke()`, the runtime queries progressive recall at the
`index` level with `top_k=5` and injects results into the system prompt under
`# Prior Context (from memory)`.

**Current limitation:** the search is unscoped -- it searches the entire
`memory_records` table by embedding similarity without filtering by session,
tenant, or agent.

### 1.5 Hybrid Retrieval Pipeline (`hybrid.py`, `rag.py`, `bm25.py`)

The `HybridSearcher` combines pgvector semantic search with an in-process BM25
keyword index using Reciprocal Rank Fusion (RRF). The `RAGPipeline` wraps this
into augmented-prompt generation with optional query expansion.

The BM25 index is fully in-process and not tenant-scoped. It is populated at
startup from all `LongTermMemory` records via `warm_up_bm25()`.

### 1.6 Session Manager (`session.py`)

`SessionManager` is an encrypted in-memory key-value store for runtime
conversation sessions. Each `SessionData` has `session_id`, `user_id`, and
`agent_name`. Sessions are encrypted with Fernet and stored only in process
memory. This is separate from the `OperatorSessionService` which provides
durable filesystem-backed session lifecycle management.

### 1.7 Context Transfer (`context.py`)

`ContextTransfer` copies named fields from one session's `data` dict to
another session's `data` dict via `SessionManager.update()`. This is the only
existing mechanism for cross-session data sharing, and it operates on the
encrypted in-memory session store, not on long-term memory.

### 1.8 Session Summarizer (`summarizer.py`)

`SessionSummarizer` compresses a list of observations into a structured JSON
summary via LLM and stores it in long-term memory with metadata type
`session_summary`. This creates a durable summary in the same global pool.

### 1.9 How Agents Use Memory Today

The full read-write flow during an agent invocation is:

1. `AgentRuntime.__init__()` receives `progressive_recall` and
   `observation_capture` from `app.state`.
2. During `invoke()` / `invoke_iterative()`, the runtime queries
   `progressive_recall.search()` with the serialized inputs and injects
   results into the system prompt.
3. After the LLM responds, the runtime creates an `Observation` and calls
   `observation_capture.record()` to store it with an embedding.
4. The observation's `session_id` and `agent_name` go into the JSONB metadata
   but are not used as query filters.

**Key observation:** all agents across all sessions and tenants read from and
write to the same unpartitioned memory pool. The only isolation is the
`_PRIVATE_TAGS` mechanism which suppresses LTM storage for PII-tagged
observations.

---

## 2. Multi-Agent Sharing Requirements

### 2.1 What "Shared Conversation Memory" Means

In a workflow DAG, multiple agents execute as steps within a single session.
Today each agent independently reads from and writes to the global memory pool
but there is no structured mechanism for:

- Agent A to intentionally share a conclusion with Agent B downstream in the DAG
- Multiple agents to read from a shared working-memory space that is scoped to
  just this workflow execution
- Distinguishing between "my private scratch notes" and "shared team context"
  within a session

**Shared conversation memory** means a structured, session-scoped memory
namespace where:

1. All agents in a workflow DAG can read shared observations and context
2. Agents can write observations that are explicitly marked as shared
3. The shared namespace is bounded to the session lifetime and tenant scope
4. Per-agent private state remains separate and is not leaked to other agents

### 2.2 Use Cases

| Use case | Description |
| --- | --- |
| DAG step handoff | Agent A's output becomes Agent B's input not just via workflow state but also via shared memory context |
| Collaborative research | A researcher agent stores findings; a code-worker agent reads them to implement |
| Multi-pass review | A QA agent records review comments; a code-worker reads and addresses them |
| Orchestrator situational awareness | The orchestrator agent reads all shared observations to make routing decisions |
| Session replay enrichment | Shared memory provides a richer event timeline than workflow step outputs alone |

### 2.3 What Shared Memory Is Not

Shared conversation memory is not:

- A replacement for workflow step input/output wiring (the DAG state machine
  already handles that)
- A cross-session memory bridge (that remains the role of `ContextTransfer`)
- A real-time streaming channel between concurrently executing agents (that is
  NATS pub/sub)
- A replacement for tool-call results (those are already in the tool loop)

---

## 3. Isolation Constraints

### 3.1 Tenant Isolation

**Hard requirement:** observations written by Tenant A must never appear in
memory queries executed by Tenant B.

Today this is violated: the `memory_records` table has no `tenant_id` column,
and all searches are unfiltered. This must be fixed as a precondition or
co-delivery with shared memory.

**Design decision:** add a `tenant_id` column to `MemoryRecord` (or its
successor table). All write paths must populate it. All read paths must filter
by it. The shared memory design assumes this column exists.

### 3.2 Session Scoping

Shared memory within a session must be visible only to agents operating within
that session. Agents in different sessions -- even for the same tenant -- must
not see each other's shared working memory unless the session is explicitly
linked via `ContextTransfer`.

**Design decision:** shared memory records include both `tenant_id` and
`session_id` as indexed, enforced filter columns. A cross-session search
requires an explicit opt-in parameter.

### 3.3 DAG Boundaries

A workflow DAG defines the execution boundary for shared memory:

- Agents within the same DAG execution share the same session ID and can
  access the shared namespace
- Parallel branches in the DAG can write to shared memory concurrently (see
  conflict resolution in Section 4.5)
- A sub-workflow (nested DAG) inherits the parent session's shared namespace
  by default

### 3.4 Privacy Tags

The existing `_PRIVATE_TAGS` mechanism (`sensitive`, `pii`, `secret`) must
continue to suppress storage in long-term memory regardless of namespace. An
observation tagged `pii` is never stored, not even in the shared namespace.

---

## 4. Proposed Design

### 4.1 Memory Namespaces

Introduce explicit namespace paths for memory records. Every record belongs to
exactly one namespace:

```
{tenant_id}/{session_id}/shared          -- shared working memory for the DAG
{tenant_id}/{session_id}/agent/{agent_id} -- agent-private scratch space
{tenant_id}/global                       -- tenant-wide long-term memory (existing behavior)
```

The namespace is stored as a structured set of columns on the memory record,
not as a concatenated string path:

| Column | Type | Indexed | Description |
| --- | --- | --- | --- |
| `tenant_id` | `varchar(64)` | yes | Tenant isolation key |
| `session_id` | `varchar(64)` | yes (nullable) | Session scope; NULL for tenant-global records |
| `namespace` | `varchar(32)` | yes | One of: `shared`, `agent`, `global` |
| `agent_id` | `varchar(64)` | yes (nullable) | Owning agent; only set when namespace = `agent` |

This maps onto the existing `MemoryRecord` model as new columns (not a
separate table) to avoid fragmenting the embedding index. The existing
unscoped records are retroactively treated as `namespace=global` with
`tenant_id` backfilled from the JSONB metadata where available.

### 4.2 Read Access Model

| Reader | `global` namespace | `shared` namespace | `agent` namespace |
| --- | --- | --- | --- |
| Any agent in the session | read | read | own records only |
| Orchestrator agent | read | read | read (all agents) |
| Agent outside the session | read (same tenant) | no | no |
| Different tenant | no | no | no |

The orchestrator exemption allows the orchestrator agent (identified by
`role=orchestrator` in the agent definition) to inspect any agent's private
scratch space within the same session for oversight purposes.

The `progressive_recall.search()` method gains an optional `namespace_filter`
parameter:

```python
async def search(
    self,
    query: str,
    level: str = "index",
    top_k: int | None = None,
    *,
    tenant_id: str | None = None,
    session_id: str | None = None,
    namespace: str | None = None,
    agent_id: str | None = None,
) -> list[RecallResult]:
```

When `tenant_id` is provided, results are restricted to that tenant. When
`session_id` is provided, results include both session-scoped and
tenant-global records. When `namespace="shared"`, only shared-namespace
records for that session are returned.

### 4.3 Write Access Model

| Writer | Can write to `global` | Can write to `shared` | Can write to `agent` |
| --- | --- | --- | --- |
| Any agent via `ObservationCapture` | yes (default behavior today) | yes (explicit opt-in) | yes (own namespace only) |
| `SessionSummarizer` | yes | no | no |
| External ingestion | yes | no | no |

Writing to the `shared` namespace requires the caller to explicitly set
`namespace="shared"` on the observation. The default write path continues to
target the `global` namespace, preserving backward compatibility.

The `Observation` dataclass gains an optional `namespace` field:

```python
@dataclass(frozen=True, slots=True)
class Observation:
    # ... existing fields ...
    namespace: str = "global"  # "global", "shared", or "agent"
```

`ObservationCapture.record()` reads `namespace` from the observation and
populates the corresponding columns when storing.

### 4.4 Storage Schema Changes

Add columns to the `memory_records` table:

```sql
ALTER TABLE memory_records
    ADD COLUMN tenant_id VARCHAR(64),
    ADD COLUMN session_id VARCHAR(64),
    ADD COLUMN namespace VARCHAR(32) NOT NULL DEFAULT 'global',
    ADD COLUMN agent_id VARCHAR(64);

CREATE INDEX ix_memory_records_tenant ON memory_records (tenant_id);
CREATE INDEX ix_memory_records_session ON memory_records (tenant_id, session_id);
CREATE INDEX ix_memory_records_namespace ON memory_records (tenant_id, session_id, namespace);
```

The pgvector cosine distance search must be adapted to include a `WHERE`
clause for the tenant and session filters. This means the current raw SQL in
`LongTermMemory.search()` becomes:

```sql
SELECT content, metadata, 1 - (embedding <=> :emb::vector) AS score
FROM memory_records
WHERE tenant_id = :tenant_id
  AND (session_id = :session_id OR session_id IS NULL)
  AND namespace IN (:namespaces)
ORDER BY embedding <=> :emb::vector
LIMIT :k
```

A composite index on `(tenant_id, session_id)` plus the ivfflat or HNSW
pgvector index should keep search performance acceptable. Exact index tuning
will be determined during P2.4 implementation based on profiling.

### 4.5 Conflict Resolution

Different observation types require different conflict semantics when multiple
agents write to the shared namespace concurrently:

| Write pattern | Strategy | Rationale |
| --- | --- | --- |
| Observations (event records) | Append-only | Observations are immutable event records. Every agent's observation is valuable. No dedup needed because each observation has a unique ID. |
| Session summaries | Last-write-wins | Only one summary should exist per session at any point. The latest summary supersedes prior ones. |
| Key-value state (future) | Distributed lock | If shared memory later supports structured key-value pairs (e.g., "current plan", "agreed conclusions"), concurrent writers must coordinate via the P1.2 distributed lock primitives. |

For P2.4, only the append-only pattern is in scope. Observations are
inherently append-only (each has a unique UUID, is frozen/immutable, and is
never updated in place). This means the first implementation does not require
any locking or merge logic for the write path.

### 4.6 Cross-Instance Safety

The P1.2 scaling module provides three primitives relevant to shared memory:

1. **`RedisDistributedLock`**: SETNX with TTL-based expiry. Used when a
   write-after-check pattern needs atomicity (e.g., "write a session summary
   only if one does not already exist for this session").

2. **`InstanceRegistry`**: Heartbeat-based peer awareness. Used to detect
   whether multiple instances are serving the same tenant/session, which
   determines whether shared-memory searches need to query the durable store
   or can use the in-process observation buffer.

3. **`SingleInstanceGuard` / `SchedulerOwnershipGuard`**: Used to protect
   scheduled background tasks (e.g., periodic session summarization) from
   duplicate execution across instances.

For the P2.4 append-only observation write path:

- **No distributed lock is needed.** PostgreSQL INSERT is already atomic. Two
  instances can concurrently insert observations into `memory_records` for the
  same session without conflict because each observation has a unique primary
  key.

- **Read consistency caveat:** the in-process BM25 index (`bm25.py`) and the
  observation buffer (`ObservationCapture._buffer`) are replica-local. If
  Instance A writes an observation to PostgreSQL, Instance B will see it in
  pgvector search but not in BM25 search until the next BM25 warm-up cycle.
  This is an existing secondary divergence risk documented in the
  horizontal-scaling architecture and is not worsened by shared memory.

- **When we later add key-value or summary writes** (beyond P2.4), the
  distributed lock must be acquired with a key of the form
  `agent33:lock:memory:{tenant_id}:{session_id}:summary` to prevent
  concurrent summary overwrites.

### 4.7 BM25 Index Scoping

The in-process BM25 index is currently a single global corpus. With memory
namespaces, two options exist:

1. **Post-filter:** Run BM25 search as today, then filter results by
   tenant/session/namespace after scoring. Simple but wastes ranking effort.

2. **Partitioned indexes:** Maintain separate BM25 indexes per tenant. Session
   and namespace filtering remain post-filter since sessions are transient.

**Design decision for P2.4:** use option 1 (post-filter). The BM25 index is
a secondary ranking signal combined via RRF; the primary ranking is pgvector
which will be properly filtered by the SQL WHERE clause. Partitioned BM25
indexes add complexity for a secondary signal and can be revisited if
profiling shows that post-filtering degrades hybrid search quality.

### 4.8 Observation Buffer Consistency

`ObservationCapture._buffer` is an in-process list. In a multi-instance
deployment, each instance has its own buffer. This means:

- `flush()` returns only locally buffered observations, not observations from
  other instances
- Session summarization via `SessionSummarizer.auto_summarize()` only sees
  observations that passed through the local instance

**Design decision:** for P2.4, document this as a known limitation. The
observation buffer is a performance optimization (batching writes), not a
durability mechanism. All observations that reach `ObservationCapture.record()`
are stored in PostgreSQL synchronously. The buffer's role is read-side
convenience (e.g., for local flush before summarization), not the source of
truth.

For future work beyond P2.4, the summarizer should query PostgreSQL with a
`session_id` filter instead of relying on the local buffer. This ensures it
sees all observations for the session regardless of which instance recorded
them.

---

## 5. Implementation Boundary for P2.4

P2.4 implements **the first safe shared-memory write path**. Specifically:

### 5.1 In Scope for P2.4

1. **Add `tenant_id`, `session_id`, `namespace`, `agent_id` columns** to the
   `MemoryRecord` model and create an Alembic migration for the schema change.

2. **Update `ObservationCapture.record()`** to populate the new columns from
   the observation's fields. Add a `namespace` field to `Observation` with
   default `"global"`.

3. **Update `LongTermMemory.store()`** to accept and store the new columns.

4. **Update `LongTermMemory.search()`** to accept optional `tenant_id`,
   `session_id`, and `namespace` filter parameters. When provided, add WHERE
   clauses to the SQL query.

5. **Update `ProgressiveRecall.search()`** to pass through the filter
   parameters to `LongTermMemory.search()`.

6. **Update `AgentRuntime.invoke()` / `invoke_iterative()`** to pass
   `tenant_id` and `session_id` when calling `progressive_recall.search()`.

7. **Backfill logic** for existing records: a one-time migration script or
   Alembic data migration that sets `namespace='global'` and attempts to
   extract `tenant_id` from JSONB metadata for existing records.

8. **Tests:** unit tests for namespace-filtered search, integration tests for
   multi-agent shared write/read flow within a session.

### 5.2 Explicitly Deferred Beyond P2.4

- Partitioned BM25 indexes (post-filter is sufficient)
- Distributed-lock-protected summary writes
- Key-value shared state within the namespace
- Cross-session memory bridges beyond `ContextTransfer`
- Observation buffer federation across instances
- UI/API endpoints for managing memory namespaces
- Memory retention policies scoped to namespaces
- Embedding cache partitioning by tenant

---

## 6. Non-Goals

This design does **not** address:

1. **Real-time inter-agent communication.** Agents needing synchronous
   message passing should use the NATS event bus, not memory writes.

2. **Cross-tenant memory sharing.** There is no use case for tenants to share
   memory. Tenant isolation is a hard boundary.

3. **Memory garbage collection or compaction.** Namespace-aware retention
   policies are deferred. Existing `RetentionManager` TTL mechanisms are
   session-level, not namespace-level.

4. **Embedding model compatibility across namespaces.** The `EmbeddingSwapManager`
   hot-swap feature affects all namespaces equally. There is no per-namespace
   embedding model selection.

5. **Replacing the workflow DAG state machine.** Shared memory supplements
   the DAG step input/output wiring; it does not replace it. Workflow step
   results continue to flow through the expression evaluator and state
   machine.

6. **Permission-based access control within a tenant.** All agents within a
   tenant can access the `global` namespace. All agents within a session can
   access the `shared` namespace. Finer-grained role-based access (e.g.,
   "only QA agents can read code-worker scratch") is out of scope.

7. **Migrating the session `SessionManager` (encrypted in-memory store) to a
   shared backend.** That is a P1.3+ scaling concern, not a memory namespace
   concern.

---

## Appendix A: Data Flow Diagram

```
AgentRuntime.invoke()
    |
    |-- [READ] progressive_recall.search(query, tenant_id, session_id, namespace="shared")
    |       |
    |       +-- LongTermMemory.search(embedding, tenant_id, session_id, namespaces=["shared","global"])
    |               |
    |               +-- SQL: WHERE tenant_id = ? AND (session_id = ? OR session_id IS NULL)
    |
    |-- [LLM call] router.complete(messages)
    |
    |-- [WRITE] observation_capture.record(Observation(namespace="shared", ...))
            |
            +-- embedding_provider.embed(content)
            +-- LongTermMemory.store(content, embedding, metadata, tenant_id, session_id, namespace)
                    |
                    +-- INSERT INTO memory_records (..., tenant_id, session_id, namespace, agent_id)
            |
            +-- nats_bus.publish("agent.observation", {...})
```

## Appendix B: Lock Key Naming Convention

For future writes that require distributed coordination (summaries, key-value
state), use this lock key pattern:

```
agent33:lock:memory:{tenant_id}:{session_id}:{operation}
```

Examples:
- `agent33:lock:memory:tenant42:sess_abc:summary` -- session summary write
- `agent33:lock:memory:tenant42:sess_abc:kv:current_plan` -- key-value write

This follows the `agent33:lock:` prefix convention established by P1.2's
`_REDIS_LOCK_PREFIX`.

## Appendix C: Migration Path for Existing Records

Existing `memory_records` rows have no `tenant_id`, `session_id`, `namespace`,
or `agent_id` values. The migration strategy:

1. Add columns as nullable with defaults (`namespace DEFAULT 'global'`).
2. Run a data migration that inspects `metadata->>'session_id'` and
   `metadata->>'agent_name'` to populate the new columns where possible.
3. Records with no recoverable tenant_id are assigned to a `__legacy__`
   tenant placeholder.
4. After migration, add a NOT NULL constraint on `tenant_id` and `namespace`.
5. Update all write paths to require `tenant_id` before the NOT NULL
   constraint is applied.
