# Research: Event Hooks, MCP Registries, and Plugin Architectures for AI Agent Platforms

**Date**: 2026-02-23
**Scope**: Lifecycle hooks, MCP connector registries, plugin SDKs, circuit breakers, health monitoring, connector auth
**Method**: Web search + direct code extraction from 15+ repositories

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Repository Index](#2-repository-index)
3. [Lifecycle Hook Frameworks](#3-lifecycle-hook-frameworks)
4. [MCP Server Registries & Connection Management](#4-mcp-server-registries--connection-management)
5. [Connector Authentication Patterns](#5-connector-authentication-patterns)
6. [Circuit Breakers & Rate Limiting](#6-circuit-breakers--rate-limiting)
7. [Health Monitoring & Degradation](#7-health-monitoring--degradation)
8. [Plugin SDK / Developer Experience](#8-plugin-sdk--developer-experience)
9. [Synthesis: Patterns for AGENT-33](#9-synthesis-patterns-for-agent-33)
10. [Sources](#10-sources)

---

## 1. Executive Summary

This research surveyed 15+ actively-maintained repositories (1,000+ stars, commits within January-February 2026) implementing event hook systems, MCP connector registries, and plugin architectures for AI agent platforms. The findings reveal strong convergence around several patterns:

**Lifecycle Hooks**: Two dominant models emerged -- (a) the observer/callback model (OpenAI Agents SDK, CrewAI) where hook classes are subclassed and registered on agents, and (b) the middleware chain model (Microsoft Agent Framework, Semantic Kernel) where interceptors form a pipeline with `next()` delegation. Microsoft Agent Framework's 3-tier middleware (agent/function/chat) is the most sophisticated implementation found.

**MCP Registries**: The official `modelcontextprotocol/registry` (6.5k stars, Go) provides namespace-validated publishing with GitHub OAuth. The `agentic-community/mcp-gateway-registry` adds enterprise OAuth2 (3-legged + M2M), semantic tool discovery, and virtual MCP server aggregation. The MCP Python SDK (21.8k stars) provides `ClientSession` with ping-based health checks and StreamableHTTP transport with session resumability.

**Circuit Breakers**: No agent framework implements circuit breakers natively. The pattern must be adopted from standalone libraries (PyBreaker, aiobreaker, circuitbreaker). PyBreaker (655 stars) provides the most complete implementation with Redis-backed state, async support, configurable exclusions, and listener events.

**Plugin SDKs**: Microsoft Agent Framework offers the most complete developer experience with decorators (`@tool`, `@agent_middleware`, `@function_middleware`), class-based and function-based authoring, agent-level vs run-level registration scopes, and termination/override semantics. Semantic Kernel's `@kernel_function` + FilterTypes enum is mature but less flexible.

---

## 2. Repository Index

| Repository | Stars | Last Commit | Language | Key Patterns |
|---|---|---|---|---|
| [openai/openai-agents-python](https://github.com/openai/openai-agents-python) | 19.1k | Feb 2026 | Python | Lifecycle hooks, MCP integration, guardrails |
| [microsoft/agent-framework](https://github.com/microsoft/agent-framework) | 7.4k | Feb 20, 2026 | Python/.NET | 3-tier middleware, checkpoints, MCP |
| [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) | 27.3k | Feb 2026 | Python/C#/Java | Filter system, plugin arch, AI connectors |
| [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) | 21.8k | Feb 2026 | Python | Client session, transport, health ping |
| [modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry) | 6.5k | Feb 10, 2026 | Go | Server publishing, namespace validation |
| [agentic-community/mcp-gateway-registry](https://github.com/agentic-community/mcp-gateway-registry) | 450 | Feb 2026 | Python | OAuth2, semantic discovery, virtual servers |
| [microsoft/autogen](https://github.com/microsoft/autogen) | 54.7k | Feb 2026 | Python/.NET | Event-driven agents, extensions API |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | 25k | Feb 19, 2026 | Python | Graph workflows, checkpoints, memory |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | 44.5k | Feb 2026 | Python | Tool hooks, Crews + Flows duality |
| [n8n-io/n8n](https://github.com/n8n-io/n8n) | 176k | Feb 23, 2026 | TypeScript | Credential system, OAuth2, 400+ connectors |
| [windmill-labs/windmill](https://github.com/windmill-labs/windmill) | 15.9k | Feb 2026 | Rust/Svelte | Resource types, OAuth, job queue |
| [ravitemer/mcp-hub](https://github.com/ravitemer/mcp-hub) | 441 | Feb 2026 | TypeScript | Server lifecycle, health SSE, reconnection |
| [danielfm/pybreaker](https://github.com/danielfm/pybreaker) | 655 | Jan 2025 | Python | Circuit breaker, Redis state, listeners |
| [langchain-ai/langgraph-bigtool](https://github.com/langchain-ai/langgraph-bigtool) | 515 | Jun 2025 | Python | Dynamic tool registry, semantic retrieval |
| [airbytehq/airbyte-python-cdk](https://github.com/airbytehq/airbyte-python-cdk) | N/A | Feb 2026 | Python | OAuth2/refresh token auth, declarative connectors |

---

## 3. Lifecycle Hook Frameworks

### 3.1 OpenAI Agents SDK -- Observer/Callback Model (19.1k stars)

The OpenAI Agents SDK implements lifecycle hooks via two base classes that developers subclass:

**RunHooksBase** -- receives callbacks for the entire agent run:

```python
class RunHooksBase(Generic[TContext, TAgent]):
    async def on_agent_start(self, context: AgentHookContext[TContext], agent: TAgent) -> None: ...
    async def on_agent_end(self, context: AgentHookContext[TContext], agent: TAgent, output: Any) -> None: ...
    async def on_llm_start(self, context: RunContextWrapper[TContext], agent: Agent[TContext],
                           system_prompt: Optional[str], input_items: list[TResponseInputItem]) -> None: ...
    async def on_llm_end(self, context: RunContextWrapper[TContext], agent: Agent[TContext],
                         response: ModelResponse) -> None: ...
    async def on_tool_start(self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool) -> None: ...
    async def on_tool_end(self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool,
                          result: str) -> None: ...
    async def on_handoff(self, context: RunContextWrapper[TContext], from_agent: TAgent,
                         to_agent: TAgent) -> None: ...
```

**AgentHooksBase** -- receives callbacks for a specific agent instance:

```python
class AgentHooksBase(Generic[TContext, TAgent]):
    async def on_start(self, context: AgentHookContext[TContext], agent: TAgent) -> None: ...
    async def on_end(self, context: AgentHookContext[TContext], agent: TAgent, output: Any) -> None: ...
    async def on_handoff(self, context: RunContextWrapper[TContext], agent: TAgent, source: TAgent) -> None: ...
    async def on_tool_start(self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool) -> None: ...
    async def on_tool_end(self, context: RunContextWrapper[TContext], agent: TAgent, tool: Tool,
                          result: str) -> None: ...
    async def on_llm_start(self, context: RunContextWrapper[TContext], agent: Agent[TContext],
                           system_prompt: Optional[str], input_items: list[TResponseInputItem]) -> None: ...
    async def on_llm_end(self, context: RunContextWrapper[TContext], agent: Agent[TContext],
                         response: ModelResponse) -> None: ...
```

**Registration**: hooks are set on agents at construction time:

```python
agent = Agent(
    name="My Agent",
    tools=[my_tool],
    hooks=CustomAgentHooks(display_name="My Agent"),
)
```

**Key Limitation**: `on_tool_start`/`on_tool_end` apply only to local tools, NOT hosted tools (WebSearchTool, HostedMCPTool, etc.). This is a significant gap for MCP tool monitoring.

**File locations**:
- `src/agents/lifecycle.py` -- RunHooksBase, AgentHooksBase definitions
- `src/agents/agent.py` -- Agent class with hooks parameter
- `examples/basic/agent_lifecycle_example.py` -- usage patterns

### 3.2 Microsoft Agent Framework -- 3-Tier Middleware Chain (7.4k stars)

The most sophisticated hook system found. Three independent middleware pipelines that form chains via `next()` delegation:

**Tier 1: Agent Middleware** -- intercepts agent run execution:

```python
from agent_framework import AgentMiddleware, AgentContext

class SecurityAgentMiddleware(AgentMiddleware):
    async def process(
        self,
        context: AgentContext,
        call_next: Callable[[], Awaitable[None]],
    ) -> None:
        # Pre-processing
        if "password" in context.messages[-1].text.lower():
            context.result = AgentResponse(messages=[Message("assistant", ["Blocked."])])
            return  # Don't call call_next() to prevent execution
        await call_next()
        # Post-processing available here
```

**AgentContext** exposes: `agent`, `messages`, `is_streaming`, `metadata` (dict for cross-middleware state), `result` (modifiable), `terminate` (flag to stop), `kwargs`.

**Tier 2: Function Middleware** -- intercepts tool/function invocations:

```python
from agent_framework import FunctionMiddleware, FunctionInvocationContext

class CachingMiddleware(FunctionMiddleware):
    def __init__(self):
        self.cache = {}

    async def process(self, context: FunctionInvocationContext, next):
        cache_key = f"{context.function.name}:{context.arguments}"
        if cache_key in self.cache:
            context.result = self.cache[cache_key]
            context.terminate = True
            return
        await next(context)
        if context.result:
            self.cache[cache_key] = context.result
```

**FunctionInvocationContext** exposes: `function`, `arguments`, `metadata`, `result`, `terminate`, `kwargs`.

**Tier 3: Chat Middleware** -- intercepts raw LLM requests:

```python
from agent_framework import ChatMiddleware, ChatContext

class LoggingChatMiddleware(ChatMiddleware):
    async def process(self, context: ChatContext, next):
        print(f"Sending {len(context.messages)} messages to AI")
        await next(context)
        print("AI response received")
```

**ChatContext** exposes: `chat_client`, `messages`, `options`, `is_streaming`, `metadata`, `result`, `terminate`, `kwargs`.

**Registration scopes**:

```python
# Agent-level: persistent across ALL runs
agent = client.as_agent(
    name="Agent",
    middleware=[SecurityAgentMiddleware(), LoggingFunctionMiddleware()],
)

# Run-level: this specific run only
result = await agent.run("query", middleware=[extra_middleware])
```

**Execution order**: Agent middleware (outermost) -> Run middleware (innermost) -> Agent execution.

**Middleware decorators** for annotation-free authoring:

```python
@agent_middleware
async def simple(context, next):
    await next(context)

@function_middleware
async def log_fn(context, next):
    await next(context)

@chat_middleware
async def log_chat(context, next):
    await next(context)
```

**Key files**:
- `python/packages/` -- core framework
- `python/samples/getting_started/middleware/` -- 4 examples (class-based, function-based, shared-state, exception-handling)

### 3.3 Semantic Kernel -- Filter System (27.3k stars)

Semantic Kernel uses a simpler filter model with 3 filter types:

```python
class FilterTypes(str, Enum):
    FUNCTION_INVOCATION = "function_invocation"
    PROMPT_RENDERING = "prompt_rendering"
    AUTO_FUNCTION_INVOCATION = "auto_function_invocation"
```

**Decorator-based registration**:

```python
@kernel.filter(FilterTypes.AUTO_FUNCTION_INVOCATION)
async def auto_function_invocation_filter(context: AutoFunctionInvocationContext, next):
    await next(context)
    # Modify context.function_result after execution
    # Set context.terminate = True to stop chain
```

**FilterContextBase** provides: `function` (KernelFunction), `kernel` (Kernel), `arguments` (KernelArguments), `is_streaming` (bool).

**FunctionInvocationContext** extends FilterContextBase with: `result` (FunctionResult | None).

**AutoFunctionInvocationContext** provides: `function.name`, `function.plugin_name`, `request_sequence_index`, `function_sequence_index`, `chat_history`, `function_result`.

**Key insight**: The middleware chain pattern (`await next(context)`) allows pre/post interception, result modification, and early termination -- same as Microsoft Agent Framework but with fewer tiers.

### 3.4 Comparison Table

| Feature | OpenAI Agents SDK | MS Agent Framework | Semantic Kernel |
|---|---|---|---|
| Pattern | Observer/callback | Middleware chain | Filter chain |
| Tiers | 2 (Run + Agent) | 3 (Agent + Function + Chat) | 3 (FuncInvoke + PromptRender + AutoFunc) |
| Registration | Constructor param | Constructor + per-run | Decorator on kernel |
| Pre/Post interception | No (fire-and-forget) | Yes (via next()) | Yes (via next()) |
| Result modification | No | Yes (context.result) | Yes (context.function_result) |
| Early termination | No | Yes (context.terminate) | Yes (context.terminate) |
| Cross-middleware state | No | Yes (context.metadata dict) | No (via kernel) |
| Streaming support | N/A | Yes (separate streaming middleware) | Yes (is_streaming flag) |
| Class + function authoring | Class only | Both + decorators | Decorator only |

---

## 4. MCP Server Registries & Connection Management

### 4.1 Official MCP Registry (6.5k stars, Go)

The official registry at `modelcontextprotocol/registry` is an "app store for MCP servers" with:

**Architecture**:
- Go 1.24.x, PostgreSQL, Docker + ko builder
- API freeze at v0.1 (Oct 2025) -- no breaking changes
- Directory: `cmd/` (CLI), `internal/` (API/auth/DB/service), `pkg/` (types), `deploy/` (Pulumi)

**Publishing auth**:
- GitHub OAuth login
- GitHub OIDC (Actions support)
- DNS/HTTP domain verification for custom namespaces
- Namespace validation: `io.github.{username}` requires GitHub ownership proof

**Discovery**: API-based server listing with production data seeding at startup.

### 4.2 MCP Gateway & Registry (450 stars)

Enterprise-oriented gateway at `agentic-community/mcp-gateway-registry`:

**Authentication patterns**:
- 3-legged OAuth2: enterprise web browser flow (Keycloak or Microsoft Entra)
- 2-legged OAuth2: M2M via Client Credentials flow
- Fine-grained scopes: which servers, methods, tools, agents each identity can access
- Self-signed JWT tokens for CLI / coding assistant access

**Dynamic tool discovery**:
- `POST /api/search/semantic` -- natural language queries with relevance scoring
- Vector similarity + tokenized keyword matching
- Access-controlled views based on caller permissions
- 60-second cached aggregation for list operations

**Virtual MCP servers**: aggregate multiple backend servers into unified endpoints with session multiplexing and tool aliasing.

**Monitoring**: Grafana dashboards, OpenTelemetry, CloudWatch, Prometheus-compatible metrics.

**Peer federation**: bidirectional sync between registry instances.

### 4.3 MCP Python SDK Client Session (21.8k stars)

The `ClientSession` class in `modelcontextprotocol/python-sdk` handles connection lifecycle:

```python
class ClientSession(BaseSession[...]):
    def __init__(
        self,
        read_stream: MemoryObjectReceiveStream[SessionMessage | Exception],
        write_stream: MemoryObjectSendStream[SessionMessage],
        read_timeout_seconds: float | None = None,
        sampling_callback: SamplingFnT | None = None,
        elicitation_callback: ElicitationFnT | None = None,
        list_roots_callback: ListRootsFnT | None = None,
        logging_callback: LoggingFnT | None = None,
        message_handler: MessageHandlerFnT | None = None,
        client_info: types.Implementation | None = None,
    ) -> None: ...

    async def initialize(self) -> types.InitializeResult:
        """Protocol handshake: capabilities negotiation + version validation"""

    async def send_ping(self) -> types.EmptyResult:
        """Health check via JSON-RPC ping"""

    def get_server_capabilities(self) -> types.ServerCapabilities | None:
        """Cached capabilities from initialization"""
```

**Transport abstractions**: Stdio, SSE (deprecated), StreamableHTTP (production recommended).

**StreamableHTTP session management**:
- `Mcp-Session-Id` header for session tracking (UUID, JWT, or hash)
- Stateful mode: sessions tracked with UUIDs, resumption supported
- Stateless mode: fresh transport per request
- Reconnection via `Last-Event-ID` header for missed event recovery
- `EventStore` interface for optional resumability

### 4.4 OpenAI Agents SDK MCP Integration

Three server classes with async context manager lifecycle:

```python
# Stdio: local subprocess
async with MCPServerStdio(params={"command": "npx", "args": ["-y", "@mcp/server"]}) as server:
    agent = Agent(tools=server.tools)

# StreamableHTTP: remote server
async with MCPServerStreamableHttp(
    params={"url": "https://mcp.example.com"},
    cache_tools_list=True,
) as server:
    agent = Agent(tools=server.tools)
```

**Configuration options**:
- `cache_tools_list=True` -- cache `list_tools()` results to reduce latency
- `invalidate_tools_cache()` -- force fresh retrieval
- `failure_error_function` -- customize tool failure messages
- `max_retry_attempts` + `retry_backoff_seconds_base` -- automatic retry
- `require_approval` -- human-in-the-loop tool execution
- `tool_filter` -- restrict which tools agents can access
- `tool_meta_resolver` -- inject per-call metadata (tenant IDs, trace context)

### 4.5 MCP Hub (441 stars)

Centralized MCP server manager at `ravitemer/mcp-hub`:

- **Dual interface**: REST API (`/api/*`) + unified MCP endpoint (`/mcp`)
- **Health monitoring**: real-time SSE at `/api/events` for server status
- **Reconnection**: automatic recovery with state restoration
- **Server lifecycle**: start/stop/enable/disable on demand
- **Auto-cleanup**: optional shutdown when no clients remain
- **`${}` variable syntax**: environment variables, command execution, workspace variables in config

---

## 5. Connector Authentication Patterns

### 5.1 n8n Credential System (176k stars)

The most battle-tested credential architecture found:

- **Centralized credential manager**: create once, reuse across all workflows
- **Encryption**: all credentials encrypted with `N8N_ENCRYPTION_KEY` before DB storage
- **OAuth2 base class pattern**: `ICredentialType` with `extends: 'oAuth2Api'`
- **Auto token refresh**: built-in refresh token management
- **Dual auth modes**: e.g., GitHub supports both `githubApi` (token) and `githubOAuth2Api` (OAuth2)
- **400+ connectors** with standardized auth patterns

Example credential class (TypeScript):

```typescript
// GoogleOAuth2Api.credentials.ts
export class GoogleOAuth2Api implements ICredentialType {
    name = 'googleOAuth2Api';
    extends = ['oAuth2Api'];
    // ... properties for client_id, client_secret, scope, etc.
}
```

### 5.2 Windmill Resource Types (15.9k stars)

- **Resource Types**: each integration has a schema defining required credentials
- **OAuth + SSO**: Google Workspace, Microsoft/Azure, Okta via superadmin UI
- **Per-workspace encryption**: one encryption key per workspace
- **Pre-approved types**: sourced from WindmillHub for self-hosted instances

### 5.3 Airbyte CDK OAuth2

- `TokenAuthenticator`: basic token-based auth
- `Oauth2Authenticator`: refresh token + client credentials, automatic access token refresh
- **Declarative auth**: YAML configuration for OAuth2 flows
- Grant types: `refresh_token` or `client_credentials`
- Generated access token attached via `Authorization` header

### 5.4 MCP Gateway OAuth2

Most sophisticated MCP-specific auth:
- 3-legged OAuth2 (browser flow)
- 2-legged OAuth2 (client credentials for M2M)
- Fine-grained scopes per server/method/tool/agent
- JWT self-signing for CLI access
- Keycloak or Microsoft Entra ID backend

### 5.5 Pattern Summary

| System | OAuth2 | API Key | mTLS | Refresh | Encryption |
|---|---|---|---|---|---|
| n8n | Full (browser + refresh) | Yes | No | Auto | AES per instance |
| Windmill | SSO-based | Yes | No | Via SSO | Per workspace |
| Airbyte CDK | Refresh + client_credentials | Yes (token) | No | Auto | N/A |
| MCP Gateway | 3-leg + 2-leg + JWT | Via scopes | No | Yes | Credential masking |

---

## 6. Circuit Breakers & Rate Limiting

**Critical finding**: No AI agent framework implements circuit breakers natively. This is an opportunity for AGENT-33.

### 6.1 PyBreaker (655 stars)

The most complete Python circuit breaker implementation:

```python
from pybreaker import CircuitBreaker, CircuitBreakerListener

class ToolCallListener(CircuitBreakerListener):
    def before_call(self, cb, func, *args, **kwargs):
        """Called before the protected function"""
    def success(self, cb):
        """Called on successful execution"""
    def failure(self, cb, exc):
        """Called when the protected function fails"""
    def state_change(self, cb, old_state, new_state):
        """Called on CLOSED->OPEN->HALF_OPEN transitions"""

breaker = CircuitBreaker(
    fail_max=5,              # failures before opening
    reset_timeout=60,        # seconds before HALF_OPEN
    success_threshold=1,     # successes to close
    exclude=[ValidationError],  # business exceptions ignored
    listeners=[ToolCallListener()],
    state_storage=CircuitRedisStorage(state='closed', redis_object=redis_client),
    name='mcp-server-x',
)

# Decorator usage
@breaker
async def call_mcp_tool(tool_name, params):
    ...

# Context manager
with breaker.calling():
    result = await risky_operation()
```

**State machine**: CLOSED (normal) -> OPEN (after fail_max failures) -> HALF_OPEN (after reset_timeout) -> CLOSED (after success_threshold successes)

**Exclusions**: type-based (`exclude=[CustomError]`) or predicate-based (`exclude=[lambda e: e.status_code < 500]`)

### 6.2 aiobreaker (asyncio-native)

Fork of PyBreaker with native asyncio support (no Tornado dependency). Same API surface but designed for async/await codebases.

### 6.3 circuitbreaker Library

Simpler decorator-based approach:

```python
from circuitbreaker import circuit

@circuit(failure_threshold=5, recovery_timeout=30, expected_exception=ConnectionError)
async def call_external_service():
    ...
```

Supports async generators for fallback functions.

### 6.4 Recommended Pattern for AGENT-33

Wrap MCP tool calls and external service calls with circuit breakers:

```python
# Per-MCP-server circuit breaker
class MCPCircuitBreaker:
    def __init__(self, server_id: str, fail_max: int = 5, reset_timeout: int = 60):
        self.breaker = CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            exclude=[ValidationError, PermissionError],
            listeners=[MCPHealthListener(server_id)],
            name=f"mcp-{server_id}",
        )

    async def call_tool(self, tool_name: str, params: dict) -> Any:
        return await self.breaker.call_async(self._execute, tool_name, params)
```

---

## 7. Health Monitoring & Degradation

### 7.1 MCP Health Check Patterns

From the MCP implementation guides, the standard approach:

**Ping-based health**: MCP Python SDK `ClientSession.send_ping()` verifies connectivity via JSON-RPC.

**Multi-tier health assessment**:

```python
def get_health_status(metrics) -> str:
    error_rate = metrics.failed / metrics.total
    avg_response = sum(metrics.durations) / len(metrics.durations)

    if error_rate < 0.01 and avg_response < 500:
        return "healthy"
    elif error_rate < 0.05 and avg_response < 1000:
        return "degraded"
    else:
        return "unhealthy"
```

**Connection monitoring**:

```python
class ConnectionMonitor:
    connections: dict[str, ConnectionInfo]  # id -> {connected_at, last_activity, request_count}

    def get_metrics(self) -> dict:
        active = list(self.connections.values())
        return {
            "total_connections": len(active),
            "total_requests": sum(c.request_count for c in active),
            "idle_connections": sum(1 for c in active if self._is_idle(c)),
        }
```

**Keep-alive with periodic pings** (30-second interval recommended):

```python
async def keep_alive(transport):
    while True:
        try:
            await transport.send({"type": "ping"})
        except Exception:
            await trigger_reconnection()
        await asyncio.sleep(30)
```

**Auto-recovery with exponential backoff**:

```python
class ResilientMCPClient:
    async def connect(self):
        while self.attempts < 5:
            try:
                self.session = await create_client_session(self.server_params)
                return
            except Exception:
                delay = min(2 ** self.attempts, 60)
                await asyncio.sleep(delay)
                self.attempts += 1
```

### 7.2 Recommended Thresholds

From production implementations:
- **Error rate alert**: 5% of requests failing
- **Response time alert**: individual requests >1 second
- **Memory alert**: heap usage >500MB
- **Connection limit**: max 100 simultaneous connections
- **Keep-alive interval**: 30 seconds
- **Max reconnection attempts**: 5 with exponential backoff (max 60s)

### 7.3 MCP Hub Health Architecture

`ravitemer/mcp-hub` implements:
- SSE-based real-time health events at `/api/events`
- Automatic reconnection for unhealthy servers
- Auto-shutdown when no clients connected
- Real-time capability refresh on server add/remove

### 7.4 OpenAI Agents SDK Resilience

Built into MCP server classes:
- `connect_timeout_seconds` -- connection establishment deadline
- `cleanup_timeout_seconds` -- graceful shutdown deadline
- `max_retry_attempts` -- automatic retry count
- `retry_backoff_seconds_base` -- exponential backoff base
- `failure_error_function` -- custom error messages vs exceptions

---

## 8. Plugin SDK / Developer Experience

### 8.1 Microsoft Agent Framework (Best-in-Class DX)

**Tool authoring** with `@tool` decorator:

```python
from agent_framework import tool
from typing import Annotated
from pydantic import Field

@tool(approval_mode="never_require")
def get_weather(
    location: Annotated[str, Field(description="The location to get the weather for.")],
) -> str:
    """Get the weather for a given location."""
    return f"Weather in {location}: sunny, 22C"
```

**Middleware authoring** -- 3 registration styles:
1. **Class-based**: subclass `AgentMiddleware`, `FunctionMiddleware`, or `ChatMiddleware`
2. **Function-based**: plain async functions with `(context, next)` signature
3. **Decorator-based**: `@agent_middleware`, `@function_middleware`, `@chat_middleware`

**Agent construction**:

```python
agent = client.as_agent(
    name="WeatherAgent",
    instructions="You are a helpful weather assistant.",
    tools=get_weather,
    middleware=[SecurityMiddleware(), LoggingMiddleware()],
)
```

### 8.2 OpenAI Agents SDK Plugin DX

**Tool authoring** with `@function_tool`:

```python
from agents import function_tool

@function_tool
def get_weather(city: str) -> str:
    """Get the weather for a city."""
    return f"Sunny in {city}"
```

**Guardrails** (input/output/tool validation):

```python
from agents import Agent, InputGuardrail, GuardrailFunctionOutput

async def check_safety(ctx, agent, input) -> GuardrailFunctionOutput:
    result = await safety_agent.run(input)
    return GuardrailFunctionOutput(
        output_info=result,
        tripwire_triggered="unsafe" in result.final_output.lower(),
    )

agent = Agent(
    name="Safe Agent",
    input_guardrails=[InputGuardrail(guardrail_function=check_safety)],
)
```

**Guardrail execution modes**: parallel (default, optimistic) or blocking (safe, prevents wasted tokens).

### 8.3 Semantic Kernel Plugin DX

**Plugin authoring** with `@kernel_function`:

```python
from semantic_kernel.functions import kernel_function

class WeatherPlugin:
    @kernel_function(description="Get weather for a location")
    def get_weather(self, location: str) -> str:
        return f"Weather in {location}: sunny"
```

**Plugin loading from multiple sources**:
- Native code functions
- Prompt templates (YAML)
- OpenAPI specs (auto-generate tools from API specs)
- MCP servers

**AI connector hierarchy**: `AIServiceClientBase` -> task-specific bases (`ChatCompletionClientBase`, `EmbeddingGeneratorBase`, etc.) -> provider implementations (OpenAI, Anthropic, Ollama, etc.).

### 8.4 CrewAI Plugin DX

**Decorator-based agent/task definition**:

```python
from crewai import Agent, Task, Crew
from crewai_tools import SerperDevTool

agent = Agent(
    role="Researcher",
    goal="Find accurate information",
    tools=[SerperDevTool()],
)
```

**Custom tool** via `BaseTool` subclass with validation, caching, and event emission.

**MCP integration**: access to thousands of community MCP server tools.

**Dual paradigm**: Crews (autonomous teams) + Flows (event-driven control).

### 8.5 LangGraph Dynamic Tool Registry

From `langgraph-bigtool`:

```python
tool_registry = {str(uuid.uuid4()): tool for tool in all_tools}

# Agent automatically gets a `retrieve_tools` meta-tool
agent = create_agent(
    model=model,
    tools=tool_registry,
    store=InMemoryStore(),  # or Postgres
)
```

Semantic search via embeddings matches user queries against tool descriptions. Scales to hundreds/thousands of tools without context window bloat.

---

## 9. Synthesis: Patterns for AGENT-33

### 9.1 Lifecycle Hook System -- Recommended Design

Adopt the **Microsoft Agent Framework middleware chain model** with these adaptations:

```python
# Three-tier middleware for AGENT-33
class AgentHookContext:
    agent: AgentDefinition
    messages: list[ChatMessage]
    metadata: dict[str, Any]  # cross-middleware state
    result: AgentResult | None
    terminate: bool = False

class ToolHookContext:
    tool: Tool
    arguments: dict[str, Any]
    metadata: dict[str, Any]
    result: Any
    terminate: bool = False

class WorkflowHookContext:
    workflow: WorkflowDefinition
    step: WorkflowStep
    state: WorkflowState
    metadata: dict[str, Any]
    result: StepResult | None
    terminate: bool = False

# Base classes
class AgentHook(ABC):
    @abstractmethod
    async def process(self, ctx: AgentHookContext, next: Callable) -> None: ...

class ToolHook(ABC):
    @abstractmethod
    async def process(self, ctx: ToolHookContext, next: Callable) -> None: ...

class WorkflowHook(ABC):
    @abstractmethod
    async def process(self, ctx: WorkflowHookContext, next: Callable) -> None: ...
```

AGENT-33 advantage: add a **WorkflowHook** tier that neither OpenAI nor Microsoft have, intercepting DAG step execution with access to workflow state and topology.

### 9.2 MCP Connector Registry -- Recommended Design

Combine patterns from MCP Python SDK + MCP Hub + OpenAI Agents SDK:

```python
class MCPConnectorRegistry:
    """Manages MCP server connections with health monitoring"""

    servers: dict[str, MCPServerEntry]  # server_id -> entry

    async def register(self, config: MCPServerConfig) -> str:
        """Register and connect to MCP server"""

    async def deregister(self, server_id: str) -> None:
        """Disconnect and remove"""

    async def health_check(self, server_id: str) -> HealthStatus:
        """Ping-based health with multi-tier assessment"""

    async def discover_tools(self, query: str) -> list[MCPTool]:
        """Semantic search across all connected servers"""

    async def call_tool(self, server_id: str, tool_name: str, params: dict) -> Any:
        """Circuit-breaker-protected tool call"""

class MCPServerEntry:
    config: MCPServerConfig
    session: ClientSession | None
    circuit_breaker: CircuitBreaker
    health: HealthStatus  # healthy | degraded | unhealthy
    last_ping: datetime
    tools_cache: list[ToolInfo] | None
    cache_ttl: int = 60
```

### 9.3 Connector Auth -- Recommended Design

Follow n8n's centralized credential model:

```python
class CredentialType(str, Enum):
    API_KEY = "api_key"
    OAUTH2_AUTHORIZATION_CODE = "oauth2_auth_code"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    BEARER_TOKEN = "bearer_token"
    BASIC_AUTH = "basic_auth"

class ConnectorCredential(BaseModel):
    id: str
    tenant_id: str
    name: str
    credential_type: CredentialType
    encrypted_data: bytes  # AES-encrypted credential payload
    oauth2_refresh_token: SecretStr | None
    oauth2_token_url: str | None
    expires_at: datetime | None

class CredentialManager:
    async def store(self, cred: ConnectorCredential) -> str: ...
    async def resolve(self, cred_id: str) -> dict[str, str]: ...  # decrypted
    async def refresh_oauth2(self, cred_id: str) -> str: ...  # new access token
```

### 9.4 Circuit Breaker Integration -- Recommended Design

Wrap PyBreaker/aiobreaker for AGENT-33's tool and MCP calls:

```python
class ToolCircuitBreaker:
    def __init__(self, name: str, fail_max: int = 5, reset_timeout: int = 60):
        self.breaker = CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
            exclude=[ValidationError, PermissionError],
            listeners=[self._listener],
            name=name,
        )

    @property
    def state(self) -> str:  # "closed" | "open" | "half_open"
        return self.breaker.current_state

    async def execute(self, fn: Callable, *args, **kwargs) -> Any:
        return await self.breaker.call_async(fn, *args, **kwargs)
```

### 9.5 Priority Ranking for AGENT-33 Implementation

| Priority | Feature | Complexity | Value | Inspiration |
|---|---|---|---|---|
| P0 | 3-tier lifecycle hooks (agent/tool/workflow) | Medium | High | MS Agent Framework |
| P1 | MCP connector registry with health | High | High | MCP SDK + Hub + Gateway |
| P2 | Circuit breakers on tool/MCP calls | Low | Medium | PyBreaker |
| P3 | Connector credential management | Medium | Medium | n8n credential system |
| P4 | Dynamic tool discovery (semantic) | Medium | Medium | LangGraph bigtool + MCP Gateway |
| P5 | Plugin SDK with decorators | Low | Medium | MS Agent Framework @tool |
| P6 | Guardrails (input/output/tool) | Medium | Medium | OpenAI Agents SDK |

---

## 10. Sources

### Primary Repositories
- [openai/openai-agents-python](https://github.com/openai/openai-agents-python) -- 19.1k stars, lifecycle hooks + MCP + guardrails
- [microsoft/agent-framework](https://github.com/microsoft/agent-framework) -- 7.4k stars, 3-tier middleware
- [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel) -- 27.3k stars, filter system + plugin arch
- [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk) -- 21.8k stars, client session + transport
- [modelcontextprotocol/registry](https://github.com/modelcontextprotocol/registry) -- 6.5k stars, server publishing
- [agentic-community/mcp-gateway-registry](https://github.com/agentic-community/mcp-gateway-registry) -- 450 stars, enterprise gateway
- [microsoft/autogen](https://github.com/microsoft/autogen) -- 54.7k stars, event-driven agents
- [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) -- 25k stars, graph workflows
- [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) -- 44.5k stars, tool hooks + Crews/Flows
- [n8n-io/n8n](https://github.com/n8n-io/n8n) -- 176k stars, credential system
- [windmill-labs/windmill](https://github.com/windmill-labs/windmill) -- 15.9k stars, resource types + OAuth
- [ravitemer/mcp-hub](https://github.com/ravitemer/mcp-hub) -- 441 stars, server lifecycle + health SSE
- [danielfm/pybreaker](https://github.com/danielfm/pybreaker) -- 655 stars, circuit breaker
- [langchain-ai/langgraph-bigtool](https://github.com/langchain-ai/langgraph-bigtool) -- 515 stars, dynamic tool registry
- [airbytehq/airbyte-python-cdk](https://github.com/airbytehq/airbyte-python-cdk) -- connector development kit

### Documentation
- [Microsoft Agent Framework Middleware](https://learn.microsoft.com/en-us/agent-framework/user-guide/agents/agent-middleware) -- complete middleware reference
- [OpenAI Agents SDK Lifecycle](https://openai.github.io/openai-agents-python/ref/lifecycle/) -- hook API reference
- [OpenAI Agents SDK MCP](https://openai.github.io/openai-agents-python/mcp/) -- MCP server integration
- [OpenAI Agents SDK Guardrails](https://openai.github.io/openai-agents-python/guardrails/) -- input/output/tool guardrails
- [MCP Health Checks Guide](https://mcpcat.io/guides/implementing-connection-health-checks/) -- health monitoring patterns
- [MCP Transports Spec](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) -- StreamableHTTP spec
- [Semantic Kernel Components](https://learn.microsoft.com/en-us/semantic-kernel/concepts/semantic-kernel-components) -- plugin architecture
- [Airbyte CDK Auth](https://docs.airbyte.com/connector-development/connector-builder-ui/authentication) -- OAuth2 patterns
