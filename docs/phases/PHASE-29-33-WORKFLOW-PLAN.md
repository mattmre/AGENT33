# Phase 29-33 Workflow Plan (Agent Intelligence + Extensibility)

Purpose: define sequencing and review gates for PAI-inspired improvement phases that enhance agent reasoning, adaptive execution, continuous learning, event-driven extensibility, and ecosystem distribution.

Research basis: `docs/research/pai-development-principles-analysis.md`

## Dependency Chain (Revised — Parallelized)

```
Phase 29 (Reasoning)
  ├── 29.1-29.2 (core) ──→ Phase 30 (Routing) ──┐
  │                                                ├──→ Phase 32 (Hooks, Connectors, Circuit Breakers)
  └── 29.1-29.2 (core) ──→ Phase 31 (Learning) ──┘           │
                                                          Phase 33
                                                     (Packs & Distribution)

  Note: Phase 32.1 (middleware framework) and 32.7 (circuit breakers) have no
  upstream dependencies and can start as independent early work.
```

1. Phase 29 (Agent Reasoning Protocol) establishes structured reasoning (Agno NextAction FSM), ISC tracking (CrewAI GuardrailResult interface), and constraint extraction. **Stage 29.1-29.2 as P0** to unblock downstream.
2. Phase 30 (Adaptive Execution & Deterministic Routing) adds effort classification (heuristic-first), deterministic-first resolution, dynamic prompt composition, and cost-aware model selection. Depends on 29.1-29.2 only.
3. Phase 31 (Continuous Learning & Signal Capture) builds closed learning loop with signal capture (Langfuse schema), learning extraction (DSPy SIMBA), and steering rules. Depends on 29.1-29.2 only. **Runs in parallel with Phase 30.**
4. Phase 32 (Middleware Chain, MCP Connectors, Circuit Breakers, Plugin SDK) provides 3-tier middleware chain (MS Agent Framework pattern), dynamic external service integration, circuit breakers (first in ecosystem), and plugin SDK.
5. Phase 33 (Skill Packs, Distribution & Capability Discovery) enables ecosystem growth with Agent Skills standard-compatible packs, cross-skill dependency resolution, and 4 ecosystem differentiation features.

## Task Mapping (Phase 29-33)

| Phase | Task ID | Owner | Dependencies | Outputs |
| --- | --- | --- | --- | --- |
| 29 | T31 | Runtime + Agent | Phase 18, 17 | Reasoning protocol (NextAction FSM), ISC system (GuardrailResult), constraint extraction, build drift prevention (5-scenario StuckDetector) |
| 30 | T32 | Runtime + Efficiency | Phase 29.1-29.2 | Effort classifier (heuristic-first), deterministic router, prompt templates, context priming, cost-aware model selection |
| 31 | T33 | Intelligence + Memory | Phase 29.1-29.2 | Signal capture (Langfuse schema), execution analyzer, learning extractor (SIMBA), steering rules |
| 32 | T34 | Extensibility + Integration | Phase 30, 31, 12, 16 | 3-tier middleware chain, MCP connector registry, circuit breakers, plugin SDK |
| 33 | T35 | Ecosystem + Distribution | Phase 32 | Agent Skills-compatible packs, distribution, versioning, capability discovery, marketplace |

### Parallelization Notes
- T32 and T33 can start in parallel once T31's deliverables 29.1-29.2 ship
- T34's middleware framework (32.1) and circuit breakers (32.7) can start as independent early work
- Critical path: T31 → T32/T33 (parallel) → T34 → T35 = 8-12 sessions

## Review Gates

### Phase 29 requires:
- Agent quality review (reasoning loop produces verifiable ISC artifacts)
- Regression review (existing agent tests still pass, no performance regression)
- Security review (constraint extraction doesn't leak tenant data)

### Phase 30 requires:
- Performance review (effort classification adds <100ms latency)
- Correctness review (deterministic routing matches expected solutions)
- Token budget review (prompt composition stays within model limits)

### Phase 31 requires:
- Privacy review (signal capture respects tenant data isolation)
- Quality review (learning extraction produces actionable proposals)
- Integration review (steering rules don't conflict with existing governance)

### Phase 32 requires:
- Security review (middleware can't bypass existing security layers; plugin SDK enforces capability grants)
- Performance review (blocking middleware meets <500ms budget; circuit breaker state transitions are O(1))
- Backward compatibility review (existing routes/agents work without middleware)
- Integration review (circuit breaker Redis state is tenant-isolated; MCP connector credentials stored in vault)

### Phase 33 requires:
- Security review (pack installation validates integrity)
- Isolation review (user/system separation is enforced)
- Compatibility review (pack dependency resolution handles conflicts)

## Estimated Effort

| Phase | New Files | New Tests | New Endpoints | Sessions | Notes |
|-------|-----------|-----------|---------------|----------|-------|
| 29 | 6-8 | 80-100 | 4-6 | 2-3 | Stage 29.1-29.2 as P0 |
| 30 | 6-8 | 70-90 | 4-6 | 2-3 | +cost-aware routing |
| 31 | 5-6 | 50-70 | 4-6 | 2 | Leverages Phase 16/20 infra |
| 32 | 9-12 | 90-110 | 8-10 | 3-4 | +circuit breakers + plugin SDK |
| 33 | 7-9 | 70-90 | 6-8 | 2-3 | +4 differentiation features |
| **Total** | **33-43** | **360-460** | **26-36** | **11-16** | |

Critical path with parallelization: **8-12 sessions** (down from 11-16 serial).

## Notes
- This plan is additive to `PHASE-21-24-WORKFLOW-PLAN.md`.
- Phases 23-24 and 25-28 may be completed in parallel with or before this chain depending on session priorities.
- Each phase should be implementable in 2-3 focused sessions.
- P0 items within each phase should be completed first to unblock downstream phases.
