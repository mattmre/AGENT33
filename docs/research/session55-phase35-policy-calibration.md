# Session 55 — Phase 35 Multimodal Policy Calibration & Voice Daemon Lifecycle

## Context

Phase 35 (Multimodal Async-Governance Convergence) landed the core connector-boundary wiring for all three multimodal adapters (STT, TTS, Vision) in prior sessions.  This session addresses the two remaining items from the Phase 35 roadmap:

1. **Policy default calibration** — documenting *why* each default value was chosen and providing per-modality recommended presets.
2. **Voice daemon lifecycle completion** — fleshing out the `LiveVoiceDaemon` scaffold with a proper typed interface (start / stop / health_check / process / synthesize) ready for LiveKit SDK wiring.

## Policy Calibration

### Default Policy Analysis

| Field | Default | Rationale |
|---|---|---|
| `max_text_chars` | 5 000 | ≈ 1 250 tokens.  Covers most TTS prompts and vision text instructions while blocking accidental megabyte payloads. |
| `max_artifact_bytes` | 5 000 000 (5 MB) | Fits a high-resolution JPEG or a short audio clip.  Keeps worker memory predictable. |
| `max_timeout_seconds` | 300 (5 min) | Accommodates slow VLM inference (e.g. GPT-4 Vision on complex images) while bounding runaways. |
| `allowed_modalities` | all three | Permissive default; operators restrict for cost/compliance via `set_policy`. |

### Recommended Per-Modality Presets (`RECOMMENDED_POLICIES`)

These are *advisory* — not auto-enforced.  Deployment tooling or operators can use them as starting points.

| Preset | max_text_chars | max_artifact_bytes | max_timeout_seconds | allowed_modalities |
|---|---|---|---|---|
| `stt` | 0 | 10 MB | 120 s | speech_to_text only |
| `tts` | 10 000 | 0 | 60 s | text_to_speech only |
| `vision` | 2 000 | 20 MB | 300 s | vision_analysis only |

**Design decisions:**
- STT needs no text input (`max_text_chars=0`) but handles larger audio files (10 MB for multi-minute recordings).
- TTS needs generous text input (10 000 chars ≈ 2 500 tokens) but no binary artifact.  Synthesis is fast, so 60 s timeout suffices.
- Vision accepts large images (20 MB for high-res screenshots/photos) with a short text prompt.  VLM inference can be slow, so the full 300 s timeout is retained.

## Voice Daemon Lifecycle

### Interface Surface

```
LiveVoiceDaemon(room_name, url, api_key, api_secret)
  async start()                          → None
  async stop()                           → None
  health_check()                         → bool
  async process_audio_chunk(chunk: bytes) → str | None
  async synthesize_speech(text: str)     → bytes | None
```

### Design Choices

- **Async lifecycle** — `start()` and `stop()` are async to match the expected LiveKit SDK connect/disconnect coroutines.
- **Sync `health_check()`** — health probes should be fast and non-blocking; reading a boolean flag is O(1).
- **Stub returns** — both processing methods return `None` to signal "no output yet" which is also valid semantics for partial transcription (no final result available).
- **Structured logging** — migrated from stdlib `logging` to project-standard `structlog` with event-keyed messages (`voice_daemon.starting`, etc.) for consistent observability.
- All stub methods carry `# TODO: Wire LiveKit SDK when dependency is added` for grep-ability.

### LiveKit Wiring Plan (Deferred)

When the `livekit-agents` dependency is added:

1. `start()` will create a `VoicePipelineAgent` with VAD + STT + LLM + TTS plugins and connect to the room.
2. `process_audio_chunk()` will push raw PCM/Opus frames into the agent's ingest buffer.
3. `synthesize_speech()` will call the TTS plugin directly and return encoded audio.
4. `stop()` will disconnect the room participant and release resources.
5. `health_check()` will additionally verify the WebRTC peer connection state.

## Test Coverage

- `engine/tests/test_voice_daemon.py` — 9 tests covering:
  - Start/stop lifecycle and idempotency
  - `health_check()` returns correct boolean in each state
  - `process_audio_chunk()` returns `None` (stub)
  - `synthesize_speech()` returns `None` (stub)
- Existing regression suites (`test_multimodal_api.py`, `test_connector_boundary_multimodal_adapters.py`) remain green — policy model changes are additive only.

## Files Modified

| File | Change |
|---|---|
| `engine/src/agent33/multimodal/models.py` | Added docstrings to `MultimodalPolicy` fields; added `RECOMMENDED_POLICIES` dict |
| `engine/src/agent33/multimodal/voice_daemon.py` | Completed lifecycle: `start`, `stop`, `health_check`, `process_audio_chunk`, `synthesize_speech`; migrated to structlog |
| `engine/tests/test_voice_daemon.py` | New — lifecycle + stub behaviour tests |
| `docs/research/session55-phase35-policy-calibration.md` | This document |
