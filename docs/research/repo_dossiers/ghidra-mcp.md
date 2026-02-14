# Repo Dossier: LaurieWired/GhidraMCP

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

GhidraMCP is an MCP (Model Context Protocol) server that bridges LLMs to Ghidra's reverse engineering capabilities through a two-layer architecture: a Java plugin (86.2% of codebase) runs an embedded HTTP server inside Ghidra exposing 30+ REST endpoints for decompilation, analysis, and modification, while a Python bridge (13.8%) translates MCP tool calls into HTTP requests. With 7.6k stars and 648 forks, it demonstrates how to make complex domain-specific tools accessible to LLMs by wrapping expert-level functionality (binary decompilation, cross-reference analysis, symbol renaming) behind simple, well-documented tool interfaces. The system operates locally with no auth, relying on MCP's stdio transport for security isolation, and uses Ghidra's transaction framework to ensure data consistency across AI-driven modifications.

## 2) Core orchestration model

**No multi-agent orchestration** — GhidraMCP is a single-purpose tool bridge with no agent framework. The orchestration model is purely client-driven: the LLM (via MCP client like Claude Desktop) decides which tools to call and in what sequence. The architecture is:

```
MCP Client (Claude) → stdio transport → Python bridge → HTTP → Java plugin → Ghidra APIs
```

**Key pattern**: Progressive capability exposure through layered abstraction. The Java plugin exposes Ghidra's complex C++ decompiler and binary analysis engine through simple HTTP endpoints (`/decompile_function?address=0x401000`), while the Python bridge further simplifies this into MCP tools with typed parameters and docstrings. This three-layer translation (Ghidra API → HTTP → MCP) makes binary reverse engineering accessible to general-purpose LLMs without domain-specific training.

**Stateless design**: Every tool call is independent; the plugin reads current state from Ghidra's active program and returns results. No session management, no conversation history, no workflow state. The LLM must maintain context across calls (e.g., remembering which function it decompiled to ask for cross-references next).

**Synchronous execution**: All operations block until completion. Decompilation uses a 30-second timeout to prevent hangs on complex functions. No async/streaming patterns; each tool call returns complete results or error.

## 3) Tooling and execution

**Tool registry**: 27 MCP tools defined in `bridge_mcp_ghidra.py` using FastMCP's `@mcp.tool()` decorator. Tools fall into five categories:

1. **Listing/Discovery** (8 tools): `list_methods`, `list_classes`, `list_segments`, `list_imports`, `list_exports`, `list_namespaces`, `list_data_items`, `list_strings` — all paginated with `offset`/`limit` parameters (defaults: 0/100-2000 depending on data type)
2. **Code Analysis** (3 tools): `decompile_function`, `disassemble_function`, `search_functions_by_name` — core reverse engineering primitives
3. **Cross-references** (3 tools): `get_xrefs_to`, `get_xrefs_from`, `get_function_xrefs` — trace program flow and data dependencies
4. **Modification** (8 tools): `rename_function`, `rename_data`, `rename_variable`, `set_decompiler_comment`, `set_disassembly_comment`, `set_function_prototype`, `set_local_variable_type` — AI-driven refactoring
5. **Navigation** (3 tools): `get_current_address`, `get_current_function`, `get_function_by_address` — UI state access

**Execution model**: Two-phase with separate HTTP wrappers:

- `safe_get(endpoint, params)` — constructs URL via `urljoin`, 5-second timeout, returns `response.text.splitlines()` as list or `["Error {status}: {text}"]`
- `safe_post(endpoint, data)` — accepts dict or string payload, UTF-8 encoding, returns stripped response text

**Transaction safety**: Modifications execute inside Ghidra's transaction framework:

```java
int tx = program.startTransaction("Rename function");
try {
    // Perform operation
    successFlag.set(true);
} finally {
    program.endTransaction(tx, successFlag.get());
}
```

All DB changes auto-rollback on exception. Ghidra's undo/redo stack preserves AI modifications alongside manual edits.

**Thread marshalling**: GUI-sensitive operations use `SwingUtilities.invokeAndWait()` to respect Ghidra's single-threaded UI model. Decompilation runs on background threads via `DecompInterface` with 30-second timeout.

**Input validation**: Minimal at Python layer (non-empty query strings, reasonable pagination defaults). Java layer relies on Ghidra APIs rejecting invalid addresses/symbols. No explicit sanitization — trusts MCP stdio transport for isolation.

**Error handling**: Three-tier strategy:

1. HTTP errors → formatted strings: `"Error 404: Function not found"`
2. Ghidra exceptions → logged via `Msg.error()`, returned as user-friendly messages
3. Generic exceptions → caught at tool level, include exception type in response

Notable gap: No retry logic, no partial result handling for large datasets (pagination is manual).

## 4) Observability and evaluation

**Zero built-in observability** — no metrics, tracing, or telemetry. Logging limited to:

- Ghidra's `Msg.error()/warn()/info()` utility for server-side errors (console only, not exposed to MCP client)
- Python bridge has no logging in default stdio mode (optional log setup for SSE transport, but not shown in code)

**No evaluation framework**. The system has no tests (test directory exists but Maven shows only JUnit 3.8.1 dependency with test scope). No CI test runs in GitHub Actions — workflow only builds and packages artifacts.

**User-driven validation**: Quality depends on LLM's ability to:

1. Verify decompilation output makes sense
2. Cross-check modifications against intended changes
3. Detect when tool calls fail (error messages returned as strings, not exceptions)

**Community feedback mechanism**: 39 open GitHub issues serve as de facto bug tracker. Common problems:

- Timeout errors on large functions (5-second HTTP timeout too aggressive)
- Installation failures on newer Ghidra versions (11.4.x compatibility issues)
- Incomplete xref reporting (not listing all function calls)
- Authorization errors on rename operations (threading/transaction conflicts)

**Release cadence**: 5 releases in 10 months (March 2024 → June 2024), suggesting active early development but slowing maintenance. No semver guarantees; versions tied to Ghidra releases (1.4 = Ghidra 11.3.2).

## 5) Extensibility

**Highly extensible by design** — adding new tools is trivial:

1. **Java plugin**: Add HTTP endpoint handler (lambda pattern):
   ```java
   server.createContext("/new_endpoint", exchange -> {
       // Access Ghidra APIs
       String result = program.getFunctionManager()...;
       sendResponse(exchange, result);
   });
   ```

2. **Python bridge**: Add MCP tool definition:
   ```python
   @mcp.tool()
   def new_tool(param: str) -> str:
       """Docstring for LLM."""
       return safe_get("/new_endpoint", {"param": param})
   ```

**No plugin architecture within GhidraMCP itself** — it's a single monolithic plugin. Extensibility comes from Ghidra's ecosystem: the plugin can call any Ghidra API (600+ classes in SoftwareModeling, Base, Decompiler modules).

**Configuration**: Port number configurable via Ghidra Tool Options UI (default 8080). Python bridge accepts `--ghidra-server` flag to override URL (default `http://127.0.0.1:8080/`). No config files, env vars, or runtime parameter tuning.

**Transport flexibility**: Python bridge supports stdio (default, for MCP clients) or SSE (Server-Sent Events, for web UIs). Toggled via command-line flag. HTTP server in Java plugin is stateless and agnostic to client type.

**Packaging**: Maven assembly creates Ghidra-compatible ZIP extension (metadata + JAR in `lib/` folder). Python bridge distributed as standalone script with 2 dependencies (`mcp==1.5.0`, `requests==2.32.3`). No Docker, no installers, no cross-platform builds (Windows users must adapt Python invocation in MCP configs).

**Known extension points** (from GitHub issues):

- Structure management (create/edit/rename Ghidra structs) — requested but not implemented
- Tab/window navigation (switch between open binaries) — would require UI manipulation APIs
- Ghidra Server support (remote project access) — currently local-only

## 6) Notable practices worth adopting in AGENT-33

### 6.1 Progressive Capability Disclosure via Layered Abstraction

GhidraMCP translates expert-domain complexity (binary reverse engineering) into LLM-consumable tools through deliberate simplification at each layer:

- **Ghidra layer**: 600+ classes, C++ decompiler, transaction framework, symbol tables
- **HTTP layer**: 30 REST endpoints, minimal parameters (address, offset, limit), text responses
- **MCP layer**: 27 typed tools, docstrings explaining hex formats and pagination

**AGENT-33 application**: Our code execution layer (Phase 13) has similar complexity: sandboxing, validation, adapters, disclosure levels. We could expose this through tiered interfaces:

1. **Low-level**: `CodeExecutor.execute(contract)` — full ExecutionContract with all safety params
2. **Mid-level**: HTTP/NATS endpoints with JSON schemas (current plan)
3. **High-level**: MCP tools like `safe_shell_command(cmd: str)` that auto-infer validation rules

The key insight: don't expose raw complexity to LLMs. Each abstraction layer should hide 80% of configuration while preserving 100% of safety.

### 6.2 Transaction-Wrapped Modifications with Auto-Rollback

Every Ghidra modification (rename, retype, comment) runs inside explicit transactions that auto-rollback on exception:

```java
int tx = program.startTransaction("Description");
AtomicBoolean success = new AtomicBoolean(false);
try {
    // Mutation logic
    success.set(true);
} finally {
    program.endTransaction(tx, success.get());
}
```

**AGENT-33 gap**: Our workflow execution has checkpoints but no atomic operation wrapper. If a workflow step partially fails (e.g., writes file A, crashes before file B), we leave inconsistent state. We should add:

- `@atomic_step` decorator for workflow actions
- SQLAlchemy nested transactions for multi-table updates
- File operation journaling (write to temp, commit on success, rollback on failure)

GhidraMCP's pattern ensures the UI always shows valid state, even when AI hallucinates invalid modifications. Our system should provide the same guarantee.

### 6.3 Tool Categorization with Pagination Defaults

The 27 tools cluster into clear functional groups (listing, analysis, modification, navigation), and every list operation has sensible pagination:

- High-volume data (strings, data items): `limit=2000`
- Medium-volume (methods, classes): `limit=100`
- All operations: `offset=0` by default
- Docstrings explain pagination explicitly

**AGENT-33 application**: Our tool registry (`tools/builtin/`) has 4 tools with inconsistent interfaces:

- `shell_exec` — no output size limit (can crash on `cat /dev/random`)
- `file_read` — implicit max via config, not documented in tool schema
- `web_fetch` — "results may be summarized if large" (opaque behavior)
- `browser_control` — no pagination for multi-element operations

We should standardize pagination across all list-like operations and document limits in tool definitions that LLMs see.

### 6.4 Dual Transport Support (stdio + SSE) from Single Codebase

The Python bridge supports two deployment modes with one codebase:

```python
if args.transport == "sse":
    from mcp.server.sse import SseServerTransport
    # Setup SSE transport
else:
    mcp.run()  # Default stdio
```

**AGENT-33 application**: Our automation layer (`automation/webhooks.py`) only supports HTTP webhooks. We could add:

- stdio mode for local CLI tools
- SSE mode for real-time dashboard updates
- WebSocket mode for low-latency triggers

The pattern: design internal logic transport-agnostic, then add thin wrappers for each delivery mechanism. GhidraMCP's `safe_get/safe_post` functions don't care about MCP transport; they just return strings. Our workflow actions should similarly return pure data, letting the router handle serialization.

### 6.5 Minimal-Dependency Python Bridge Pattern

The Python bridge has exactly 2 dependencies and 200 lines of code. No frameworks, no abstractions, no over-engineering:

```python
import requests
from mcp import FastMCP

@mcp.tool()
def simple_wrapper(param: str) -> str:
    response = requests.get(f"{base_url}/endpoint", params={"param": param})
    return response.text if response.ok else f"Error {response.status_code}"
```

**AGENT-33 anti-pattern**: Our `llm/providers/` module has 3 layers of abstraction (BaseProvider, ModelRouter, provider implementations) for what is fundamentally HTTP request wrapping. We could learn from GhidraMCP's simplicity:

- Don't abstract until you have 3+ concrete implementations
- Keep HTTP logic at call site; avoid "client" classes that hide request details
- Use plain dicts/dataclasses, not custom serialization frameworks

The tradeoff: GhidraMCP's simplicity means no retry logic, connection pooling, or advanced error handling. But those features should be opt-in, not default complexity.

### 6.6 Security Through Isolation, Not Authentication

GhidraMCP has zero authentication/authorization:

- HTTP server binds to localhost (though 1 issue notes it currently binds to all interfaces — bug, not design)
- Python bridge uses stdio transport (process isolation)
- MCP clients (Claude Desktop) only expose to local user

**Security model**: Trust the runtime environment, not the network. If attacker has localhost HTTP access, they already own the machine.

**AGENT-33 application**: Our current design uses JWT/API keys for all access (`security/auth.py`). This makes sense for multi-tenant cloud deployment but adds friction for local/single-user mode. We should support:

- **Cloud mode** (current): Full auth, tenant isolation, encrypted secrets
- **Local mode** (new): No auth, single tenant, filesystem-based config

The toggle should be one config variable (`deployment_mode="local"|"cloud"`), not 15 security settings users must coordinate.

**Risk**: GhidraMCP's "no auth" design assumes benign LLM. If Claude is compromised or prompt-injected, it has full Ghidra control. Our governance layer exists to prevent this, but we never inject `GovernanceConstraints` into prompts (see Critical Finding in MEMORY.md). We should learn GhidraMCP's simplicity, but add the safety rails they lack.

## 7) Risks / limitations to account for

### 7.1 Zero Input Validation Creates Command Injection Risk

The Python bridge passes user input directly to HTTP URLs:

```python
def rename_function(address: str, new_name: str) -> str:
    return safe_post("/rename_function_by_address", {"address": address, "name": new_name})
```

If `new_name` contains URL-special chars, HTTP params, or shell metacharacters, the Java plugin receives them unescaped. While Ghidra's symbol validation rejects most attacks, this violates defense-in-depth.

**AGENT-33 implication**: Our code execution validation (`execution/validation.py`) has 5 input validators (IV-01 through IV-05), but they only run on `ExecutionContract` fields. If we add HTTP/MCP bridges (as suggested in 6.1), we must validate at bridge layer too, not just executor core.

**Mitigation**: URL-encode all parameters, use JSON POST bodies (not query strings), whitelist allowed characters for symbol names.

### 7.2 Synchronous 5-Second Timeout Breaks on Complex Functions

All HTTP calls use `timeout=5` seconds. Decompiling large functions (10k+ instructions) regularly exceeds this, causing tool failures the LLM must retry. The Java server has 30-second decompiler timeout but the Python client gives up first.

**AGENT-33 risk**: Our workflow actions have per-step `timeout_seconds` config (default 300s) but no progressive timeout strategy. If a step times out, we fail the entire workflow. We should learn from GhidraMCP's mistake:

- Don't use fixed timeouts for variable-complexity operations
- Implement progressive disclosure: quick summary → full detail → background job
- Return partial results with continuation tokens

**Mitigation**: Make timeout configurable per-tool, add streaming response support for long operations, return "operation started, poll /status" for >5s jobs.

### 7.3 No Test Coverage Means Silent Breakage Across Ghidra Versions

The repo has 39 open issues, many reporting breakage on newer Ghidra versions (11.4.x) despite plugin claiming 11.3.2 compatibility. Root cause: zero automated tests, no version matrix CI.

**AGENT-33 strength**: We have 197 tests, ruff/mypy in CI, `@pytest.mark.integration` for service-dependent tests. But we lack:

- **Version matrix testing**: No CI runs against multiple Python versions, multiple DB versions, multiple LLM provider versions
- **Compatibility declarations**: No minimum version specs in `pyproject.toml` dependencies
- **Deprecation warnings**: No proactive alerts when using soon-to-be-removed APIs

**Lesson**: GhidraMCP's popularity (7.6k stars) comes despite zero tests because the value prop (LLMs doing reverse engineering) is so compelling. But maintainability suffers. We should not trade test quality for feature velocity.

### 7.4 Stateless Design Prevents Multi-Step Workflows

Every tool call is independent. To "decompile function X, find its callees, rename them all," the LLM must:

1. Call `decompile_function(X)` → get pseudocode
2. Parse pseudocode to extract callee names (LLM prompt engineering, not tool logic)
3. For each callee, call `search_functions_by_name(name)` → get address
4. For each address, call `rename_function(address, new_name)`

This requires 3N+1 sequential HTTP round-trips for N callees. No batching, no server-side iteration, no workflow composition.

**AGENT-33 advantage**: Our workflow engine supports DAGs with parallel steps, data transforms, conditionals, and sub-workflows. We could expose this through MCP by:

- Adding `register_workflow(dag_yaml)` tool that stores workflow server-side
- Adding `execute_workflow(workflow_id, inputs)` tool that runs it
- Returning workflow execution ID that LLM can poll/cancel

This would reduce 3N+1 round-trips to 1 for common patterns, but requires more complexity than GhidraMCP's simplicity-first design.

**Tradeoff**: Stateless tools are easier to reason about and debug. Stateful workflows are more efficient but introduce lifecycle management (cleanup, cancellation, resume). We should support both: simple tools for ad-hoc queries, workflows for repeatable multi-step operations.

### 7.5 HTTP Binding to All Interfaces (Security Bug)

Per issue #XX, the Java server currently binds to `0.0.0.0:8080` instead of `127.0.0.1:8080`, exposing Ghidra's full modification API to the local network with no authentication.

**AGENT-33 implication**: Our FastAPI app binds to `0.0.0.0` by default (see `docker-compose.yml`: `ports: "8000:8000"`). This is correct for containerized deployment but dangerous for local development. We should:

- Bind to `127.0.0.1` in dev mode (local-only access)
- Bind to `0.0.0.0` in prod mode with mandatory auth
- Document the security model in `CLAUDE.md` and `.env.example`

GhidraMCP's bug demonstrates that even experienced developers miss this. We should add a startup check that warns when binding to all interfaces without auth enabled.

### 7.6 No Rate Limiting Enables Resource Exhaustion

An LLM stuck in a loop (or malicious prompt injection) can spam tool calls:

```python
for i in range(10000):
    list_strings(offset=i*2000, limit=2000)  # Enumerate all strings
```

No request throttling, no concurrent call limits, no resource quotas. The HTTP server processes requests sequentially but doesn't track per-client usage.

**AGENT-33 gap**: We have no rate limiting anywhere. Our `AuthMiddleware` validates tokens but doesn't count requests. An API key holder can spam `/v1/agents/invoke` until Redis/DB dies.

**Mitigation**: Add rate limiting middleware (e.g., `slowapi` for FastAPI) with per-tenant quotas, per-endpoint limits, and burst allowances. GhidraMCP's local-only design assumes benign clients; our multi-tenant cloud design cannot.

## 8) Feature extraction (for master matrix)

| Feature Category | GhidraMCP | AGENT-33 Current | Gap / Opportunity |
|---|---|---|---|
| **MCP Server Support** | ✅ Native (FastMCP) | ❌ None | Add MCP bridge for tools/agents |
| **Tool Interface Design** | ✅ 27 typed tools, docstrings, pagination | ⚠️ 4 tools, inconsistent interfaces | Standardize tool schemas |
| **Multi-Layer Abstraction** | ✅ Ghidra → HTTP → MCP | ⚠️ Direct API exposure | Add progressive disclosure |
| **Transaction Safety** | ✅ Auto-rollback on exception | ❌ No atomic operations | Add transaction decorators |
| **Dual Transport** | ✅ stdio + SSE | ❌ HTTP only | Add stdio/SSE/WS transports |
| **Input Validation** | ❌ Minimal/none | ✅ 5-tier validation (Phase 13) | Maintain our strength |
| **Test Coverage** | ❌ Zero tests | ✅ 197 tests | Maintain our strength |
| **Rate Limiting** | ❌ None | ❌ None | Add throttling middleware |
| **Timeout Strategy** | ❌ Fixed 5s (too short) | ⚠️ Fixed 300s (no progressive) | Add adaptive timeouts |
| **Stateful Workflows** | ❌ Stateless tools only | ✅ DAG engine | Add workflow-as-tool bridge |
| **Security Model** | Local-only, no auth | Multi-tenant JWT/API keys | Add local-mode toggle |
| **Error Handling** | ⚠️ String messages (no exceptions) | ✅ Structured errors + lineage | Maintain our strength |
| **Documentation** | ✅ Excellent (docstrings + README) | ⚠️ Code-heavy, few examples | Add tool usage examples |
| **Extensibility** | ✅ Trivial (add endpoint + wrapper) | ⚠️ Complex (registry + schema + tests) | Simplify tool registration |
| **Community Adoption** | ✅ 7.6k stars, 648 forks | ⚠️ Internal/early stage | Focus on DX, not just features |

**Key takeaway**: GhidraMCP succeeds because it makes complex tools accessible through simple, well-documented interfaces. AGENT-33 has stronger engineering (tests, validation, transactions) but worse developer experience (no MCP support, complex tool registration, sparse examples). We should merge GhidraMCP's simplicity with our robustness.

## 9) Evidence links

### Repository & Documentation
- Main repo: https://github.com/LaurieWired/GhidraMCP
- README: https://github.com/LaurieWired/GhidraMCP/blob/main/README.md
- Latest release: https://github.com/LaurieWired/GhidraMCP/releases/tag/v1.4 (June 23, 2024)
- Open issues: https://github.com/LaurieWired/GhidraMCP/issues (39 as of 2026-02-14)
- License: https://github.com/LaurieWired/GhidraMCP/blob/main/LICENSE (Apache 2.0)

### Source Code Analysis
- Python MCP bridge: https://github.com/LaurieWired/GhidraMCP/blob/main/bridge_mcp_ghidra.py (27 tools, 200 LOC)
- Java plugin: https://github.com/LaurieWired/GhidraMCP/blob/main/src/main/java/com/lauriewired/GhidraMCPPlugin.java (HTTP server, 30+ endpoints)
- Maven config: https://github.com/LaurieWired/GhidraMCP/blob/main/pom.xml (Ghidra dependencies, assembly)
- Python deps: https://github.com/LaurieWired/GhidraMCP/blob/main/requirements.txt (`mcp==1.5.0`, `requests==2.32.3`)
- Extension metadata: https://github.com/LaurieWired/GhidraMCP/blob/main/src/main/resources/extension.properties
- Module manifest: https://github.com/LaurieWired/GhidraMCP/blob/main/src/main/resources/Module.manifest

### Build & CI
- GitHub Actions workflow: https://github.com/LaurieWired/GhidraMCP/blob/main/.github/workflows/build.yml (Maven build, Ghidra download)
- Assembly descriptor: https://github.com/LaurieWired/GhidraMCP/blob/main/src/assembly/ghidra-extension.xml (ZIP packaging)

### Key Issues Referenced
- Security: HTTP binding to all interfaces (needs localhost restriction)
- Performance: 5-second timeout too short for complex decompilation
- Compatibility: Installation failures on Ghidra 11.4.x
- Feature requests: Structure management, Ghidra Server support, tab navigation
- Bug reports: Incomplete xref results, rename authorization errors

### Community Metrics
- Stars: 7.6k (as of 2026-02-14)
- Forks: 648
- Contributors: 9
- Language breakdown: Java 86.2%, Python 13.8%
