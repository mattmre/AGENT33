# Qwen-Agent Competitive Analysis for AGENT-33

**Date:** 2026-03-05
**Session:** 55
**Source Repository:** [QwenLM/Qwen-Agent](https://github.com/QwenLM/Qwen-Agent)
**License:** Apache-2.0
**Method:** Live source code analysis via GitHub API + AGENT33 cross-reference

---

## Executive Summary

Qwen-Agent is Alibaba's production-grade multi-agent framework powering Qwen Chat. This analysis compares its architecture, capabilities, and patterns against AGENT-33 to identify adoption opportunities. **AGENT-33 has significantly stronger infrastructure (governance, workflows, memory, MCP, hooks) while Qwen-Agent has superior developer/user UX patterns (streaming, multimodal, agent archetypes, model compatibility)**. The five highest-impact adoption items are: (1) generator-based streaming in the tool loop, (2) multimodal content blocks in messages, (3) ReAct-style fallback for non-function-calling models, (4) pre-built agent archetypes, and (5) stateful code execution.

---

## 1. Qwen-Agent Architecture Overview

### 1.1 Package Structure

```
qwen_agent/
├── agent.py              # Base Agent ABC (11KB) — streaming generator protocol
├── multi_agent_hub.py    # MultiAgentHub ABC — agent registry constraint layer
├── agents/               # 16+ agent types
│   ├── assistant.py      # RAG-integrated assistant (FnCallAgent subclass)
│   ├── fncall_agent.py   # Function-calling agent with Memory integration
│   ├── react_chat.py     # ReAct (Reasoning + Acting) agent
│   ├── group_chat.py     # Multi-agent conversation (14KB)
│   ├── group_chat_auto_router.py  # LLM-selected speaker routing
│   ├── group_chat_creator.py      # Dynamic group creation
│   ├── router.py         # 1-of-N agent dispatch
│   ├── tir_agent.py      # Tool-Integrated Reasoning (code interpreter)
│   ├── memo_assistant.py # Memory-augmented assistant
│   ├── virtual_memory_agent.py  # Persistent memory management
│   ├── dialogue_simulator.py    # Multi-turn dialogue generation
│   ├── human_simulator.py       # Human behavior simulation
│   ├── user_agent.py            # Human-in-the-loop agent
│   ├── article_agent.py         # Long-form content generation
│   ├── write_from_scratch.py    # Document authoring
│   ├── doc_qa/                  # Parallel document QA
│   ├── keygen_strategies/       # Keyword generation for retrieval
│   └── writing/                 # Writing-specialized agents
├── tools/                # 15+ tools with decorator-based registry
│   ├── base.py           # BaseTool ABC + @register_tool decorator + TOOL_REGISTRY
│   ├── code_interpreter.py  # Docker/Jupyter sandboxed execution (19KB)
│   ├── mcp_manager.py    # Production MCP client (22KB)
│   ├── doc_parser.py     # Multi-format document parsing (PDF/DOCX/PPTX/HTML)
│   ├── retrieval.py      # Embedding-based RAG retrieval
│   ├── storage.py        # Key-value persistent storage
│   ├── web_search.py     # Web search API integration
│   └── ...
├── llm/                  # LLM provider abstraction
│   ├── schema.py         # Message/ContentItem/FunctionCall (Pydantic models)
│   ├── base.py           # BaseChatModel ABC (35KB) — snapshot streaming
│   ├── function_calling.py  # Text-based function call parsing (✿FUNCTION✿/✿ARGS✿)
│   ├── oai.py            # OpenAI/DashScope/generic provider
│   ├── fncall_prompts/   # Per-model function calling prompt templates
│   └── ...
├── memory/
│   └── memory.py         # RAG-augmented Memory agent (extends Agent)
├── gui/                  # Gradio-based WebUI
└── utils/                # Tokenization, parallel execution, utilities
```

### 1.2 Core Design Patterns

#### Pattern 1: Streaming Generator Protocol (Universal)
Every agent's `_run()` method is a Python generator that yields `List[Message]` snapshots:

```python
class Agent(ABC):
    @abstractmethod
    def _run(self, messages: List[Message], lang: str = 'en', **kwargs) -> Iterator[List[Message]]:
        raise NotImplementedError

    def run(self, messages, **kwargs) -> Iterator[List[Message]]:
        # Preprocesses messages, injects system prompt, calls _run()
        for rsp in self._run(messages=new_messages, **kwargs):
            yield rsp

    def run_nonstream(self, messages, **kwargs) -> List[Message]:
        *_, last = self.run(messages, **kwargs)
        return last
```

**Snapshot streaming** (not delta): each yield contains the full response so far. Consumers always have complete state without reassembly.

#### Pattern 2: Decorator-Based Tool & LLM Registry
```python
TOOL_REGISTRY = {}

def register_tool(name, allow_overwrite=False):
    def decorator(cls):
        TOOL_REGISTRY[name] = cls
        cls.name = name
        return cls
    return decorator
```

Tools self-register at import time. Resolution is `TOOL_REGISTRY[name](cfg)`. Same pattern for LLM providers.

#### Pattern 3: Multimodal-Native Messages (Pydantic)
```python
class ContentItem(BaseModel):
    text: Optional[str] = None
    image: Optional[str] = None   # URL or base64
    file: Optional[str] = None
    audio: Optional[Union[str, dict]] = None
    video: Optional[Union[str, list]] = None

class Message(BaseModel):
    role: str  # system/user/assistant/function
    content: Union[str, List[ContentItem]]  # Multimodal!
    reasoning_content: Optional[Union[str, List[ContentItem]]] = None
    function_call: Optional[FunctionCall] = None
    extra: Optional[dict] = None
```

#### Pattern 4: Agent Composition via Sub-Agents
Agents can contain and delegate to other agents:
- `MemoAssistant` = `Assistant` + `VirtualMemoryAgent`
- `GroupChat` = N agents with speaker selection
- `Router` = LLM-driven 1-of-N dispatch

#### Pattern 5: Dual Function Calling (Native + Text-Based)
```python
class FnCallAgent(Agent):
    # Works even with models that DON'T support native function calling
    # Parses ✿FUNCTION✿/✿ARGS✿ markers from text output
    # OR uses <tool_call> XML tags
    # Transparent fallback
```

### 1.3 Agent Taxonomy

| Category | Agents | Purpose |
|----------|--------|---------|
| **Leaf Agents** | `Assistant`, `FnCallAgent`, `ReActChat`, `TIRAgent`, `VirtualMemoryAgent`, `DialogueRetrievalAgent` | Execute tasks directly |
| **Composite** | `MemoAssistant`, `GroupChat`, `GroupChatAutoRouter`, `Router` | Orchestrate sub-agents |
| **Utility** | `Memory`, `UserAgent`, `HumanSimulator`, `DialogueSimulator` | Support patterns |
| **Specialized** | `ArticleAgent`, `WriteFromScratch`, `DocQAAgent`, `ParallelDocQA` | Domain-specific |
| **Hub** | `MultiAgentHub` | Registry + constraints layer |

### 1.4 Multi-Agent Coordination

Three patterns:

1. **Router** (1-of-N): LLM selects which agent handles the request. Uses `Call: agent_name` prompt pattern.

2. **GroupChat** (N-of-N): Turn-based multi-agent conversation. Speaker selection: `auto` (LLM-routed via `GroupChatAutoRouter`), `round_robin`, `random`, or `manual`. Supports `@mention` routing. Messages are managed per-speaker with role remapping.

3. **MultiAgentHub**: ABC that enforces unique-named agent list constraints. Used as mixin for `GroupChat` and `Router`.

### 1.5 MCP Integration (mcp_manager.py — 22KB)

Production-grade MCP client:
- Multi-server connection pool (STDIO + SSE transports)
- Schema translation: MCP tool specs → Qwen `BaseTool.schema` format
- Dynamic tool discovery via `tools/list`
- Connection lifecycle management (startup, health, reconnect, shutdown)
- Tool routing: dispatches to correct MCP server by tool name
- Async/sync bridge for Qwen-Agent's sync `call()` interface

Configuration:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    },
    "web": {
      "url": "http://localhost:8080/sse"
    }
  }
}
```

### 1.6 Code Interpreter

Docker-based Jupyter kernel execution:
- Stateful: variables persist across calls within a conversation
- Captures stdout, stderr, display_data (images), execute_result
- Base64-encoded image output for multimodal responses
- Configurable timeout, resource limits
- Falls back to local execution if Docker unavailable
- File upload/download via mounted volumes

### 1.7 Memory System

Simple but elegant — Memory is itself an Agent:

```python
class Memory(Agent):
    def _run(self, messages, lang='en', **kwargs):
        rag_files = self.get_rag_files(messages)
        query = extract_text_from_message(messages[-1])
        # Keyword generation via keygen_strategies
        # Retrieval via registered retrieval tool
        content = self.function_map['retrieval'].call({'query': query, 'files': rag_files})
        yield [Message(role=ASSISTANT, content=content, name='memory')]
```

Key: uses LLM-based keyword generation strategies before retrieval for better recall.

---

## 2. AGENT-33 vs Qwen-Agent Feature Comparison

### 2.1 Comprehensive Feature Matrix

| Feature | AGENT-33 | Qwen-Agent | Winner |
|---------|----------|------------|--------|
| **Agent Definition** | Declarative JSON + runtime assembly | Class hierarchy with `_run()` override | Draw — different paradigms |
| **Agent Registry** | JSON-file discovery + search API | Import-time registration + `__init__.py` exports | **AGENT-33** (API + search) |
| **Tool Registration** | Protocol-based + entrypoint + MCP discovery | Decorator-based global registry | **AGENT-33** (3 channels) |
| **Tool Governance** | Pre-execute policy checks, allowlists, autonomy enforcement | None | **AGENT-33** |
| **Tool Schema Validation** | JSON Schema (Draft 7) on every call | `_verify_json_format_args` on demand | **AGENT-33** |
| **LLM Providers** | 22 providers, auto-registration from env | ~5 providers (DashScope, OpenAI, Azure, OpenVINO, local) | **AGENT-33** |
| **LLM Routing** | Effort-based scoring + prefix matching | Factory function with server detection | **AGENT-33** |
| **Streaming (Agent)** | ❌ Awaits complete responses | ✅ Generator-based snapshot streaming | **Qwen-Agent** |
| **Streaming (API)** | ✅ SSE proxy for chat endpoint | ✅ Native in all agents | Draw |
| **Multimodal Messages** | `content: str` only (multimodal module separate) | `content: str | List[ContentItem]` native | **Qwen-Agent** |
| **Function Call Fallback** | Native `tool_calls` only | Text-based parsing (✿FUNCTION✿/ReAct/XML) | **Qwen-Agent** |
| **Memory Architecture** | 3-tier: short/observation/long-term, pgvector, BM25+vector hybrid, progressive recall | Single Memory agent with retrieval tool, keyword generation | **AGENT-33** |
| **RAG Pipeline** | Hybrid BM25+vector RRF, diagnostics, injection sanitization | Embedding + keyword fallback, LLM-based keygen | **AGENT-33** |
| **Context Management** | Token budgeting, LLM summarization, message unwinding | Token truncation (middle removal) | **AGENT-33** |
| **Workflow Engine** | Full DAG: 11 actions, parallel/conditional, retry, checkpoints | None | **AGENT-33** |
| **Multi-Agent Chat** | Workflow DAG + handoffs | GroupChat with 4 speaker selection methods | **Qwen-Agent** (for chat patterns) |
| **Agent Routing** | Workflow-level `route` action | `Router` agent with LLM dispatch | Draw |
| **MCP Client** | Dual: SDK-based + HTTP JSON-RPC, SSRF protection | Single: mcp SDK + STDIO/SSE | **AGENT-33** |
| **MCP Server** | Stub/prototype | Not applicable | — |
| **Code Execution** | CLI subprocess adapter, stateless | Docker Jupyter kernel, stateful | **Qwen-Agent** |
| **Skills System** | SKILL.md/YAML, progressive disclosure L0/L1/L2, tool narrowing | None | **AGENT-33** |
| **Hooks/Middleware** | Pre/post at agent/tool/workflow levels | None | **AGENT-33** |
| **Reasoning Protocol** | 5-phase FSM: OBSERVE→PLAN→EXECUTE→VERIFY→LEARN | ReAct (Thought/Action/Observation) | Draw — different strengths |
| **Governance/Security** | Autonomy levels, leakage detection, prompt injection scanning | None | **AGENT-33** |
| **Handoff Protocol** | StateLedger context wipes (Swarm-inspired) | Message role remapping in GroupChat | **AGENT-33** |
| **Agent Archetypes** | Generic runtime with role configs | 16+ specialized agent classes | **Qwen-Agent** |
| **Document QA** | Memory ingestion + RAG pipeline | ParallelDocQA (chunked parallel processing) | Draw |
| **GUI** | React/Vite SPA (custom) | Gradio one-liner (`WebUI(bot).run()`) | Draw — different goals |
| **Observability** | Trace pipeline, failure taxonomy, metrics | None | **AGENT-33** |
| **Evaluation** | Golden tasks, metrics, regression gates | None | **AGENT-33** |
| **Multi-Tenancy** | Full: tenant_id on all models, JWT/API-key auth | None | **AGENT-33** |

### 2.2 Scorecard Summary

| Dimension | AGENT-33 | Qwen-Agent |
|-----------|:--------:|:----------:|
| Governance & Security | ★★★★★ | ★★ |
| Workflow Orchestration | ★★★★★ | ★★ |
| Memory & RAG | ★★★★★ | ★★★ |
| MCP Integration | ★★★★ | ★★★ |
| Skills & Composability | ★★★★ | ★★ |
| Multi-Provider Routing | ★★★★★ | ★★★ |
| Hooks & Extensibility | ★★★★ | ★★ |
| **Streaming UX** | **★★** | **★★★★★** |
| **Multimodal Messages** | **★★** | **★★★★** |
| **Agent Archetypes** | **★★** | **★★★★** |
| **Model Compatibility** | **★★★** | **★★★★★** |
| **Code Interpreter** | **★★** | **★★★★** |
| **Group Chat** | **★★** | **★★★★** |
| Observability | ★★★★ | ★ |
| Evaluation Gates | ★★★★ | ★ |
| Multi-Tenancy | ★★★★★ | ★ |

---

## 3. Key AGENT-33 Weaknesses (vs Qwen-Agent Strengths)

### 3.1 CRITICAL: No Streaming in Agent Loop

**Impact:** Users see nothing until the entire LLM response + tool execution completes. For multi-step tool loops, this can mean 30+ seconds of silence.

**Qwen-Agent approach:**
- Every `_run()` is a generator that `yield`s partial results
- Parent agents iterate child generators, streaming passthrough
- Snapshot model: each yield contains full state (not deltas)

**AGENT-33 gap:** `AgentRuntime.invoke()` and `tool_loop.run_iterative_tool_loop()` both await complete `LLMResponse` objects. The `_call_llm()` method returns a full response, not a generator.

**Recommendation:** Add `invoke_streaming()` to `AgentRuntime` and `run_iterative_tool_loop_streaming()` that yield `ToolLoopEvent` objects (token chunks, tool calls, tool results, reasoning steps). This is the **highest-impact UX improvement**.

### 3.2 HIGH: No Multimodal Content in Core Messages

**Impact:** Cannot pass images, audio, video through the agent loop. The `multimodal/` module exists but isn't wired into `ChatMessage`.

**Qwen-Agent approach:** `ContentItem` Pydantic model with exactly-one-of `text|image|file|audio|video` validation. `Message.content` accepts both `str` and `List[ContentItem]`.

**Recommendation:** Extend `ChatMessage.content` to `Union[str, list[ContentBlock]]` where `ContentBlock` is a discriminated union. Add serialization support to both `OpenAIProvider` and `OllamaProvider`.

### 3.3 HIGH: No Text-Based Function Calling Fallback

**Impact:** Models without native `tool_calls` support cannot use tools at all. This excludes many open models (older Llama, Mistral Instruct, etc.).

**Qwen-Agent approach:** `FnCallAgent` + `BaseFnCallModel` parse text-based tool patterns:
- `✿FUNCTION✿: name` / `✿ARGS✿: {json}` (Qwen native)
- `<tool_call>` XML tags
- ReAct `Action: name` / `Action Input: {json}`

**Recommendation:** Add a `TextToolCallParser` to `agents/tool_loop.py` that activates when `LLMResponse.tool_calls` is empty but the content matches known patterns. Register parsers per-model-family.

### 3.4 MEDIUM: No Pre-Built Agent Archetypes

**Impact:** Every agent is a generic `AgentRuntime` with different JSON definitions. No specialized execution patterns for common use cases.

**Qwen-Agent approach:** 16+ `Agent` subclasses with specialized `_run()` implementations.

**Recommendation:** Create thin archetype wrappers:
- `AssistantArchetype` — general-purpose with RAG (pre-configured memory integration)
- `CoderArchetype` — with code interpreter tool + persistent session
- `RouterArchetype` — LLM-driven 1-of-N dispatch
- `GroupChatArchetype` — multi-agent conversation room
These can be implemented as skill packs or configuration presets rather than class hierarchies.

### 3.5 MEDIUM: No Stateful Code Execution

**Impact:** Each code execution is stateless — no variable persistence between calls. Limits data analysis and iterative coding workflows.

**Qwen-Agent approach:** Docker Jupyter kernel with stateful sessions, image output capture, file I/O.

**Recommendation:** Enhance `CodeExecutor` with an optional Jupyter kernel adapter alongside the existing CLI adapter. Add session management (create/reuse/destroy) and multimodal output capture.

### 3.6 MEDIUM: No GroupChat-Style Multi-Agent

**Impact:** AGENT-33's multi-agent is workflow-centric (DAG steps) or handoff-centric (StateLedger). No support for dynamic multi-agent conversations where agents respond to each other.

**Qwen-Agent approach:** `GroupChat` with speaker selection (auto/round-robin/random/manual), `@mention` routing, message management per-speaker.

**Recommendation:** Implement a `GroupChatAction` workflow step that runs N agents in a conversation loop with configurable speaker selection. Wire through the existing workflow engine rather than creating a parallel orchestration layer.

---

## 4. Key AGENT-33 Strengths (to Preserve)

### 4.1 Governance Framework
Qwen-Agent has **zero** governance. AGENT-33's multi-layer governance (autonomy levels, tool governance, pre-execution checks, prompt injection detection, leakage scanning) is a massive differentiator for enterprise use.

### 4.2 Workflow Engine
Qwen-Agent has no workflow concept. AGENT-33's DAG-based workflow engine with 11 action types, conditional branching, parallel execution, sub-workflows, retry/timeout, and checkpointing is unique.

### 4.3 Memory Architecture
Qwen-Agent's memory is a single retrieval agent. AGENT-33's three-tier memory with pgvector, BM25+vector hybrid RRF, progressive recall (10x token savings), and retention policies is significantly more sophisticated.

### 4.4 Skills System
Qwen-Agent has no skills concept. AGENT-33's SKILL.md format, progressive disclosure, tool narrowing, and autonomy overrides are unique composability features.

### 4.5 Hooks & Observability
Qwen-Agent has no hook system and minimal observability. AGENT-33's pre/post hooks at agent/tool/workflow levels plus trace pipeline, failure taxonomy, and metrics are enterprise essentials.

### 4.6 Multi-Tenancy
Qwen-Agent is single-tenant. AGENT-33's full multi-tenancy with tenant_id on all models and JWT/API-key auth is required for production SaaS deployment.

---

## 5. Patterns Worth Adopting

### 5.1 Memory-as-Agent Pattern
Qwen-Agent's `Memory` extends `Agent` — it's a first-class agent that processes files and yields memory content. This pattern makes memory composable with agents (MemoAssistant = Assistant + Memory agent).

**AGENT-33 adaptation:** Could make progressive recall available as a "memory agent" that participates in agent conversations, rather than only as a context injection mechanism.

### 5.2 Agent-as-Tool Pattern
In Qwen-Agent, agents can be registered as tools for other agents. A `Router` can delegate to any agent by name.

**AGENT-33 adaptation:** The workflow `invoke-agent` action already does this, but making agents available as tools in the `ToolRegistry` would enable more dynamic composition.

### 5.3 Keyword Generation Strategies
Qwen-Agent uses LLM-based keyword generation before retrieval (via `keygen_strategies/`). This improves retrieval recall for complex queries.

**AGENT-33 adaptation:** Add an LLM-based query expansion step in the RAG pipeline before hybrid search. Could significantly improve retrieval quality.

### 5.4 Snapshot Streaming Model
Each yield contains the full response so far (not deltas). Simplifies consumer code — no reassembly needed.

**AGENT-33 adaptation:** When implementing streaming, consider snapshot model for the agent loop and delta model only for the SSE API layer.

### 5.5 Configuration-Driven Agent Instantiation
Qwen-Agent's dict-based config (`{'model': '...', 'tools': [...], 'system_message': '...'}`) enables easy programmatic agent creation.

**AGENT-33 adaptation:** Already has JSON definition files. Could add a `from_dict()` factory for runtime agent creation without files.

---

## 6. Prioritized Recommendations

### Phase A: Critical UX (Highest Impact)

| # | Item | Effort | Impact | Description |
|---|------|--------|--------|-------------|
| A1 | Streaming Agent Loop | L (large) | ★★★★★ | Add `AsyncGenerator`-based streaming to `AgentRuntime.invoke()` and `tool_loop`. Yield `ToolLoopEvent` with token chunks, tool calls, tool results. |
| A2 | Multimodal ContentBlock | M (medium) | ★★★★ | Extend `ChatMessage.content` to `Union[str, list[ContentBlock]]`. Update provider serialization. |
| A3 | Text-Based Tool Parsing | M (medium) | ★★★★ | Add `TextToolCallParser` for ReAct/XML/marker-based function calling fallback. |

### Phase B: Agent Capabilities

| # | Item | Effort | Impact | Description |
|---|------|--------|--------|-------------|
| B1 | GroupChat Action | M (medium) | ★★★ | Implement `group-chat` workflow action with speaker selection strategies. |
| B2 | Agent Archetypes | S (small) | ★★★ | Create configuration presets for common patterns (Assistant, Coder, Router, GroupChat). |
| B3 | LLM Query Expansion | S (small) | ★★★ | Add LLM-based keyword generation step in RAG pipeline before hybrid search. |
| B4 | Agent-as-Tool Bridge | S (small) | ★★ | Register agents as tools in ToolRegistry for dynamic composition. |

### Phase C: Code Execution

| # | Item | Effort | Impact | Description |
|---|------|--------|--------|-------------|
| C1 | Jupyter Kernel Adapter | L (large) | ★★★ | Add `JupyterAdapter` to `execution/adapters/` with stateful sessions and image output. |
| C2 | Code Interpreter Tool | M (medium) | ★★★ | Wrap Jupyter adapter as a registered tool with Docker sandbox support. |

### Phase D: Future Considerations

| # | Item | Effort | Impact | Description |
|---|------|--------|--------|-------------|
| D1 | MCP Server (Full) | L (large) | ★★ | Complete the MCP server stub to expose AGENT-33 tools to external agents. |
| D2 | GUI Toolkit | L (large) | ★★ | Consider Gradio integration for rapid prototyping alongside the React SPA. |
| D3 | Model-Specific FnCall Prompts | M (medium) | ★★ | Per-model function calling prompt templates (like Qwen-Agent's `fncall_prompts/`). |

---

## 7. Architectural Alignment Notes

### 7.1 Where Both Frameworks Agree
- **Messages as universal interface** — both use message lists as the core API
- **OpenAI-compatible format** — both serialize to OpenAI's chat format
- **Tool registration pattern** — both use name-based resolution from registries
- **Agent composition** — both support agents delegating to other agents
- **RAG integration** — both have built-in document retrieval capabilities

### 7.2 Fundamental Paradigm Difference
- **Qwen-Agent:** Class hierarchy with `_run()` override. Agents are Python classes.
- **AGENT-33:** Definition-driven with runtime assembly. Agents are JSON configs + generic runtime.

AGENT-33's approach is more enterprise-friendly (declarative, configurable, auditable) while Qwen-Agent's is more developer-friendly (subclass and customize). **Both are valid — they serve different use cases. AGENT-33 should not abandon its definition-driven approach.**

### 7.3 Integration Opportunity
The `core/orchestrator/QWEN_CODE_TOOL_PROTOCOL.md` already references Qwen-Agent's code tool protocol. This suggests AGENT-33 was designed to integrate with Qwen-Agent at the tool level. The MCP client implementation in `tools/mcp_client.py` could connect to a Qwen-Agent instance running as an MCP server.

---

## 8. Appendix: Qwen-Agent File Inventory

| File | Size | Key Contents |
|------|------|--------------|
| `agent.py` | 11KB | `Agent` ABC, `BasicAgent`, streaming generator protocol |
| `multi_agent_hub.py` | 1KB | `MultiAgentHub` ABC with agent list constraints |
| `agents/assistant.py` | 5KB | RAG-integrated `Assistant` (extends `FnCallAgent`) |
| `agents/fncall_agent.py` | 5KB | Function-calling `FnCallAgent` with Memory integration |
| `agents/group_chat.py` | 14KB | `GroupChat` with 4 speaker selection methods |
| `agents/router.py` | 4KB | LLM-driven 1-of-N agent dispatch |
| `agents/react_chat.py` | ~3KB | ReAct reasoning agent |
| `agents/tir_agent.py` | ~2KB | Tool-Integrated Reasoning (code interpreter) |
| `agents/memo_assistant.py` | ~3KB | Memory-augmented assistant |
| `agents/virtual_memory_agent.py` | ~4KB | Persistent memory management |
| `tools/base.py` | 7KB | `BaseTool` ABC, `@register_tool`, `TOOL_REGISTRY`, `BaseToolWithFileAccess` |
| `tools/code_interpreter.py` | 19KB | Docker/Jupyter sandboxed Python execution |
| `tools/mcp_manager.py` | 22KB | Production MCP client: multi-server, STDIO/SSE, schema translation |
| `tools/doc_parser.py` | ~8KB | PDF/DOCX/PPTX/HTML/CSV parsing with chunking |
| `tools/retrieval.py` | ~5KB | Embedding-based semantic retrieval |
| `llm/schema.py` | 5KB | `Message`, `ContentItem`, `FunctionCall` Pydantic models |
| `llm/base.py` | 35KB | `BaseChatModel` ABC: snapshot streaming, token management, retry |
| `llm/function_calling.py` | ~10KB | Text-based function call detection (✿FUNCTION✿, XML, ReAct) |
| `llm/oai.py` | ~8KB | OpenAI/DashScope/generic providers |
| `memory/memory.py` | 6KB | Memory agent with RAG retrieval + keyword generation |

---

## 9. Research Methodology

1. **Live source code** fetched via GitHub API (`github-mcp-server-get_file_contents`) for all critical files
2. **AGENT-33 source code** read directly from `engine/src/agent33/` via filesystem
3. **Cross-referenced** with AGENT-33's `core/orchestrator/QWEN_CODE_TOOL_PROTOCOL.md` and `CLAUDE.md`
4. **Pattern-level comparison** rather than line-level to identify strategic adoption opportunities
5. **Validated findings** against actual imports, class hierarchies, and method signatures

---

*This document is part of AGENT-33's competitive intelligence research. It should be updated as either framework evolves.*
