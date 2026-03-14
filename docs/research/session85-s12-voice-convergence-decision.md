# Session 85 - S12 Phase 35 / 48 Voice Convergence Decision

## Goal

Decide whether AGENT-33 should finish direct in-process `livekit` transport inside the
Phase 35 voice scaffold, or keep Phase 35 as a compatibility control plane and reserve
real media transport for the Phase 48 voice sidecar.

## Current Baseline

- Phase 35 already shipped the operator control plane:
  - tenant-scoped voice session routes
  - multimodal policy enforcement
  - startup/shutdown lifecycle handling
  - frontend wiring through `LiveVoicePanel`
- The current runtime still uses a stub daemon:
  - `engine/src/agent33/multimodal/service.py`
  - `engine/src/agent33/multimodal/voice_daemon.py`
- Before this slice, the engine allowed `VOICE_DAEMON_TRANSPORT=livekit` to pass initial
  service validation when credentials were present, but the start path still failed later
  inside the stub daemon.

## Repo Research Refresh

### What the current code already gives us

- `MultimodalService` provides the control-plane shape that Phase 48 can preserve:
  - session registry
  - tenant scoping
  - policy checks
  - shutdown cleanup
- `LiveVoiceDaemon` is still explicitly a scaffold, not a real media pipeline.
- The operator runbook already treats `stub` as the only practical mode today.

### What the roadmap says

- Phase 48 explicitly calls for a standalone voice sidecar, not a larger in-process
  LiveKit buildout.
- Session 70 planning already warned that finishing direct `livekit` wiring in the
  existing scaffold would likely create throwaway work because the sidecar is the real
  long-term operator target.

## External Research Refresh

Primary sources checked on 2026-03-14:

- LiveKit Agents docs overview: https://docs.livekit.io/agents/
- LiveKit voice AI quickstart: https://docs.livekit.io/agents/start/voice-ai/
- LiveKit Agents repository: https://github.com/livekit/agents
- `livekit-agents` package metadata: https://pypi.org/project/livekit-agents/

### Confirmed facts

- LiveKit now has an official agent stack with both docs and a maintained package.
- The current published `livekit-agents` package is compatible with Python 3.11, so the
  AGENT-33 engine can technically install it.
- The official LiveKit model is still a dedicated realtime agent runtime that joins rooms
  and manages media/session orchestration as its own process boundary.

## Decision

Do not implement direct in-process `livekit` transport inside the existing Phase 35
multimodal service.

Treat Phase 35 as the durable control-plane compatibility layer and Phase 48 as the only
place where real media transport should land.

## Why

1. The architecture mismatch is real.
   LiveKit's official agent model is a dedicated realtime runtime, while the current
   AGENT-33 Phase 35 code is an in-process FastAPI-attached control plane.

2. Phase 48 already defines the correct destination.
   The roadmap wants a standalone sidecar with playback abstraction, graceful shutdown,
   status reporting, and operator health surfaces. Building direct `livekit` media inside
   the current scaffold would duplicate work and complicate migration.

3. The current control plane is already useful without media transport.
   The existing routes, policy checks, and tenant/session lifecycle can stay as the API
   contract that the sidecar later satisfies behind the scenes.

4. The current operator behavior was misleading.
   Allowing `livekit` through early validation implied that valid credentials were the
   missing piece, even though the actual design decision is broader: this runtime is not
   where LiveKit transport should land.

## Minimal Implementation for This Slice

This slice should only:

- document the decision clearly
- reject direct `livekit` transport before a failed session record is created
- preserve `stub` as the only supported current runtime mode

It should not:

- add `livekit-agents` to dependencies
- start a sidecar implementation
- change the public voice session API surface
- attempt realtime media transport in the FastAPI process

## Implementation Notes

- `MultimodalService._validate_voice_runtime()` now rejects `livekit` transport with a
  deterministic Phase 48 sidecar message.
- The operator runbook now reflects that `livekit` is intentionally deferred, not merely
  waiting on missing credentials.
- The direct daemon error message now matches the architectural decision if the class is
  instantiated outside the service guard.

## Phase 48 Carry-Forward Contract

Phase 48 should:

- keep the current tenant-scoped voice session routes if possible
- replace the daemon internals with a sidecar adapter or client
- expose sidecar health through operator/health surfaces
- treat current `voice_daemon_*` settings as compatibility input until a dedicated sidecar
  config surface is ready

## Validation

Targeted checks for this decision slice:

- `python -m pytest tests/test_voice_daemon.py tests/test_multimodal_api.py -q --no-cov`
- `python -m ruff check src/agent33/multimodal/service.py src/agent33/multimodal/voice_daemon.py tests/test_multimodal_api.py tests/test_voice_daemon.py`
- `python -m ruff format --check src/agent33/multimodal/service.py src/agent33/multimodal/voice_daemon.py tests/test_multimodal_api.py tests/test_voice_daemon.py`
- `python -m mypy src/agent33/multimodal/service.py src/agent33/multimodal/voice_daemon.py --config-file pyproject.toml`
