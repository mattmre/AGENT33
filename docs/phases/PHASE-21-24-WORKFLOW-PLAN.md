# Phase 21-24 Workflow Plan (Extensibility + Product Access)

Purpose: define sequencing and review gates for post-core phases that focus on extensibility, frontend productization, and operator access.

## Dependency Chain
1. Phase 21 (Extensibility patterns) establishes integration guidance and artifact relationships.
2. Phase 22 (Unified UI platform) delivers first-party application access to runtime features.
3. Phase 23 (future) can extend workspace/user models after UI baseline is stable.
4. Phase 24 (future) can extend plugin/marketplace and UX hardening.

## Task Mapping (Phase 21-24)

| Phase | Task ID | Owner | Dependencies | Outputs |
| --- | --- | --- | --- | --- |
| 21 | T27 | Research + Architect | Phase 20 complete | Extensibility patterns and artifact relationship model |
| 22 | T28 | Product + Runtime | Phase 21, 14, 16 | Frontend app, auth flows, containerized hosting |
| 23 | T29 | Security + Platform | Phase 22 | Workspace/user lifecycle hardening |
| 24 | T30 | Product + Ecosystem | Phase 23 | Plugin/extension UX and operator polish |

## Review Gates
- Phase 22 requires:
  - security review (token/API-key handling)
  - QA review (end-to-end feature coverage)
  - operations review (local/VPS deployment evidence)
- Future phases must preserve backward compatibility of Phase 22 APIs/UI contracts.

## Notes
- This plan is additive to `PHASE-11-20-WORKFLOW-PLAN.md`.
- If future phases are not yet implemented, keep them as placeholders and focus on complete verification for active phase work.

