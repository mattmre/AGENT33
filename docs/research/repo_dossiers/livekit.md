# Repo Dossier: livekit/livekit

**Snapshot date:** 2026-02-14

## 1) One-paragraph summary

LiveKit is an open-source, real-time communication platform built around a WebRTC Selective Forwarding Unit (SFU) server written in Go. It provides room-based audio, video, and data-channel routing for applications ranging from video conferencing to AI voice agents. The primary interfaces are server-side SDKs (Go, Python, JS, Ruby, PHP, Rust), client SDKs (JavaScript, Swift, Kotlin, Flutter, Unity, React), and a companion Python agent framework (`livekit/agents`) that enables LLM-powered voice and multimodal agents to join rooms as participants. The core orchestration primitive is the **Room** -- a named session where participants publish and subscribe to media tracks, with the SFU handling selective forwarding, simulcast, and bandwidth estimation.

## 2) Core orchestration model

- **Primary primitive:** Room-based publish/subscribe. A Room is a named session containing Participants, each of whom publishes and subscribes to Tracks (audio, video, data). The server selectively forwards media packets between participants without transcoding (SFU model). For AI agents, the companion `livekit/agents` framework adds a dispatch model where agent Workers are assigned to rooms on demand.
- **State model:** Explicit server-side room state managed by the LiveKit server. Room metadata, participant metadata, and track state are maintained centrally. Multi-node deployments use Redis for shared state and room routing. The agent framework maintains local pipeline state (current utterance, interruption state, function call context) per agent session.
- **Concurrency:** Fully concurrent. Multiple participants in a room operate simultaneously. The SFU handles many rooms across a cluster of nodes. The agent framework uses Python asyncio with a worker pool model -- a single worker process can handle multiple concurrent agent sessions, each running its own STT/LLM/TTS pipeline independently.
- **Human-in-the-loop:** Not a built-in concept at the SFU level, but naturally supported through the room model. Human participants and AI agent participants coexist in the same room. Voice interruption handling in the agent framework (barge-in detection) is a form of real-time HITL. Data channels enable structured control messages (mute, transfer, escalate) from human participants or external systems.

## 3) Tooling and execution

- **Tool interface:** The agent framework supports LLM function calling as the primary tool interface. Agents can register callable functions that the LLM can invoke during conversation. These are exposed via the standard OpenAI-compatible function calling schema. The server itself exposes gRPC and Twirp (HTTP/JSON) APIs for room management, egress, ingress, and SIP operations. Webhooks provide event-driven integration.
- **Runtime environment:** The SFU server runs as a standalone Go binary or Docker container. Production deployments typically use Kubernetes with the official Helm chart. LiveKit Cloud offers a managed hosted option. Agent workers run as separate Python processes that connect to the LiveKit server via WebSocket, receiving dispatch requests when rooms need agent participation. Egress (recording/streaming) runs as a separate service using headless Chrome for compositing.
- **Sandboxing / safety controls:** Participant permissions are controlled via JWT tokens with fine-grained grants (canPublish, canSubscribe, canPublishData, canPublishSources, canUpdateOwnMetadata, hidden, room-specific grants). The server enforces these at the media layer. No code execution sandboxing exists at the SFU level -- that is the responsibility of application code. Agent workers run in their own processes and can be containerized for isolation.

## 4) Observability and evaluation

- **Tracing/logging:** The server emits structured logs (configurable level). Prometheus metrics are exposed at `/metrics` for SFU performance (track counts, packet loss, bandwidth, room counts, participant counts, connection quality scores). OpenTelemetry tracing support exists for distributed tracing across multi-node deployments. The agent framework provides event callbacks and logging for pipeline stages (STT transcription, LLM response, TTS synthesis, interruptions). LiveKit Cloud adds a dashboard with room analytics, quality metrics, and session replay.
- **Evaluation harness:** No built-in evaluation harness for AI agent quality. The project includes integration tests for the SFU server (Go test suite) and the agent framework (Python pytest). For voice agent evaluation, the ecosystem relies on external tools -- LiveKit has published guidance on using their Agents Playground for manual testing and iterating on voice agent behavior.

## 5) Extensibility

- **Where extensions live:** Agent framework plugins in `livekit-plugins-*` packages (separate PyPI packages for each STT/LLM/TTS provider). Server extensions via Webhooks, server-side SDKs, and the Egress/Ingress/SIP services. Client extensions via client SDKs with custom track processors and data channel handlers.
- **How to add tools/skills:** In the agent framework, register Python functions as callable tools via `@agent.tool` decorator or `FunctionContext`. These are passed to the LLM as available functions. New STT/LLM/TTS providers are added by implementing the plugin interface (`stt.STT`, `llm.LLM`, `tts.TTS` base classes) and publishing as a `livekit-plugins-*` package.
- **Config surface:** Server configuration via `livekit.yaml` or CLI flags (port, Redis URL, TURN/STUN servers, key/secret pairs, logging level, region, node IP). Agent workers configured via environment variables and code (worker options, room filters, agent pipeline parameters). JWT tokens configure per-participant permissions. Room settings (max participants, empty timeout, metadata) configured via server API at room creation time.

## 6) Notable practices worth adopting in AGENT 33

- **Room-as-session primitive for real-time agent interaction.** LiveKit's room model where AI agents and humans coexist as equal participants in a shared session is a powerful pattern. AGENT-33 could adopt a similar "session room" concept where agents, tools, and human operators share a unified communication space with pub/sub semantics, rather than strictly linear request/response chains.

- **Plugin architecture for swappable providers.** The `livekit-plugins-*` pattern (separate packages per STT/LLM/TTS provider, all implementing a common base class) provides clean separation of concerns and easy provider swapping. AGENT-33's LLM provider abstraction in `llm/` could adopt this pattern for a more formal plugin registry with consistent interfaces, especially as more providers are added.

- **Voice pipeline with interruption handling.** The `VoicePipelineAgent` implements sophisticated barge-in detection: when a user starts speaking mid-response, the agent cancels the current TTS output, sends a truncated transcript to the LLM for context, and restarts generation. This real-time responsiveness pattern is relevant if AGENT-33 adds voice or streaming interfaces.

- **Token-based fine-grained permissions per participant.** LiveKit's JWT grant system where each participant token specifies exactly what that participant can do (publish audio, subscribe to video, send data, update metadata) maps well to AGENT-33's multi-tenancy model. Each agent invocation could carry a scoped token defining exactly which tools, resources, and actions are permitted for that session.

- **Worker dispatch model for agent scaling.** Agents register as workers and get dispatched to rooms on demand. This decouples agent lifecycle from room lifecycle, enabling horizontal scaling. AGENT-33 could adopt a similar pattern where agent workers register capabilities and get dispatched to workflow steps, rather than being tightly coupled to a single workflow execution.

- **Webhook-driven event system for external integration.** LiveKit fires webhooks for room lifecycle events (created, finished), participant events (joined, left), track events (published, unpublished), and egress events. This event-driven integration pattern aligns with AGENT-33's existing webhook and event sensor architecture in `automation/`.

## 7) Risks / limitations to account for

- **Infrastructure complexity for voice/video.** Adding real-time media capabilities to AGENT-33 would require running a LiveKit server (or using LiveKit Cloud), managing TURN/STUN servers for NAT traversal, handling codec negotiation, and dealing with network quality variability. This is a substantial operational burden compared to text-based agent interactions.

- **Agent framework is Python-only.** The `livekit/agents` framework is exclusively Python. While LiveKit has server SDKs in many languages, the AI agent pipeline (VoicePipelineAgent, MultimodalAgent) is only available in Python. This is fine for AGENT-33 (also Python) but limits portability.

- **Latency sensitivity.** Voice agents require end-to-end latency under ~500ms to feel natural. This constrains LLM choice (must be fast), TTS choice (must support streaming), and deployment topology (agent workers should be co-located with the SFU). AGENT-33's current Ollama-based LLM approach may not meet latency requirements for voice without significant optimization.

- **No built-in conversation persistence.** LiveKit rooms are ephemeral -- when a room ends, the conversation state is lost unless the application explicitly captures it. AGENT-33 would need to bridge its memory subsystem with LiveKit sessions to maintain continuity across voice interactions.

- **Egress service resource intensity.** Recording and streaming (Egress) uses headless Chrome for compositing, which is memory and CPU intensive. This may not be practical for resource-constrained deployments.

## 8) Feature extraction (for master matrix)

- **Repo:** livekit/livekit
- **Primary language:** Go (server), Python (agent framework), TypeScript (client SDK)
- **Interfaces:** WebRTC (audio/video/data), gRPC API, Twirp (HTTP/JSON) API, WebSocket signaling, Webhooks, SIP (phone), WHIP/WHEP (broadcast), Client SDKs (JS, Swift, Kotlin, Flutter, Unity, React), Server SDKs (Go, Python, JS, Ruby, PHP, Rust), CLI (`lk`)
- **Orchestration primitives:** Room (named session with pub/sub tracks), Participant (identity with permissions), Track (audio/video/data stream), Agent Worker (dispatch-on-demand), VoicePipelineAgent (STT->LLM->TTS chain), MultimodalAgent (direct model integration)
- **State/persistence:** Server-side room state in memory + Redis (multi-node). No built-in conversation persistence -- rooms are ephemeral. Egress provides recording for archival. Agent framework maintains local pipeline state per session.
- **HITL controls:** Human participants in rooms alongside AI agents. Voice interruption (barge-in) handling. Data channel messaging for control signals. JWT-scoped permissions per participant.
- **Sandboxing:** JWT token grants with fine-grained permissions (canPublish, canSubscribe, canPublishData, per-source restrictions). No code execution sandboxing (not applicable -- SFU forwards media, does not execute user code).
- **Observability:** Prometheus metrics (`/metrics`), structured logging, OpenTelemetry tracing, connection quality scoring, LiveKit Cloud dashboard with analytics and session replay.
- **Evaluation:** Go test suite for SFU server. Python pytest for agent framework. Agents Playground for manual voice agent testing. No automated voice agent quality evaluation harness.
- **Extensibility:** Plugin packages for STT/LLM/TTS providers (`livekit-plugins-*`). Webhook event system. Custom track processors. Data channel protocols. Server SDKs for custom integrations.

## 9) Evidence links

- https://github.com/livekit/livekit -- Main repository (Go SFU server)
- https://github.com/livekit/agents -- Python agent framework for AI voice/multimodal agents
- https://github.com/livekit/protocol -- Protobuf definitions and shared protocol types
- https://docs.livekit.io/ -- Official documentation
- https://docs.livekit.io/agents/ -- Agent framework documentation
- https://docs.livekit.io/realtime/concepts/architecture/ -- SFU architecture overview
- https://docs.livekit.io/home/get-started/authentication/ -- Token and permission model
- https://docs.livekit.io/agents/voice-agent/voice-pipeline/ -- VoicePipelineAgent documentation
- https://docs.livekit.io/agents/voice-agent/function-calling/ -- Function calling / tool use in agents
- https://docs.livekit.io/agents/plugins/ -- Plugin system documentation
- https://github.com/livekit/agents/tree/main/livekit-plugins -- Plugin source code
- https://docs.livekit.io/home/self-hosting/deployment/ -- Deployment and scaling guide
- https://docs.livekit.io/realtime/egress/overview/ -- Egress (recording/streaming) service
- https://docs.livekit.io/realtime/sip/ -- SIP integration for telephony

---

## 10) AGENT-33 Adaptation Analysis

> *This section focuses on patterns and capabilities relevant to AGENT-33's multi-agent orchestration framework.*

### Recommended Adaptations

#### A. Room-Based Session Model for Multi-Agent Collaboration

**Source pattern:** LiveKit Rooms where multiple participants (human + AI) coexist with pub/sub track semantics.

**AGENT-33 application:** Extend the existing workflow session model with a "collaboration room" concept:
- Multiple agents can be active in a session simultaneously (not just sequential DAG steps)
- Agents publish observations and subscribe to relevant channels
- Human operators can join as participants for real-time oversight
- Data channel semantics for structured inter-agent messaging beyond the current workflow state passing

#### B. Worker Dispatch Model for Agent Scaling

**Source pattern:** Agent workers register capabilities and get dispatched to rooms on demand via the LiveKit server.

**AGENT-33 application:** Evolve the agent registry into a dispatch system:
- Agents register as available workers with declared capabilities
- Workflow steps request agents by capability rather than fixed identity
- Enable horizontal scaling by running multiple agent workers
- Decouple agent lifecycle from workflow lifecycle (agents can serve multiple concurrent workflows)

#### C. Plugin Architecture for Provider Abstraction

**Source pattern:** `livekit-plugins-*` packages with common base classes (`stt.STT`, `llm.LLM`, `tts.TTS`).

**AGENT-33 application:** Formalize the LLM provider abstraction:
- Define a formal `BaseLLMPlugin` interface that all providers implement
- Package providers as separate installable plugins (currently in `llm/ollama.py`, `llm/openai_compat.py`)
- Enable discovery and registration of plugins at startup (similar to agent definition auto-discovery)
- Extend pattern to tool providers, memory backends, and messaging integrations

#### D. Fine-Grained Capability Tokens

**Source pattern:** JWT grants with per-participant permissions (canPublish, canSubscribe, canPublishData, room-specific).

**AGENT-33 application:** Enhance the existing JWT/permission system:
- Issue per-invocation tokens with scoped tool permissions (agent X can use shell but not browser)
- Add resource-level grants (agent can read memory but not write)
- Implement room/session-level isolation (agent token only valid for specific workflow execution)
- Aligns with Phase 14 security hardening goals

#### E. Voice/Multimodal Agent Pipeline (Future Phase)

**Source pattern:** VoicePipelineAgent with STT -> LLM -> TTS chain and interruption handling.

**AGENT-33 application:** For a future phase adding voice capabilities:
- Integrate LiveKit as an infrastructure dependency (run SFU server alongside AGENT-33)
- Build a voice agent type that extends the existing `AgentDefinition` model
- Use `livekit/agents` framework as the voice runtime, bridging to AGENT-33's agent registry
- Connect voice session transcripts to AGENT-33's memory subsystem for persistence
- This would be a significant infrastructure addition -- flag as Phase 22+ candidate

### Implementation Priority

| Adaptation | Impact | Effort | Priority |
|------------|--------|--------|----------|
| C. Plugin Architecture for Providers | High | Medium | 1 |
| D. Fine-Grained Capability Tokens | High | Medium | 2 |
| B. Worker Dispatch Model | High | High | 3 |
| A. Room-Based Session Model | Medium | High | 4 |
| E. Voice/Multimodal Pipeline | Medium | Very High | 5 |

### Non-Applicable Patterns

The following LiveKit patterns are not directly applicable to AGENT-33's current scope:
- WebRTC SFU media routing (Go server, codec negotiation, TURN/STUN, simulcast)
- Egress service with headless Chrome compositing
- SIP gateway for telephony integration
- WHIP/WHEP broadcast protocol handling
- Client-side SDK patterns (mobile/web video rendering)
