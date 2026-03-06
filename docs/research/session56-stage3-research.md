# Session 56: Stage 3 Implementation Research

Last updated: 2026-03-06

## Overview

Research findings for Stage 3 refinement work across 4 areas:
- Phase 25: WebSocket workflow status streaming
- Phase 28: LLMGuard/Garak security adapter completion
- Phase 38: Token-level LLM streaming with tool_call reassembly
- Phase 43: MCP resources and auth module

## Phase 25 Stage 3: WebSocket Workflow Status

### Current State
- No real-time push exists — workflow status is only available after completion via history
- Three SSE reference implementations exist (operations_hub, agent stream, observation stream)
- No WebSocket infrastructure exists — this would be the first WS endpoint
- NATS bus is connected at startup, pub/sub works
- Hook system fires `workflow.step.pre`/`workflow.step.post` during execution
- Frontend `WorkflowStatusNode` already handles running/success/failed/pending statuses

### Architecture Decision
- Use Starlette's built-in WebSocket (zero new dependencies)
- WorkflowWSManager with per-workflow subscriptions and cleanup
- Optional event_sink parameter on WorkflowExecutor
- 8 event types: workflow_started, step_started, step_completed, step_failed, step_skipped, step_retrying, workflow_completed, workflow_failed
- Client protocol: subscribe/unsubscribe/ping over JSON WebSocket

## Phase 28 Stage 3: LLMGuard/Garak Adapters

### Current State
- LLMGuardAdapter and GarakAdapter exist as stubs returning empty lists
- LLMSecurityScanner is fully implemented with regex-based detection
- SecurityScanService has run lifecycle management
- SQLite persistence, SARIF conversion, and dedup all implemented

### Architecture Decision
- LLM Guard: Replace stubs with real scan_prompt/scan_output calls using PromptInjection, Toxicity, InvisibleText (input) and Sensitive, NoRefusal (output) scanners
- Garak: Replace stub with probe discovery and execution using promptinject, encoding, dan, leakreplay modules
- Both libraries as optional dependencies in `security-scanning` extras group
- Score-to-severity mapping: ≥0.9=CRITICAL, ≥0.7=HIGH, ≥0.5=MEDIUM, else LOW
- All errors caught and logged, never crash caller

## Phase 38 Stage 2: Token-Level Streaming

### Current State
- Phase 38a complete: loop-level events work but LLM calls are blocking (router.complete())
- LLMStreamChunk.delta_tool_calls exists but is NEVER populated
- OpenAI stream_complete() ignores delta.tool_calls
- Ollama stream_complete() doesn't send tools in streaming body

### Architecture Decision
- Add ToolCallDelta dataclass for incremental tool call fragments
- Add ToolCallAssembler to reconstruct complete ToolCalls from streaming deltas
- Parse tool_call deltas in OpenAI (SSE) and Ollama (NDJSON) providers
- Add "llm_token" event type for real-time content streaming
- Modify run_stream() to use stream_complete() with fallback to complete()
- OpenAI sends tool_calls as index-based incremental deltas; Ollama sends full objects

## Phase 43 Stage 2: MCP Resources & Auth

### Current State
- MCP server has 7 tools exposed via MCPServiceBridge
- MCPServiceBridge is NEVER wired in main.py lifespan (dead code at runtime!)
- No MCP resources registered (only tools)
- No scope enforcement on MCP routes
- MCP SDK ≥1.0.0 installed with Resource/ResourceTemplate support

### Architecture Decision
- Wire MCPServiceBridge in main.py lifespan (critical fix)
- Add 4 static resources: agents, tools, skills, status
- Add 3 resource templates: agents/{name}, tools/{name}, skills/{name}
- URI scheme: agent33:// prefix
- Auth: per-operation scope checking (agents:read, tools:execute, agents:invoke)
- Scope enforcement on SSE/messages endpoints via require_scope()

## Risk Matrix

| Phase | Risk | Key Mitigation |
|-------|------|----------------|
| 25 | WebSocket auth bypass | Inline JWT validation before accept() |
| 25 | Connection leak | Cleanup in finally block + periodic ping |
| 28 | False negatives | Log scanner errors, return informational finding on error |
| 28 | Heavy transitive deps | Optional dependency group, lazy imports |
| 38 | Tool_call reassembly | ToolCallAssembler state machine, finalize on finish_reason |
| 38 | Breaking LLMStreamChunk | delta_tool_calls never populated, safe to change type |
| 43 | Bridge never wired | Fix in main.py lifespan (highest priority) |
| 43 | SDK version mismatch | Guard resource handlers with hasattr checks |
