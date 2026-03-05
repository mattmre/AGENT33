# Session 55 – Phase 32 Connector Boundary Audit

**Date:** 2026-03-07
**Phase:** 32 – Middleware Chain, MCP Connectors & Circuit Breakers
**Scope:** All outbound HTTP call sites in `engine/src/agent33/`

## Summary

All **runtime** outbound HTTP calls that process user or agent input are
routed through `ConnectorExecutor` via `build_connector_boundary_executor()`.
Two categories of call sites are intentionally exempt: infrastructure health
probes and developer CLI tooling.

| Category | Count | Through Boundary? |
|----------|------:|:------------------:|
| LLM providers | 2 | ✅ |
| Embedding providers | 2 | ✅ |
| Tools (web_fetch, search, reader) | 3 | ✅ |
| MCP bridge / client | 2 | ✅ |
| Workflow HTTP action | 1 | ✅ |
| Multimodal adapters | 3 | ✅ |
| Chat proxy | 1 | ✅ |
| Messaging adapters | 7 | ✅ (via `messaging/boundary.py`) |
| Health probes | 3 | ❌ (infrastructure) |
| CLI tool | 2 | ❌ (developer tooling) |

## Boundary-Protected Call Sites

### LLM Providers

| File | Line | Connector | Notes |
|------|-----:|-----------|-------|
| `llm/openai.py` | 42 | `httpx.AsyncClient` | Wrapped by `build_connector_boundary_executor` (L49) |
| `llm/ollama.py` | 40 | `httpx.AsyncClient` | Wrapped by `build_connector_boundary_executor` (L47) |

### Embedding Providers

| File | Line | Connector | Notes |
|------|-----:|-----------|-------|
| `memory/embeddings.py` | 34 | `httpx.AsyncClient` | Wrapped (L41) |
| `memory/jina_embeddings.py` | 33 | `httpx.AsyncClient` | Wrapped (L40) |

### Built-in Tools

| File | Line | Connector | Notes |
|------|-----:|-----------|-------|
| `tools/builtin/web_fetch.py` | 72 | `httpx.AsyncClient` | Wrapped (L77) |
| `tools/builtin/search.py` | 56 | `httpx.AsyncClient` | Wrapped (L59) – SearXNG |
| `tools/builtin/reader.py` | 110,162 | `httpx.AsyncClient` | Wrapped (L84) |

### MCP

| File | Line | Connector | Notes |
|------|-----:|-----------|-------|
| `tools/mcp_bridge.py` | 99,129 | `httpx.AsyncClient` | Wrapped (L237–238) |
| `tools/mcp_client.py` | — | via boundary | Wrapped (L120) |

### Workflow HTTP Action

| File | Line | Connector | Notes |
|------|-----:|-----------|-------|
| `workflows/actions/http_request.py` | 142 | `httpx.AsyncClient` | Wrapped (L107) |

### Multimodal Adapters

| File | Line | Connector | Notes |
|------|-----:|-----------|-------|
| `multimodal/adapters.py` | 60 | TTS | Wrapped (L32) |
| `multimodal/adapters.py` | 117,138 | STT | Wrapped (L93) |
| `multimodal/adapters.py` | 229 | Image gen | Wrapped (L180) |

### Chat Proxy

| File | Line | Connector | Notes |
|------|-----:|-----------|-------|
| `api/routes/chat.py` | 59 | `httpx.AsyncClient` | Wrapped (L69) |

### Messaging Adapters

All messaging adapters create `httpx.AsyncClient` instances directly but are
wrapped at the operation level by `messaging/boundary.py` which calls
`build_connector_boundary_executor`.

| File | Adapter |
|------|---------|
| `messaging/discord.py` | Discord |
| `messaging/slack.py` | Slack |
| `messaging/telegram.py` | Telegram |
| `messaging/whatsapp.py` | WhatsApp |
| `messaging/matrix.py` | Matrix |
| `messaging/signal.py` | Signal |
| `messaging/imessage.py` | iMessage |

## Exempt Call Sites (Not Through Boundary)

### Health Probes – `api/routes/health.py`

| Line | Target | Justification |
|-----:|--------|---------------|
| 31 | Ollama health | Infrastructure probe; no user input; 3 s timeout |
| 64 | SearXNG health | Infrastructure probe; no user input; 3 s timeout |
| 79 | Qdrant health | Infrastructure probe; no user input; 3 s timeout |

These are read-only liveness checks invoked by the `/health` endpoint. They
carry no user-controlled payload and use hard-coded URLs from settings.
**Risk: Low.** No remediation needed.

### CLI Tooling – `cli/main.py`

| Line | Target | Justification |
|-----:|--------|---------------|
| 141 | Own API (chat) | Developer CLI; runs locally |
| 185 | Own API (health) | Developer CLI; runs locally |

The CLI makes requests to the engine's own REST API on `localhost`. These
are developer-facing utilities, not runtime agent paths.
**Risk: None.** No remediation needed.

## Gaps Found

**None.** All runtime outbound call sites that process user or agent data
pass through the connector boundary middleware chain, which enforces:

1. **Governance** – blocklist filtering via policy packs
2. **Timeout** – per-connector timeout enforcement
3. **Retry** – configurable retry with back-off
4. **Circuit breaker** – failure threshold / half-open recovery
5. **Metrics** – call count and latency tracking

## Recommendations

1. **Keep audit current** – any new `httpx.AsyncClient` usage in runtime
   paths must go through `build_connector_boundary_executor`.
2. **CI lint rule** (future) – consider a ruff custom rule or grep-based CI
   check that flags new `httpx.AsyncClient(` in `engine/src/agent33/` unless
   annotated with `# boundary-exempt`.
3. **Messaging adapter consolidation** – the seven messaging adapters share
   a common HTTP pattern. A shared base class could further centralise
   boundary enforcement.
