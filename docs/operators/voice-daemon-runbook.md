# Voice Daemon Runbook

## Purpose

Operate the Phase 35 live voice control plane safely until full LiveKit media transport is enabled.

## Current Runtime Modes

- `stub`: session lifecycle works end to end for UI, policy, auth, and shutdown handling
- `livekit`: intentionally blocked unless the runtime dependency is installed and configured

## Required Engine Settings

- `VOICE_DAEMON_ENABLED=true|false`
- `VOICE_DAEMON_TRANSPORT=stub|livekit`
- `VOICE_DAEMON_URL`
- `VOICE_DAEMON_API_KEY`
- `VOICE_DAEMON_API_SECRET`
- `VOICE_DAEMON_ROOM_PREFIX`
- `VOICE_DAEMON_MAX_SESSIONS`

For local validation, use:

```env
VOICE_DAEMON_ENABLED=true
VOICE_DAEMON_TRANSPORT=stub
VOICE_DAEMON_ROOM_PREFIX=agent33-voice
VOICE_DAEMON_MAX_SESSIONS=25
```

## Tenant Policy Controls

Use the multimodal tenant policy endpoint to tune voice access:

- `voice_enabled`
- `max_voice_concurrent_sessions`
- `max_voice_session_seconds`

`max_voice_session_seconds` is currently recorded on each session for operator budgeting,
but the stub runtime does not auto-expire sessions yet. Stop or reconnect sessions
manually when they exceed the expected duration.

Example:

```json
{
  "voice_enabled": true,
  "max_voice_concurrent_sessions": 1,
  "max_voice_session_seconds": 1800
}
```

## Operator Actions

### List sessions

`GET /v1/multimodal/voice/sessions`

Use this to:

- find currently active tenant-scoped sessions
- locate a `session_id` before deeper inspection or stop requests

### Get session details

`GET /v1/multimodal/voice/sessions/{session_id}`

Use this to inspect:

- session state
- room name
- transport mode
- last recorded startup error, if any

### Start a session

`POST /v1/multimodal/voice/sessions`

Expected result:

- HTTP `201`
- session state `active`
- transport `stub` or configured transport

### Inspect session health

`GET /v1/multimodal/voice/sessions/{session_id}/health`

Use this to confirm:

- session state
- daemon health boolean
- transport mode
- basic daemon counters

### Stop a session

`POST /v1/multimodal/voice/sessions/{session_id}/stop`

Expected result:

- HTTP `200`
- session state `stopped`

## Failure Modes

### `503 voice runtime is disabled`

Cause:

- `VOICE_DAEMON_ENABLED=false`

Resolution:

- enable the runtime or leave the voice tab disabled for the environment

### `503 livekit transport is configured without complete runtime credentials`

Cause:

- `VOICE_DAEMON_TRANSPORT=livekit` without `VOICE_DAEMON_URL`, `VOICE_DAEMON_API_KEY`,
  or `VOICE_DAEMON_API_SECRET`

Resolution:

- complete the runtime settings or switch back to `stub`

### `503 voice runtime could not start session`

Cause:

- the configured transport failed during daemon startup
- `livekit` was selected before the runtime dependency wave was installed

Resolution:

- inspect engine logs for the specific startup failure
- switch back to `stub` until the LiveKit runtime lands

### `400 voice session limit exceeded`

Cause:

- tenant hit `max_voice_concurrent_sessions`

Resolution:

- stop the active session or raise the policy limit explicitly

## Shutdown Behavior

Active voice daemon sessions are stopped during FastAPI lifespan shutdown. This prevents stale active sessions from surviving process restarts inside the in-memory runtime.
