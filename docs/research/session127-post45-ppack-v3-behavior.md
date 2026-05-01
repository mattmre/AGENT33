# Session 127 Research: POST-4.5 P-PACK v3 Behavior Contract

**Date:** 2026-04-17  
**Scope:** lock the `POST-4.5` behavior changes that the merged P-PACK v3 A/B harness should evaluate

## Decision

`POST-4.5` uses the existing P-PACK v3 A/B assignment to change how session-scoped packs are resolved at runtime:

- **control** sessions keep the current P-PACK v1 behavior
- **treatment** sessions use a new source-aware resolution order when `ppack_v3_enabled` is enabled

## Why this shape

The repository has clear pack application surfaces but no standalone written v3 manifest/schema change:

- `PackRegistry.enable_for_session(...)`
- `PackSharingService.apply_shares(...)`
- `PackRegistry.get_session_packs(...)`
- `PackRegistry.get_session_prompt_addenda(...)`
- `PackRegistry.get_session_tool_config(...)`
- `AgentRuntime._inject_pack_addenda(...)`
- `AgentRuntime._get_pack_tool_config(...)`

The merged POST-4.4 harness already assigns deterministic `control` / `treatment` variants and records them in outcome metadata, so the safest POST-4.5 slice is to route pack behavior through that existing split.

## P-PACK v3 rule set

### Control path

- Preserve the existing deterministic P-PACK v1 order: session packs are resolved by pack name
- Prompt addenda and tool-config merging continue to follow that name-sorted order

### Treatment path

- Only active when both conditions are true:
  1. `ppack_v3_enabled` is enabled
  2. the current session is assigned to the `treatment` variant
- Resolve session packs by **source-aware application precedence**:
  - workflow-shared packs (`pack_ref` / `pack_refs`) apply first
  - explicit session-enabled packs apply after shared packs
  - preserve activation order within each source group
- Prompt addenda and tool-config merging follow that resolved order

## Practical effect

This makes operator-selected packs higher-precedence than workflow-shared packs without inventing a new pack manifest field. It also gives the A/B harness a concrete behavior delta to compare:

- control: legacy name-sorted pack application
- treatment: source-aware pack precedence

## Non-goals

- No new pack manifest schema
- No new pack priority field
- No tenant-wide enablement changes
- No behavioral change for control sessions or when `ppack_v3_enabled` is off

## Validation target

- `pytest tests/test_ppack_v3_ab.py`
- existing P-PACK v1 / v2 regression tests
- runtime regression coverage for pack addenda and tool-config narrowing
