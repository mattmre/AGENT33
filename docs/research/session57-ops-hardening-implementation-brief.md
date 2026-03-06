# Session 57 Operational Hardening Implementation Brief

**Date:** 2026-03-06
**Scope:** Phase 30 trace tuning, Phase 31 backup/restore validation, Phase 32 cross-service tenant verification, Phase 33 marketplace/distribution integration, and Phase 35 voice daemon implementation.

## Key Findings
- Phase 30 core routing exists, but production telemetry is weakly correlated and current effort-routing exports are too sparse for real tuning.
- Phase 31 persistence, backup/restore endpoints, and corruption handling exist, but production-scale validation and operator hardening are incomplete.
- Phase 32 tenant verification is inconsistent across routes/services; this is the foundational hardening item for the rest of the operational backlog.
- Phase 33 has local pack loading, provenance, and conflict primitives, but no marketplace/distribution implementation and no marketplace-grade trust model.
- Phase 35 has multimodal policy presets and a `LiveVoiceDaemon` scaffold, but the daemon remains a stub and is not wired into runtime lifecycle/auth flows.

## Dependency-Ordered Plan
1. Phase 32 tenant-verification foundation across routes, services, and connector metadata.
2. Phase 30 production trace tuning and richer effort-routing telemetry.
3. Phase 31 backup/restore hardening and production-scale validation.
4. Phase 33 trust/persistence hardening, then marketplace/distribution integration.
5. Phase 35 voice daemon implementation and policy tuning.

## Recommended PR Boundaries
- PR 1: Phase 32 tenant-verification foundation
- PR 2: Phase 30 telemetry + trace tuning
- PR 3: Phase 31 backup/restore hardening + validation
- PR 4: Phase 33 trust/persistence hardening
- PR 5: Phase 33 marketplace/distribution integration
- PR 6: Phase 35 voice daemon implementation + policy tuning

## Key Files
- Phase 30: `api/routes/agents.py`, `agents/runtime.py`, `agents/effort.py`, `observability/effort_telemetry.py`, `alerts.py`, `metrics.py`, `main.py`
- Phase 31: `improvement/persistence.py`, `improvement/service.py`, `improvement/models.py`, `api/routes/improvements.py`, `config.py`
- Phase 32: `security/permissions.py`, `security/middleware.py`, `api/routes/improvements.py`, `traces.py`, `multimodal.py`, `packs.py`, `connectors/*`, `tools/mcp_bridge.py`, `tools/mcp_client.py`
- Phase 33: `packs/registry.py`, `packs/provenance.py`, `packs/conflicts.py`, `packs/models.py`, `api/routes/packs.py`, `config.py`
- Phase 35: `multimodal/voice_daemon.py`, `multimodal/models.py`, `multimodal/service.py`, `multimodal/adapters.py`, `api/routes/multimodal.py`, `main.py`

## Recommended New Research Docs
- `docs/research/session57-phase32-cross-service-tenant-verification.md`
- `docs/research/session57-phase30-production-trace-tuning.md`
- `docs/research/session57-phase31-backup-restore-validation-matrix.md`
- `docs/research/session57-phase33-marketplace-integration.md`
- `docs/research/session57-phase35-live-voice-architecture.md`
- `docs/operators/voice-daemon-runbook.md`

## Highest-Risk Integration Points
- Cross-tenant leakage remains the top operational risk until Phase 32 is hardened.
- Backup/restore endpoints are under-protected and need operator-only handling plus safer snapshot semantics.
- Current Phase 30 telemetry lacks stable correlation fields for meaningful production tuning.
- Marketplace trust/provenance is not production-ready yet.
- Voice daemon work has the largest runtime blast radius because it introduces long-lived multimodal sessions and continuous auth/policy concerns.
