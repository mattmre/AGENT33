# S31: ElevenLabs Audio Transport for Voice Sidecar

## Summary

Add ElevenLabs real-time audio transport to the AGENT-33 voice sidecar,
enabling high-quality TTS synthesis via the ElevenLabs API.

## Scope

### New module: `engine/src/agent33/voice/elevenlabs.py`

- **ElevenLabsConfig** -- dataclass holding API key, model ID, voice ID,
  stability/similarity_boost, output format, streaming latency optimization,
  and WebSocket URL template.
- **ElevenLabsTransport** -- async HTTP transport using httpx.AsyncClient:
  - `synthesize(text)` -- HTTP POST to `/v1/text-to-speech/{voice_id}`
  - `synthesize_stream(text)` -- streaming HTTP TTS via chunked transfer
  - `list_voices()` -- GET `/v1/voices`
  - `get_voice(voice_id)` -- GET `/v1/voices/{voice_id}`
  - `health_check()` -- verify API key validity and connectivity
- **ElevenLabsTransportError** -- structured error with status_code and detail
- **ElevenLabsArtifactStore** -- local filesystem persistence for synthesized
  audio, with per-session directories and JSON manifests.

### Voice sidecar integration: `engine/src/agent33/voice/app.py`

Three new endpoints wired into the sidecar FastAPI app:

- `POST /v1/voice/synthesize` -- synthesize text to audio, optionally persisting
  the artifact to a session.
- `GET /v1/voice/voices` -- list available ElevenLabs voices.
- `GET /v1/voice/health/elevenlabs` -- check ElevenLabs connectivity.

The `create_voice_sidecar_app` factory accepts optional `elevenlabs_config` and
`elevenlabs_artifact_store` parameters. When no API key is configured, the
transport is `None` and ElevenLabs endpoints return 503.

### Config additions: `engine/src/agent33/config.py`

Four new settings under the `voice_elevenlabs_*` prefix:

| Setting | Type | Default |
|---------|------|---------|
| `voice_elevenlabs_enabled` | `bool` | `False` |
| `voice_elevenlabs_api_key` | `SecretStr` | `""` |
| `voice_elevenlabs_default_voice_id` | `str` | `""` |
| `voice_elevenlabs_model_id` | `str` | `"eleven_multilingual_v2"` |

## Design decisions

1. **No new dependencies.** ElevenLabs is accessed via `httpx`, which is already
   a core dependency. No `elevenlabs` Python SDK is added.
2. **SecretStr for API key** in config.py, matching project conventions.
3. **Streaming uses chunked HTTP**, not WebSocket client, to avoid adding a
   WebSocket client library dependency. The WebSocket URL is stored in config
   for future use when a WS client is available.
4. **Artifact store** uses the same `artifacts_dir` root as the sidecar service,
   with an `elevenlabs/` subdirectory.

## Test coverage

File: `engine/tests/test_elevenlabs_transport.py`

- Config validation (defaults, boundary values, invalid ranges)
- Transport: synthesize success, API error, network error
- Transport: synthesize_stream success, API error
- Transport: list_voices success, API error
- Transport: get_voice success, API error
- Transport: health_check (ok, failed, no key)
- ArtifactStore: save, list, get, missing artifact
- Sidecar endpoint: synthesize via app, voices via app, health/elevenlabs
- Config integration: ElevenLabs settings in Settings model
