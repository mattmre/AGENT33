# S32: LiveKit Sidecar Real Media Transport

## Decision

Per the S12 architecture decision memo, real LiveKit media transport goes in
the voice sidecar process (not the main AGENT-33 runtime). This slice
implements the LiveKit transport layer inside `engine/src/agent33/voice/`.

## Scope

### New file: `engine/src/agent33/voice/livekit_transport.py`

- `LiveKitConfig` dataclass with validation (api_key, api_secret, ws_url,
  room_prefix, default_codec, max_participants, token_ttl_seconds)
- `LiveKitRoom` and `LiveKitParticipant` data models
- `LiveKitTransport` class with:
  - JWT access token generation (PyJWT-based, LiveKit-compatible claims)
  - Room CRUD (create, list, get, delete) with in-memory tracking
  - Participant management (add, list, remove) with capacity enforcement
  - Health check and snapshot

### Modified: `engine/src/agent33/voice/app.py`

Six new sidecar API endpoints:

| Method   | Path                                        | Purpose             |
|----------|---------------------------------------------|---------------------|
| POST     | `/v1/voice/livekit/rooms`                   | Create room         |
| GET      | `/v1/voice/livekit/rooms`                   | List rooms          |
| DELETE   | `/v1/voice/livekit/rooms/{name}`            | Delete room         |
| POST     | `/v1/voice/livekit/token`                   | Generate JWT token  |
| GET      | `/v1/voice/livekit/rooms/{name}/participants` | List participants |
| GET      | `/v1/voice/health/livekit`                  | Health check        |

### Modified: `engine/src/agent33/config.py`

Four new settings fields:

- `voice_livekit_enabled: bool = False`
- `voice_livekit_api_key: SecretStr`
- `voice_livekit_api_secret: SecretStr`
- `voice_livekit_ws_url: str`

### Modified: `engine/src/agent33/multimodal/voice_daemon.py`

Updated the deferred-livekit message to indicate that sidecar transport is now
available when configured.

## Non-goals

- No `livekit-agents` SDK dependency (this is transport infrastructure)
- No real LiveKit server HTTP calls (the sidecar manages state in-memory)
- No changes to the main runtime lifespan or agent runtime

## Token Format

The generated JWT follows the LiveKit access token specification:

```json
{
  "iss": "<api_key>",
  "sub": "<identity>",
  "iat": <timestamp>,
  "nbf": <timestamp>,
  "exp": <timestamp + ttl>,
  "jti": "<unique-id>",
  "video": {
    "room": "<room_name>",
    "roomJoin": true,
    "canPublish": true,
    "canSubscribe": true,
    "canPublishData": true
  }
}
```

## Testing

Full test coverage in `engine/tests/test_livekit_transport.py` covering:

- Config validation (defaults, custom, boundary errors)
- Token generation (JWT structure, claims, TTL, error cases)
- Room CRUD (create with prefix, list, delete, duplicate detection)
- Participant lifecycle (add, list, remove, capacity enforcement)
- Health check (configured vs unconfigured)
- All six sidecar API endpoints via httpx ASGITransport
- Config integration (Settings model validation)
