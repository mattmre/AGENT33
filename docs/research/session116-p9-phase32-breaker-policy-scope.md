# Session 116 P9 - Phase 32 Breaker Policy Contract

## Scope Lock

Cluster `A2` is already largely implemented on `main` through PR `#311`
(`e50bd72`), which delivered the breaker tuning, shared breaker registry,
metrics collector wiring, and structured logging backlog.

The remaining honest gap is operator predictability:

- the live connector API snapshot does not expose the effective cooldown policy
  after progressive backoff is applied
- the snapshot response model still carries a stale `half_open_success_threshold`
  default from the pre-`#311` implementation
- there is no operator-facing runbook that explains the connector middleware
  order, retry semantics, and how to interpret breaker cooldown data from
  `/v1/connectors`

## Bounded Deliverables

1. Extend the circuit-breaker snapshot/API contract so operators can inspect:
   - base recovery timeout
   - effective recovery timeout after backoff
   - max recovery timeout cap
   - remaining cooldown while open
2. Align snapshot model defaults with the live breaker defaults on `main`.
3. Add an operator-facing connector boundary runbook and cross-link it from the
   existing operator docs surface.
4. Add regression tests for the runtime snapshot contract and the new docs.

## Explicit Non-Goals

- no new connector adoption work
- no retry algorithm redesign
- no Redis-backed breaker state
- no new dashboard or operator API endpoints beyond the existing snapshot shape
