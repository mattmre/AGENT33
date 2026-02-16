---
title: "Session 17: AWM Tier 1 Adaptation Detailed Analysis"
date: 2026-02-15
session: 17
type: research
status: complete
---

# Session 17: AWM Tier 1 Adaptation Detailed Analysis

## Overview

This document provides a detailed implementation analysis for the four AWM (Agent World Model) Tier 1 adaptations identified in the AWM analysis (`docs/research/agent-world-model-analysis.md`). Each adaptation is analyzed for current state, proposed implementation, breaking changes, and estimated test count.

The recommended implementation order is **A4 -> A1 -> A2 -> A3**, based on dependency relationships and incremental value delivery.

## A1: MCP Interface Interop Bridge

### Current State

- `AdapterType.MCP` enum value exists in the tool adapter type definitions but is entirely unused
- Zero MCP protocol handling anywhere in the codebase
- Tools are currently registered via Python code or JSON Schema definitions
- The ToolRegistry supports dynamic tool registration, which MCP can leverage
- The governance/allowlist system works on tool names, which MCP tools would need to respect

### Proposed Implementation

#### New File: `tools/mcp_bridge.py`

**MCPServerConnection** -- Manages connection to a single MCP server:

```python
class MCPServerConnection:
    def __init__(self, name: str, url: str, timeout: float = 30.0):
        ...

    async def connect(self) -> None:
        """Establish connection and discover available tools."""

    async def disconnect(self) -> None:
        """Gracefully close the connection."""

    async def list_tools(self) -> list[MCPToolSpec]:
        """Query server for available tools and their schemas."""

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Execute a tool call on the remote MCP server."""

    async def health_check(self) -> bool:
        """Verify the MCP server is responsive."""
```

**MCPToolAdapter** -- Wraps an MCP tool as a standard AGENT-33 Tool:

```python
class MCPToolAdapter:
    """Adapts an MCP server tool to the AGENT-33 Tool protocol.

    Implements SchemaAwareTool so MCP tools flow through
    validated_execute(), governance checks, and the tool loop
    identically to native tools.
    """

    def __init__(self, connection: MCPServerConnection, tool_spec: MCPToolSpec):
        ...

    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...

    @property
    def input_schema(self) -> dict: ...

    async def execute(self, **kwargs: Any) -> Any:
        """Delegate execution to the MCP server."""

    async def validated_execute(self, **kwargs: Any) -> Any:
        """Validate input against schema, then delegate."""
```

**MCPBridge** -- Top-level manager for all MCP server connections:

```python
class MCPBridge:
    def __init__(self, tool_registry: ToolRegistry, config: Settings):
        ...

    async def initialize(self) -> None:
        """Connect to all configured MCP servers, discover tools, register them."""

    async def shutdown(self) -> None:
        """Disconnect from all MCP servers."""

    def get_mcp_tools(self) -> list[MCPToolAdapter]:
        """Return all registered MCP tools."""
```

#### Config Additions

```python
# In config.py
mcp_servers: list[str] = []          # URLs of MCP servers
mcp_timeout_seconds: float = 30.0    # Per-call timeout
mcp_auto_discover: bool = True       # Auto-discover tools on connect
```

#### Integration Pattern

MCP tools register as standard `Tool` instances in the existing `ToolRegistry`. This means:
- They flow through the existing governance/allowlist system
- They work with `validated_execute()` and JSON Schema validation
- They participate in the tool loop naturally
- They appear in skill injection's `resolve_tool_context()`

#### Breaking Changes

None. This is purely additive. No existing interfaces change. MCP is opt-in via configuration.

#### Estimated Tests: 30-40

- MCPServerConnection: connect, disconnect, list_tools, call_tool, health_check, timeout, reconnect (10-12)
- MCPToolAdapter: name, description, schema, execute, validated_execute, error handling (8-10)
- MCPBridge: initialize, shutdown, multi-server, tool registration, auto-discover toggle (8-10)
- Integration: MCP tool through governance, MCP tool in tool loop, MCP tool in skill context (4-8)

## A2: Database-Backed Verification

### Current State

- All evaluation data is stored in-memory (Python dicts/lists)
- No database interaction in the evaluation subsystem
- Verification is pass/fail based on external assertion functions
- Golden tasks (GT-01..GT-07) define expected outcomes as string descriptions
- No ability to verify results by querying application state in a database

### Proposed Implementation

#### New Model: VerificationSpec

```python
class ComparisonMode(str, Enum):
    EXACT = "exact"           # Result must exactly match expected
    CONTAINS = "contains"     # Result must contain expected as substring
    ROW_COUNT = "row_count"   # Result row count must match expected integer
    NOT_EMPTY = "not_empty"   # Result must have at least one row
    REGEX = "regex"           # Result must match expected as regex pattern
    JSON_SUBSET = "json_subset"  # Result JSON must be superset of expected

class VerificationSpec(BaseModel):
    name: str                          # Human-readable name
    query: str                         # SQL query to execute
    expected: str                      # Expected result (interpretation depends on mode)
    comparison_mode: ComparisonMode    # How to compare
    database: str = "default"          # Which database to query
    timeout_seconds: float = 10.0      # Query timeout
```

#### New Class: DatabaseVerifier

```python
class DatabaseVerifier:
    def __init__(self, db_connections: dict[str, AsyncConnection]):
        ...

    async def verify(self, spec: VerificationSpec) -> VerificationResult:
        """Execute the verification query and compare against expected."""

    async def verify_all(self, specs: list[VerificationSpec]) -> list[VerificationResult]:
        """Execute all verification specs, return results."""

class VerificationResult(BaseModel):
    spec_name: str
    passed: bool
    actual_value: str | None
    expected_value: str
    error_message: str | None
    duration_ms: int
```

#### Golden Task Extension

```python
class GoldenTaskDef(BaseModel):
    # ... existing fields ...
    verification_specs: list[VerificationSpec] = []  # NEW, optional, default empty
```

The `verification_specs` field is additive with an empty default list, so existing GT-01..GT-07 definitions remain unchanged.

#### New Golden Tasks

- **GT-08**: Task that creates a database record, verified by querying the record exists
- **GT-09**: Task that updates a record, verified by querying the new value
- **GT-10**: Task that should NOT modify certain records, verified by row_count check

#### Breaking Changes

Minimal. The `verification_specs` field has a default empty list, so all existing code works without modification. The `DatabaseVerifier` is only instantiated when verification specs are present.

#### Estimated Tests: 35-45

- VerificationSpec model: validation, comparison modes, defaults (6-8)
- DatabaseVerifier: each comparison mode (exact, contains, row_count, not_empty, regex, json_subset), timeout, connection error (10-14)
- verify_all: multiple specs, partial failure, all pass, all fail (4-6)
- GoldenTaskDef extension: backward compat, with specs, serialization (4-6)
- Integration: GT-08..GT-10 with DatabaseVerifier, multi-trial with DB verification (6-8)
- Edge cases: SQL injection prevention, large result sets, null handling (5-7)

## A3: Multi-Turn Evaluation Scenarios

### Current State

- GT-01 through GT-07 are single-action documentation tasks
- No tool calling in any golden task
- No multi-turn conversation evaluation
- No way to measure tool-use accuracy or turns-to-completion
- The iterative tool loop (P0) exists but is not exercised by evaluation

### Proposed Implementation

#### New Models

```python
class ToolCallExpectation(BaseModel):
    tool_name: str                     # Expected tool to be called
    required: bool = True              # Must this tool be called?
    expected_arguments: dict | None = None  # If set, validate arguments
    order: int | None = None           # If set, enforce call ordering

class MultiTurnScenario(BaseModel):
    scenario_id: str                   # e.g., "GT-08"
    description: str
    initial_message: str               # First user message
    expected_tool_calls: list[ToolCallExpectation]
    max_turns: int = 10
    verification_specs: list[VerificationSpec] = []  # From A2
    success_criteria: str              # Natural language description
    tags: list[str] = []
```

#### New Class: MultiTurnEvaluator

```python
class MultiTurnEvaluator:
    def __init__(
        self,
        agent_runtime: AgentRuntime,
        tool_registry: ToolRegistry,
        db_verifier: DatabaseVerifier | None = None,
    ):
        ...

    async def evaluate(
        self,
        scenario: MultiTurnScenario,
        agent_config: AgentExperimentConfig,
    ) -> MultiTurnResult:
        """Run a multi-turn scenario and evaluate the outcome."""

    def _check_tool_calls(
        self,
        actual: list[ToolCallRecord],
        expected: list[ToolCallExpectation],
    ) -> ToolCallCheckResult:
        """Compare actual tool calls against expectations."""

class MultiTurnResult(BaseModel):
    scenario_id: str
    turns: int                         # Actual turns taken
    tool_calls_made: list[ToolCallRecord]
    tool_call_accuracy: float          # % of expected calls made correctly
    success: bool                      # Overall success
    verification_results: list[VerificationResult]  # From A2
    duration_ms: int
    tokens_used: int
```

#### New Golden Tasks (Multi-Turn)

| Task | Description | Tools | Turns |
|------|-------------|-------|-------|
| GT-08 | Search for information and summarize | web_fetch | 2-3 |
| GT-09 | Read a file, transform, write output | file_ops (read + write) | 3-4 |
| GT-10 | Execute shell command and interpret results | shell | 2-3 |
| GT-11 | Multi-step: search, analyze, write report | web_fetch + file_ops | 4-6 |
| GT-12 | Debug: read file, find bug, apply fix | file_ops (read + write) | 3-5 |
| GT-13 | Data pipeline: fetch, transform, validate | web_fetch + shell + file_ops | 5-8 |
| GT-14 | Research: multiple searches, synthesize | web_fetch (multiple) | 4-6 |

#### New Metrics

| Metric | Name | Description |
|--------|------|-------------|
| M-06 | Tool-Use Accuracy | % of expected tool calls made correctly (name + arguments) |
| M-07 | Multi-Turn Success Rate | % of multi-turn scenarios completed successfully |
| M-08 | Avg Turns to Completion | Average number of turns across successful scenarios |

#### Benefits from A2

Multi-turn scenarios can use `VerificationSpec` from A2 to verify final state:
- GT-09 (file transform): Verify output file contents via filesystem query
- GT-12 (debug): Verify the bug fix was applied correctly
- GT-13 (data pipeline): Verify pipeline output matches expected schema

#### Breaking Changes

Minimal. New golden tasks GT-08..GT-14 do not conflict with existing GT-01..GT-07. New metrics M-06..M-08 are additive. The `MultiTurnEvaluator` is a new class that integrates with existing `AgentRuntime` and `ToolRegistry`.

#### Estimated Tests: 45-55

- ToolCallExpectation: validation, ordering, optional arguments (4-6)
- MultiTurnScenario: validation, defaults, tags (4-6)
- MultiTurnEvaluator: single-turn, multi-turn, tool call checking, timeout, max turns (12-16)
- _check_tool_calls: exact match, partial match, order enforcement, missing calls, extra calls (8-10)
- MultiTurnResult: computation, edge cases (4-6)
- New golden tasks: GT-08..GT-14 scenario definitions and basic execution (7-8)
- Integration: multi-turn + multi-trial, multi-turn + DB verification (4-6)

## A4: Optional Tiktoken Integration

### Current State

Token counting is performed in 3 locations using 2 different heuristics:

1. **ContextManager** (`agents/context_manager.py`): Uses `len(text) / 3.5` (characters divided by 3.5)
2. **TokenAwareChunker** (`memory/ingestion.py`): Uses `len(text.split()) * 1.3` (word count times 1.3)
3. **ShortTermMemory** (`memory/short_term.py`): Uses `len(text) / 3.5` (same as ContextManager)

These heuristics diverge:
- For the text "Hello, how are you doing today?": chars/3.5 = 8.6, words*1.3 = 7.8, tiktoken = 8
- For code snippets: chars/3.5 significantly overestimates, words*1.3 underestimates

### Proposed Implementation

#### New File: `agents/tokenizer.py`

```python
class TokenCounter(Protocol):
    """Protocol for token counting implementations."""

    def count(self, text: str) -> int:
        """Count tokens in the given text."""
        ...

    def count_messages(self, messages: list[dict]) -> int:
        """Count tokens in a list of chat messages (includes overhead)."""
        ...

    @property
    def name(self) -> str:
        """Human-readable name of the counter implementation."""
        ...


class EstimateTokenCounter:
    """Heuristic-based token counter (no external dependencies).

    Uses chars/3.5 as the default heuristic, matching the existing
    ContextManager behavior.
    """

    def __init__(self, chars_per_token: float = 3.5, message_overhead: int = 4):
        self._chars_per_token = chars_per_token
        self._message_overhead = message_overhead

    def count(self, text: str) -> int:
        return max(1, int(len(text) / self._chars_per_token))

    def count_messages(self, messages: list[dict]) -> int:
        total = 0
        for msg in messages:
            total += self._message_overhead
            for value in msg.values():
                if isinstance(value, str):
                    total += self.count(value)
        return total + 3  # reply priming

    @property
    def name(self) -> str:
        return "estimate"


class TiktokenCounter:
    """Tiktoken-based token counter (requires tiktoken package).

    Provides accurate token counts for OpenAI-compatible models.
    Falls back to EstimateTokenCounter if tiktoken is not installed.
    """

    def __init__(self, model: str = "gpt-4o", fallback: TokenCounter | None = None):
        try:
            import tiktoken
            self._encoding = tiktoken.encoding_for_model(model)
            self._available = True
        except ImportError:
            self._encoding = None
            self._available = False
            self._fallback = fallback or EstimateTokenCounter()

    def count(self, text: str) -> int:
        if self._available:
            return len(self._encoding.encode(text))
        return self._fallback.count(text)

    def count_messages(self, messages: list[dict]) -> int:
        if not self._available:
            return self._fallback.count_messages(messages)
        total = 0
        for msg in messages:
            total += 4  # message overhead
            for key, value in msg.items():
                if isinstance(value, str):
                    total += len(self._encoding.encode(value))
                if key == "name":
                    total += -1  # name token adjustment
        return total + 3  # reply priming

    @property
    def name(self) -> str:
        return "tiktoken" if self._available else f"tiktoken-fallback({self._fallback.name})"
```

#### Factory Function

```python
def create_token_counter(
    prefer_tiktoken: bool = True,
    model: str = "gpt-4o",
) -> TokenCounter:
    """Create the best available token counter.

    If prefer_tiktoken is True and tiktoken is installed, returns TiktokenCounter.
    Otherwise returns EstimateTokenCounter.
    """
    if prefer_tiktoken:
        counter = TiktokenCounter(model=model)
        if counter._available:
            return counter
    return EstimateTokenCounter()
```

#### Refactoring Existing Code

**ContextManager** (`agents/context_manager.py`):
```python
# Before:
def _estimate_tokens(self, text: str) -> int:
    return max(1, int(len(text) / 3.5))

# After:
def __init__(self, ..., token_counter: TokenCounter | None = None):
    self._token_counter = token_counter or EstimateTokenCounter()

def _estimate_tokens(self, text: str) -> int:
    return self._token_counter.count(text)
```

**TokenAwareChunker** (`memory/ingestion.py`):
```python
# Before:
def _estimate_tokens(self, text: str) -> int:
    return int(len(text.split()) * 1.3)

# After:
def __init__(self, ..., token_counter: TokenCounter | None = None):
    self._token_counter = token_counter or EstimateTokenCounter()

def _estimate_tokens(self, text: str) -> int:
    return self._token_counter.count(text)
```

**ShortTermMemory** (`memory/short_term.py`):
```python
# Before:
def _count_tokens(self, text: str) -> int:
    return max(1, int(len(text) / 3.5))

# After:
def __init__(self, ..., token_counter: TokenCounter | None = None):
    self._token_counter = token_counter or EstimateTokenCounter()

def _count_tokens(self, text: str) -> int:
    return self._token_counter.count(text)
```

#### Optional Dependency

In `pyproject.toml`:
```toml
[project.optional-dependencies]
tiktoken = ["tiktoken>=0.7,<1"]
dev = [
    # ... existing dev deps ...
    "tiktoken>=0.7,<1",
]
```

#### Config Addition

```python
# In config.py
prefer_tiktoken: bool = True  # Use tiktoken if available
```

#### Breaking Changes

None. The `TokenCounter` protocol accepts the existing heuristic as the default implementation. All constructors default to `EstimateTokenCounter` when no counter is provided. Tiktoken is lazy-imported with graceful fallback.

#### Estimated Tests: 25-35

- EstimateTokenCounter: count, count_messages, edge cases (empty, long text, special chars) (6-8)
- TiktokenCounter: count, count_messages, fallback when not installed, model selection (8-10)
- create_token_counter: prefer_tiktoken True/False, tiktoken available/unavailable (4-6)
- Integration: ContextManager with TokenCounter, TokenAwareChunker with TokenCounter, ShortTermMemory with TokenCounter (4-6)
- Backward compatibility: existing tests pass without providing TokenCounter (3-5)

## Recommended Implementation Order

### A4 (Tiktoken) -> A1 (MCP) -> A2 (DB Verification) -> A3 (Multi-Turn)

**Rationale**:

1. **A4 first**: Smallest scope, no external dependencies, foundational for accurate token counting in all other adaptations. Every subsequent adaptation benefits from accurate token counts.

2. **A1 second**: Independent of evaluation changes, enables external tool integration that A3's multi-turn scenarios can leverage.

3. **A2 third**: Adds database verification capability that A3's multi-turn scenarios depend on for state verification.

4. **A3 last**: Depends on A2 (verification specs), benefits from A1 (MCP tools as evaluation targets), and A4 (accurate token counting for multi-turn conversations).

### Total Estimated New Tests: 135-175

| Adaptation | Min Tests | Max Tests |
|-----------|-----------|-----------|
| A1: MCP Bridge | 30 | 40 |
| A2: DB Verification | 35 | 45 |
| A3: Multi-Turn Eval | 45 | 55 |
| A4: Tiktoken | 25 | 35 |
| **Total** | **135** | **175** |
