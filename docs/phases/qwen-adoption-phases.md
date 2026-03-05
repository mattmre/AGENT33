# Qwen-Agent Competitive Adaptation — Phase Plan (Phases 36–43)

## Background

Based on deep competitive analysis of [QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent) (Session 55, documented in `docs/research/session55-qwen-agent-analysis.md`), AGENT-33 has architectural gaps in 7 areas where Qwen-Agent demonstrates production-quality patterns. These phases adopt their proven designs while preserving AGENT-33's enterprise architecture strengths (governance, multi-tenancy, DAG workflows, security).

**Strategy:** Evolutionary integration — absorb patterns that fill gaps without replacing existing strengths.

## Scorecard Summary

| Dimension | AGENT-33 | Qwen-Agent | Action |
|-----------|:--------:|:----------:|--------|
| Enterprise governance/security | ★★★★★ | ★★☆ | Preserve |
| DAG workflows | ★★★★★ | ★☆☆ | Preserve |
| Memory/RAG pipeline | ★★★★☆ | ★★★☆ | Enhance (Phase 39) |
| Skills/plugins | ★★★★☆ | ★★★★☆ | Preserve |
| Streaming UX | ★☆☆ | ★★★★★ | **Adopt (Phase 38)** |
| Multimodal messages | ★★☆ | ★★★★★ | **Adopt (Phase 37)** |
| Model compatibility (text fallback) | ★☆☆ | ★★★★☆ | **Adopt (Phase 36)** |
| Agent archetypes | ☆☆☆ | ★★★★☆ | **Adopt (Phase 40)** |
| Multi-agent conversation | ★★☆ | ★★★★☆ | **Adopt (Phase 41)** |
| Code interpreter | ★★★☆ | ★★★★★ | **Adopt (Phase 42)** |
| MCP interoperability | ★★☆ | ★★★☆ | **Complete (Phase 43)** |

---

## Phase 36: Text-Based Tool Call Parsing

**Priority:** P1 — Quick Win | **Risk:** Low | **Lines:** ~250

### Problem
AGENT-33's tool loop is 100% dependent on structured `tool_calls` from the LLM API response. Models without native function calling (open-weight models via Ollama, older GPT variants, reasoning models) cannot use tools at all. Qwen-Agent's `FnCallAgent` handles both structured and text-based patterns.

### Design
Insert a configurable `TextToolParser` between the LLM response and the tool-call detection in `tool_loop.py`. Only activates when `response.tool_calls` is None — zero impact on models with native function calling.

**Parser hierarchy (ChainedParser tries each in order):**
1. **ReActParser** — `Action: tool_name\nAction Input: {"arg": "val"}`
2. **XMLToolParser** — `<tool_call><name>tool_name</name><arguments>{...}</arguments></tool_call>`
3. **HermesToolParser** — `<|tool_call|>{"name": "...", "arguments": {...}}<|/tool_call|>`

### Files
| File | Change |
|------|--------|
| `llm/text_tool_parser.py` | **NEW** — TextToolParser protocol, ReActParser, XMLToolParser, HermesToolParser, ChainedParser |
| `agents/tool_loop.py` | Add `text_tool_parser` to ToolLoopConfig; insert parse step between LLM response and `has_tool_calls` check (~line 212); use `dataclasses.replace()` to inject parsed tool_calls into frozen LLMResponse |
| `agents/runtime.py` | Pass text_tool_parser from config through to ToolLoop |
| `tests/test_text_tool_parser.py` | Unit tests for each parser + tool loop integration |

### Insertion Point
```python
# tool_loop.py ~line 211-215 (BEFORE)
response = await self._router.complete(messages, ...)
if response.tool_calls:  # only checks structured API tool_calls

# tool_loop.py ~line 211-218 (AFTER)
response = await self._router.complete(messages, ...)
if not response.tool_calls and self._config.text_tool_parser:
    parsed = self._config.text_tool_parser.parse(response.content)
    if parsed:
        response = dataclasses.replace(response, tool_calls=parsed)
if response.tool_calls:
```

---

## Phase 37: Multimodal Content Blocks

**Priority:** P1 — Foundation | **Risk:** Medium | **Lines:** ~200

### Problem
`ChatMessage.content` is `str`-only. The `multimodal/` module manually constructs provider-specific formats, bypassing `ChatMessage` entirely. This prevents multimodal messages from flowing through the standard agent pipeline (tool loop, context management, observation capture).

### Design
Widen `ChatMessage.content` to `str | list[ContentPart]` with a backward-compatible `text_content` property. Each provider's serializer maps ContentBlocks to its native format.

### Data Model
```python
@dataclasses.dataclass(frozen=True, slots=True)
class TextBlock:
    text: str

@dataclasses.dataclass(frozen=True, slots=True)
class ImageBlock:
    url: str | None = None      # URL or data URI
    base64_data: str | None = None
    media_type: str = "image/png"
    detail: str = "auto"        # OpenAI: "low"|"high"|"auto"

@dataclasses.dataclass(frozen=True, slots=True)
class AudioBlock:
    url: str | None = None
    base64_data: str | None = None
    media_type: str = "audio/wav"

ContentPart = TextBlock | ImageBlock | AudioBlock
```

### Files
| File | Change |
|------|--------|
| `llm/base.py` | Add TextBlock, ImageBlock, AudioBlock, ContentPart; widen `ChatMessage.content`; add `text_content` property |
| `llm/openai.py` | `_serialize_message()` handles `list[ContentPart]` → OpenAI format |
| `llm/ollama.py` | `_serialize_message()` handles `list[ContentPart]` → Ollama `images[]` format |
| `llm/airllm_provider.py` | Use `m.text_content` for text extraction |
| `agents/context_manager.py` | `estimate_message_tokens()` handles list content |
| `api/routes/chat.py` | Pydantic models for multimodal content in API |
| `testing/mock_llm.py` | Use `msg.text_content` for content matching |
| `tests/test_multimodal_messages.py` | Serialization roundtrip, backward compat |

### Backward Compatibility
```python
# Before (still works):
msg = ChatMessage(role="user", content="Hello")
assert msg.content == "Hello"
assert msg.text_content == "Hello"

# New (multimodal):
msg = ChatMessage(role="user", content=[TextBlock("Describe this"), ImageBlock(url="...")])
assert msg.text_content == "Describe this"  # extracts text blocks
```

---

## Phase 38: Streaming Agent Loop

**Priority:** P0 — Critical UX | **Risk:** High | **Lines:** ~600

### Problem
The entire agent execution pipeline blocks until completion. No intermediate visibility into tool loop progress. Users see a loading spinner for potentially minutes of multi-step agent work. Qwen-Agent's generator-based `_run()` provides real-time snapshots.

### Design
Add parallel streaming methods at each layer — existing non-streaming methods remain untouched. AsyncGenerator everywhere internally; SSE at the HTTP boundary (following `operations_hub.py` pattern).

**Implementation phases:**
- **38a (this phase):** Loop-level event streaming — emit events between tool loop iterations using existing `complete()` calls
- **38b (future phase):** LLM token-level streaming — `stream_complete()` with SSE/NDJSON chunk parsing and tool_call reassembly

### Event Schema
```python
EventType = Literal[
    "loop_started",        # Config, model, agent_name
    "iteration_started",   # Iteration number
    "llm_request",         # Message count, tool count
    "llm_response",        # Content preview, tokens, has_tool_calls
    "tool_call_requested", # Tool name, arguments
    "tool_call_started",   # Tool name, call_id
    "tool_call_completed", # Tool name, success, output preview
    "tool_call_blocked",   # Governance blocked — reason
    "confirmation_prompt", # Double-confirmation sent
    "confirmation_result", # Continue/completed/ambiguous
    "context_managed",     # Messages before/after
    "loop_detected",       # Doom loop
    "error",               # LLM or tool error
    "completed",           # Termination reason, final output
]

@dataclasses.dataclass(frozen=True, slots=True)
class ToolLoopEvent:
    event_type: EventType
    iteration: int
    timestamp: float
    data: dict[str, Any]
    tokens_used: int = 0
    tool_calls_made: int = 0
```

### Files
| File | Change |
|------|--------|
| `agents/events.py` | **NEW** — ToolLoopEvent, EventType |
| `llm/base.py` | Add LLMStreamChunk dataclass, `stream_complete` to Protocol |
| `llm/openai.py` | Add `stream_complete()` — httpx `aiter_lines()` with SSE parsing |
| `llm/ollama.py` | Add `stream_complete()` — NDJSON line parsing |
| `llm/router.py` | Add `stream_complete()` pass-through |
| `agents/tool_loop.py` | Add `run_stream()` → `AsyncGenerator[ToolLoopEvent, None]` parallel to `run()` |
| `agents/runtime.py` | Add `invoke_iterative_stream()` |
| `api/routes/agents.py` | New `/invoke-iterative/stream` endpoint with `StreamingResponse` SSE |
| `tests/test_streaming_tool_loop.py` | Streaming event tests |

### Critical Decisions
1. **`run_stream()` parallels `run()`** — does NOT replace it; extracts shared helpers
2. **Error events, not exceptions** — AsyncGenerators can't propagate; use `event_type: "error"` + terminal `completed` event
3. **Backpressure** — check `request.is_disconnected()` in SSE endpoint; generator cancellation via `asyncio.CancelledError`

---

## Phase 39: LLM Query Expansion for RAG

**Priority:** P2 — Quick Win | **Risk:** Low | **Lines:** ~200

### Problem
RAG pipeline sends raw user query directly to embedding + BM25 with no preprocessing. Short or ambiguous queries retrieve poorly. Qwen-Agent uses its Memory agent to preprocess queries before retrieval.

### Design
Add a `QueryExpander` stage before hybrid search. Uses a small/cheap LLM to generate synonyms and sub-queries, then augments the BM25 keyword search and enriches the embedding query.

### Data Model
```python
class ExpandedQuery(BaseModel):
    original: str
    expanded_text: str         # Enriched version for embedding
    keywords: list[str]        # For BM25 boost
    sub_queries: list[str]     # Alternative phrasings
    expansion_tokens_used: int

class QueryExpander:
    def __init__(self, router: ModelRouter, model: str = "llama3.2",
                 enabled: bool = True, max_tokens: int = 200): ...
    async def expand(self, query: str) -> ExpandedQuery: ...
```

### Integration
```
User Query → [QueryExpander] → expanded_text for embedding
                             → keywords for BM25 boost
                             → sub_queries (future: multi-query)
           → [HybridSearcher] → RAGResult
```

### Files
| File | Change |
|------|--------|
| `memory/query_expansion.py` | **NEW** — QueryExpander, ExpandedQuery |
| `memory/rag.py` | Add `query_expander` parameter; expansion stage in `query_with_diagnostics()`; pass keywords to hybrid path |
| `main.py` | Wire QueryExpander into RAGPipeline at startup |
| `tests/test_query_expansion.py` | Expansion tests |

### Token Budget
| Metric | Cost |
|--------|------|
| Prompt tokens | ~150-250 |
| Response tokens | ~100-150 |
| **Total per query** | **~300-400 tokens** |
| Latency | ~200-500ms |

Mitigation: disabled for queries < 10 chars, tight max_tokens=200, uses cheapest model, integrates with RetrievalStageDiagnostic for monitoring.

---

## Phase 40: Agent Archetypes

**Priority:** P2 — Developer Experience | **Risk:** Low | **Lines:** ~400

### Problem
No template/archetype system — agents are always defined from scratch via JSON. Qwen-Agent provides pre-built agent classes (Assistant, FnCallAgent, Router, GroupChat) with sensible defaults. AGENT-33 users must manually configure capabilities, skills, constraints, and governance for every agent.

### Design
`AgentArchetype` base class with factory `create(name, **overrides) → AgentDefinition`. Four built-in archetypes with all defaults overridable.

### Built-in Archetypes
| Archetype | Description | Pre-selected Config |
|-----------|-------------|-------------------|
| `assistant` | RAG-integrated conversational agent | knowledge_retrieval capability, rag skills, conversational constraints |
| `coder` | Code interpreter + file ops | code_execution capability, code tools, sandbox constraints |
| `router` | 1-of-N agent dispatch | orchestration capability, routing skills, minimal tools |
| `group-chat-host` | Multi-agent conversation facilitator | orchestration + communication, moderation skills |

### Files
| File | Change |
|------|--------|
| `agents/archetypes/__init__.py` | ArchetypeRegistry (register, get, list_all, create_agent) |
| `agents/archetypes/base.py` | AgentArchetype base model |
| `agents/archetypes/assistant.py` | RAG Assistant archetype |
| `agents/archetypes/coder.py` | Code Interpreter archetype |
| `agents/archetypes/router.py` | Router archetype |
| `agents/archetypes/group_chat_host.py` | GroupChat Host archetype |
| `agents/definition.py` | Add optional `archetype` field |
| `main.py` | Register built-in archetypes at startup |
| `tests/test_agent_archetypes.py` | Archetype creation, override, registry tests |

---

## Phase 41: GroupChat Workflow Action

**Priority:** P2 — Multi-Agent | **Risk:** Medium | **Lines:** ~350

**Depends on:** Phase 40 (archetypes for group-chat-host)

### Problem
Current workflow actions support single-agent invocation (`invoke_agent`) and 1-of-N routing (`route`), but no multi-agent conversation. Qwen-Agent's `GroupChat` provides production-quality multi-turn, multi-agent rooms with configurable speaker selection.

### Design
New `group-chat` workflow step action type with configurable speaker selection strategies.

### Data Model
```python
class GroupChatConfig(BaseModel):
    agents: list[str]                    # Agent names/IDs
    speaker_selection: str = "auto"      # auto|round-robin|mention|random
    max_rounds: int = 10
    termination_phrase: str = "TERMINATE"
    message_history_limit: int = 50
    initial_prompt: str | None = None

class SpeakerSelector(Protocol):
    async def select(self, agents: list[str], history: list, current: str) -> str: ...
```

### Speaker Selection
| Strategy | Method |
|----------|--------|
| `auto` | LLM selects next speaker based on conversation context |
| `round-robin` | Cyclic rotation through agent list |
| `mention` | Parse `@agent_name` patterns from last message |
| `random` | Random selection (for diversity/testing) |

### Files
| File | Change |
|------|--------|
| `workflows/actions/group_chat.py` | **NEW** — GroupChatConfig, execute(), message remapping |
| `workflows/actions/speaker_selection.py` | **NEW** — 4 selector implementations |
| `workflows/definition.py` | Add `GROUP_CHAT` to StepAction, add `group_chat` field to WorkflowStep |
| `workflows/executor.py` | Add dispatch branch for GROUP_CHAT in `_dispatch_action()` |
| `tests/test_group_chat_action.py` | Multi-agent conversation tests |

### Message Role Remapping
For each agent's turn, remap message history:
- Own previous messages → `role: "assistant"`
- Other agents' messages → `role: "user"` with `[Agent Name]: ` prefix
- System context → preserved

---

## Phase 42: Stateful Code Execution (Jupyter Adapter)

**Priority:** P3 — Code Interpreter | **Risk:** Medium-High | **Lines:** ~500

**Depends on:** Phase 37 (multimodal for image output capture)

### Problem
Current `CLIAdapter` is stateless command execution. No variable persistence across executions, no multimodal output (matplotlib images, HTML). Qwen-Agent's code interpreter uses IPython with persistent kernel sessions and rich output capture.

### Design
New `JupyterAdapter` extending `BaseAdapter` with `KernelSessionManager` for stateful sessions and `OutputArtifact` for rich outputs.

### Model Extensions
```python
class OutputArtifact(BaseModel):
    type: str       # "image/png", "text/html", "application/json"
    data: str       # base64 for binary, raw for text
    metadata: dict[str, Any] = Field(default_factory=dict)

class ExecutionResult(BaseModel):  # EXTENDED
    # ... existing fields ...
    artifacts: list[OutputArtifact] = Field(default_factory=list)

class AdapterType(StrEnum):
    # ... existing ...
    KERNEL = "kernel"
```

### Session Management
- `KernelSessionManager`: pool of `KernelSession` with idle reaper
- Session keyed by `contract.metadata["session_id"]` — absent = one-shot
- Output capture: stream→stdout, display_data→OutputArtifact
- Phase 1: local kernels | Phase 2 (future): Docker container kernels

### Files
| File | Change |
|------|--------|
| `execution/adapters/jupyter.py` | **NEW** — JupyterAdapter, KernelSessionManager, KernelSession |
| `execution/models.py` | Add OutputArtifact, KERNEL to AdapterType, KernelInterface, artifacts on ExecutionResult |
| `execution/validation.py` | Add IV-06 kernel code safety checks |
| `pyproject.toml` | Add `jupyter` optional dependency group |
| `tests/test_execution_jupyter_adapter.py` | Adapter + session management tests |

### Dependencies
```toml
[project.optional-dependencies]
jupyter = ["jupyter_client>=8.6,<9", "jupyter_core>=5.7,<6", "ipykernel>=6.29,<7"]
```

---

## Phase 43: Complete MCP Server

**Priority:** P3 — Interoperability | **Risk:** Medium | **Lines:** ~600

### Problem
Current MCP server is a placeholder stub with 2 hardcoded tools and mock SSE. External MCP clients (Claude Desktop, Cursor, Windsurf) cannot interact with AGENT-33 capabilities.

### Design
Full MCP server implementation exposing AGENT-33 capabilities via the MCP SDK's `SseServerTransport`. New `mcp_server/` package with bridge pattern for clean service wiring.

### Tools Exposed
| MCP Tool | Maps To | Category |
|----------|---------|----------|
| `invoke_agent` | AgentRuntime.run() | Agent |
| `list_agents` | AgentRegistry | Agent |
| `execute_workflow` | WorkflowExecutor.run() | Workflow |
| `list_workflows` | Workflow registry | Workflow |
| `search_memory` | ProgressiveRecall.search() | RAG |
| `execute_tool` | ToolRegistry.validated_execute() | Tool |
| `list_tools` | ToolRegistry.list_all() | Tool |
| `get_system_status` | Health endpoint aggregation | System |

### Security Model
- Bearer API key on SSE connection
- Scope enforcement per-tool (e.g., `mcp:agents:invoke`)
- All inputs pass through `scan_inputs_recursive` (injection detection)
- Audit logging via structlog

### Files
| File | Change |
|------|--------|
| `mcp_server/__init__.py` | Package init |
| `mcp_server/server.py` | MCP Server setup, handler registration |
| `mcp_server/tools.py` | 8 tool handlers |
| `mcp_server/resources.py` | 3 resources (agent/workflow/tool registries) |
| `mcp_server/bridge.py` | MCPServiceBridge — wires to app.state services |
| `mcp_server/auth.py` | MCP-specific auth |
| `api/routes/mcp.py` | **REWRITE** — real SseServerTransport + POST handler |
| `main.py` | Bind MCPServiceBridge in lifespan |
| `tests/test_mcp_server.py` | Server, tools, auth tests |

---

## Execution Plan

### Wave A — Quick Wins (parallel)
| Phase | Description | Estimated Effort |
|-------|-------------|-----------------|
| 36 | Text-Based Tool Parsing | ~250 lines |
| 39 | LLM Query Expansion | ~200 lines |

### Wave B — Foundation (parallel)
| Phase | Description | Estimated Effort |
|-------|-------------|-----------------|
| 37 | Multimodal Content Blocks | ~200 lines |
| 40 | Agent Archetypes | ~400 lines |

### Wave C — Core UX
| Phase | Description | Estimated Effort |
|-------|-------------|-----------------|
| 38 | Streaming Agent Loop | ~600 lines |

### Wave D — Advanced Features (parallel)
| Phase | Description | Estimated Effort |
|-------|-------------|-----------------|
| 41 | GroupChat Workflow Action | ~350 lines |
| 42 | Jupyter Adapter | ~500 lines |
| 43 | MCP Server | ~600 lines |

### Dependency Graph
```
Wave A: [36] + [39]  ──→  (no deps, start immediately)
Wave B: [37] + [40]  ──→  (no deps on Wave A, can overlap)
Wave C: [38]         ──→  (benefits from 36+37 being done)
Wave D: [41←40] + [42←37] + [43]  ──→  (partial deps)
```

### Total Scope
- **8 new phases** (36–43)
- **~18 new files**, **~28 modified files**
- **~3,100 lines of new code** (estimated)
- **1 PR per phase** for clean review
