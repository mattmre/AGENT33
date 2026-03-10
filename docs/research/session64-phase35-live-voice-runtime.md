# Session 64 — Phase 35 Live Voice Runtime

## Goal

Replace the Phase 35 voice daemon stub-only surface with a real tenant-scoped runtime control plane that:

- enforces multimodal policy for live voice sessions
- exposes authenticated API routes for start/list/health/stop
- wires voice session lifecycle into FastAPI startup/shutdown
- connects the frontend voice panel to the backend instead of local-only UI state

## What Was Missing

On the nightly-merge baseline, `LiveVoiceDaemon` existed but only as a lifecycle stub:

- no session registry
- no tenant-scoped API
- no policy fields for long-lived voice sessions
- no app-lifespan shutdown handling
- no frontend/server wiring

That meant the "Voice Call" tab looked interactive but did not actually control anything on the backend.

## Implementation Decisions

### 1. Keep transport explicit

The repository still does not include the `livekit-agents` runtime dependency. Rather than fake WebRTC media transport, the implementation now supports:

- `stub` transport: fully functional control plane for session lifecycle and UI integration
- `livekit` transport: explicit runtime error until the dependency is installed

This avoids shipping an interface that pretends media transport works when it does not.

### 2. Voice sessions are governed by tenant policy

`MultimodalPolicy` now includes:

- `voice_enabled`
- `max_voice_concurrent_sessions`
- `max_voice_session_seconds`

These settings are enforced before daemon startup.

### 3. Multimodal service owns voice lifecycle

`MultimodalService` now tracks:

- `VoiceSession` records
- daemon instances per session
- health snapshots
- shutdown cleanup for active sessions

This keeps the voice control plane inside the existing multimodal subsystem instead of creating a parallel voice service.

### 4. Frontend continuity is session-aware

`LiveVoicePanel` now hydrates an existing active session for the authenticated tenant on load, then uses backend routes to connect/disconnect.

## API Surface Added

- `POST /v1/multimodal/voice/sessions`
- `GET /v1/multimodal/voice/sessions`
- `GET /v1/multimodal/voice/sessions/{session_id}`
- `GET /v1/multimodal/voice/sessions/{session_id}/health`
- `POST /v1/multimodal/voice/sessions/{session_id}/stop`

## Remaining Dependency Gap

True low-latency media handling still requires the LiveKit agent runtime. The current implementation intentionally stops at lifecycle/auth/policy integration until that dependency is added.

That gap is explicit in:

- `engine/src/agent33/multimodal/voice_daemon.py`
- runtime config validation for `voice_daemon_transport=livekit`

## Validation Plan

Backend:

- `python -m pytest tests/test_voice_daemon.py tests/test_multimodal_api.py -q`
- `python -m ruff check src/agent33/config.py src/agent33/main.py src/agent33/api/routes/multimodal.py src/agent33/multimodal/models.py src/agent33/multimodal/service.py src/agent33/multimodal/voice_daemon.py tests/test_voice_daemon.py tests/test_multimodal_api.py`

Frontend:

- `npm run test -- LiveVoicePanel.test.tsx`
- `npm run lint`
