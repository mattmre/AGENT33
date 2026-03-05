# Session 54 Research — Agent Orchestration Capability Gap Matrix (2026-03-05)

## Evaluation Rubric

- **Delta state**: `missing` | `partial` | `present` | `superseded`
- **Scores**:
  - Impact (I): 1-10
  - Feasibility (F): 1-10
  - Risk (R): 1-10 (higher = riskier)
- **Weighted priority**: `0.5 * I + 0.3 * F + 0.2 * (11 - R)`

## AGENT-33 Bucket Mapping

| Bucket | Current AGENT-33 posture | Landscape pressure | Delta state |
| --- | --- | --- | --- |
| Agents / Runtime | Mature runtime + capability taxonomy + routed invocation | Lighter dynamic-handoff patterns and optimized fanout | partial |
| Workflows | DAG execution, retries/timeouts, scheduling, checkpoints | Strong demand for persistent workflow control-plane state | partial |
| Skills | Registry, loader, matching, injection, packs | Marketplace/distribution trust and provenance depth | partial |
| Tooling | Schema-aware tools, governance, allowlists, MCP bridge | More explicit supervised approval workflows for destructive actions | partial |
| Memory / RAG | Hybrid retrieval stack (vector + BM25 + RRF) and progressive recall | Richer modular retrieval stage composition and diagnostics | partial |
| Security | JWT/API-key auth, policy checks, injection detection, boundaries | Durable HITL approval traceability and operator flows | partial |
| Evaluation | Golden tasks/cases, gates, regression detection, benchmark adapters | Broader comparative and scenario depth remains | partial |
| Autonomy | Budget lifecycle + preflight + runtime enforcer | Persistence durability and deeper operator tooling | partial |
| Observability | Trace and failure taxonomy, metrics and alerts | Persistent trace store and richer export integration | partial |
| Release | Lifecycle/checklists/sync/rollback flows | Stronger release-memory durability and trust controls | partial |

## Priority Candidate Backlog

| Candidate | I | F | R | Weighted priority | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| Durable orchestration control-plane persistence | 10 | 6 | 7 | 7.0 | High-value resilience across workflow/trace/autonomy/release services |
| HITL approval workflow for ask/supervised operations | 9 | 7 | 6 | 7.4 | Completes governance loop and operator safety |
| Modular retrieval-pipeline stages and diagnostics | 8 | 7 | 5 | 7.1 | Strong haystack-aligned ingestion target |
| Skill/pack provenance hardening | 8 | 5 | 7 | 5.9 | Strategic but higher integration cost |
| Dynamic lightweight agent handoff mode | 7 | 6 | 6 | 6.1 | Useful runtime ergonomics improvement |

## Implementation Wave Outcome (This Session)

Implemented now to enable continuous ingestion:

1. **Competitive intake batch ingestion API**
   - `POST /v1/improvements/intakes/competitive/repos`
   - Converts harvested repo metadata into normalized `ResearchIntake` records.
2. **Feature-candidate scoring/prioritization API**
   - `POST /v1/improvements/feature-candidates/score`
   - Returns full scored list + prioritized top-N candidates.
3. **Reusable ingestion module**
   - `engine/src/agent33/improvement/repo_ingestion.py`
   - Shared models + deterministic scoring + intake construction helpers.

## Next Strategic Deltas (Planned PR slices)

1. Durable orchestration state store (workflow + trace + autonomy + release)
2. Real approval-lifecycle service for ask/destructive workflows
3. Modular retrieval pipeline and retrieval-stage observability

