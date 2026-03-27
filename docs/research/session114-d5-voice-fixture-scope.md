# Session 114 -- D5 Voice Sidecar Fixture Scope

## Goal

Add one narrow regression that proves the current `main` multimodal voice path
can drive a real sidecar-backed session end to end without broadening into
new product behavior.

## Live Baseline

- The multimodal service already supports `transport="sidecar"` and can accept
  a daemon factory override.
- The standalone voice sidecar already persists `session.json` and
  `events.jsonl` per session.
- `config/voice/voices.json` is checked in and should remain the canonical
  voice catalog for this fixture.

## Narrowest Credible Test Path

The right regression is not a new feature slice. It is a single integration
test that drives the real sidecar app through `ASGITransport` and lets the main
multimodal API talk to it through `VoiceSidecarClient` and
`SidecarVoiceDaemon`.

### Proposed scenario

1. Load the checked-in `config/voice/voices.json` into a real
   `VoiceSidecarService`.
2. Build a standalone sidecar FastAPI app with `create_voice_sidecar_app(...)`.
3. Inject a `SidecarVoiceDaemon` through
   `_service.configure_voice_runtime(transport="sidecar", url="http://testserver", daemon_factory=...)`.
4. Start a voice session through the main multimodal API.
5. Assert the session health response includes:
   - a `sidecar_session_id`
   - `details.health.status == "ok"`
   - `details.health.persona_count == 2` to prove the checked-in voice catalog loaded
6. Assert the sidecar wrote `session.json` and `events.jsonl` on disk.
7. Stop the session through the main API and verify the sidecar manifest flips
   to `stopped`.

## Why This Is The Right Scope

- It validates the real composition boundary that remains after the sidecar
  split, not just the route surface.
- It stays bounded to one main-path regression plus one short note update.
- It uses real checked-in config and real ASGI plumbing, but does not add any
  new transport modes, persistence formats, or sidecar APIs.
- It directly covers the residual risk that the main API and sidecar session
  lifecycle diverge on the current baseline.
- It intentionally does not claim requester-attribution or audio-media
  propagation coverage; those would be separate follow-up work.

## Files In Scope

- `engine/tests/test_multimodal_api.py`
- `docs/research/session114-d5-voice-fixture-scope.md`

## Non-Goals

- No production runtime refactor.
- No new sidecar endpoints.
- No LiveKit or provider integration expansion.
- No wider multimodal API coverage beyond this single regression.
- No claim of real STT/TTS media validation; current `main` has no checked-in
  audio media fixtures for that.

## Validation Plan

- `$env:PYTHONPATH='D:\\GITHUB\\AGENT33\\worktrees\\session114-p5-voice-sidecar-fixture\\engine\\src'; python -m pytest tests/test_multimodal_api.py -q --no-cov`
- `python -m ruff check tests/test_multimodal_api.py`
- `python -m ruff format --check tests/test_multimodal_api.py`
