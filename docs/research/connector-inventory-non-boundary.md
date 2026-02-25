# Connector Inventory Continuation — Non-Boundary Outbound Surfaces

## Purpose / Scope

This note continues the outbound-connector inventory from Session 40 and documents:

- boundary-adopted surfaces now verified in-repo, and
- remaining outbound surfaces that still execute outside the connector boundary layer.

Scope is limited to currently implemented outbound network paths in `engine/src/agent33` and operational follow-through prioritization.

## Boundary-Adopted Surfaces (Verified)

| Surface | Path | Boundary status |
|---|---|---|
| Web fetch tool | `engine/src/agent33/tools/builtin/web_fetch.py` | Connector-boundary execution path in place |
| Search tool | `engine/src/agent33/tools/builtin/search.py` | Connector-boundary execution path in place |
| Reader tool | `engine/src/agent33/tools/builtin/reader.py` | Connector-boundary execution path in place |
| Workflow HTTP request action | `engine/src/agent33/workflows/actions/http_request.py` | Connector-boundary execution + policy pack support |
| MCP client manager tool calls | `engine/src/agent33/tools/mcp_client.py` | Connector-boundary wrapping for `tools/call` path |
| MCP bridge RPC calls | `engine/src/agent33/tools/mcp_bridge.py` | Boundary executor used for MCP RPC path |
| MCP security scanner integration | `engine/src/agent33/component_security/mcp_scanner.py` | Uses boundary-enabled MCP client manager calls |

## Remaining Non-Boundary Outbound Surfaces

### API / Chat

- `engine/src/agent33/api/routes/chat.py`
  - Proxies `/v1/chat/completions` with direct `httpx.AsyncClient` calls to local orchestration engine endpoints.

### Multimodal

- `engine/src/agent33/multimodal/adapters.py`
  - Direct outbound HTTP calls for:
    - OpenAI Whisper transcription
    - ElevenLabs TTS
    - OpenAI TTS
    - OpenAI Vision/chat completions

### LLM / Embeddings

- `engine/src/agent33/llm/openai.py`
  - Direct provider HTTP calls (`/chat/completions`, `/models`).
- `engine/src/agent33/llm/ollama.py`
  - Direct provider HTTP calls (`/api/chat`, `/api/tags`).
- `engine/src/agent33/memory/embeddings.py`
  - Direct Ollama embedding calls (`/api/embeddings`, `/api/embed`).
- `engine/src/agent33/memory/jina_embeddings.py`
  - Direct Jina embeddings API calls (`https://api.jina.ai/v1/embeddings`).

### Messaging

- `engine/src/agent33/messaging/slack.py`
- `engine/src/agent33/messaging/discord.py`
- `engine/src/agent33/messaging/telegram.py`
- `engine/src/agent33/messaging/whatsapp.py`
- `engine/src/agent33/messaging/signal.py`
- `engine/src/agent33/messaging/matrix.py`
- `engine/src/agent33/messaging/imessage.py`

All listed adapters currently perform direct outbound HTTP calls to provider/platform APIs.

### Infra

- `engine/src/agent33/messaging/bus.py`
  - Direct NATS connect/publish/request operations (no connector-boundary wrapper).

## Prioritized Next-Wave Recommendations

### High

1. Add boundary-managed execution wrapper(s) for `llm/*` and `memory/*embeddings*` provider calls.
2. Add boundary-managed execution wrapper(s) for `multimodal/adapters.py` provider calls.
3. Add boundary-managed execution wrapper(s) for `api/routes/chat.py` proxy egress path.

### Medium

1. Add boundary-managed wrappers for messaging adapter outbound sends + health probes.
2. Define provider-specific policy-pack profiles (LLM, multimodal, messaging) analogous to strict-web patterns.

### Low

1. Evaluate whether NATS bus operations should be represented as connector-boundary surfaces or remain infra-specialized.
2. Add inventory automation/reporting so non-boundary regressions are surfaced in CI documentation checks.

## Session Completion Statement

This session completed the connector inventory continuation requested in Session 40 follow-through by documenting verified boundary adoption and the remaining non-boundary outbound surfaces by subsystem.
