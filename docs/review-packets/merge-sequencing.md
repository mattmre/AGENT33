# Merge Sequencing and Gates (Priorities 12–14)

## Required Merge Order
1. **PR-1**: `pr-1-phase32-adoption.md`
2. **PR-2**: `pr-2-persistence-hardening.md`
3. **PR-3**: `pr-3-observability-integration.md`

## Per-PR Gates

### Gate for PR-1 (Phase 32 Adoption)
- Connector tests: **11 passed**
- Connector regression group: **92 passed**
- Baseline targeted tests: **187 passed**

### Gate for PR-2 (Persistence Hardening)
- Persistence tests (`test_phase31_learning_signals`): **14 passed**
- Baseline targeted tests: **187 passed**

### Gate for PR-3 (Observability Integration)
- Observability tests (phase30 + integration): **38 passed**
- Phase30 routing suite: **15 passed**
- Baseline targeted tests: **187 passed**

## Global Rule
- If any gate fails, stop sequence and fix forward before proceeding to the next PR.
- Validation reference: `docs/review-packets/validation-snapshots.md`.

## Phase 35 Boundary-Touching Requirement

- For any PR that touches Phase 35 connector-boundary behavior (messaging, multimodal, llm/embeddings, chat, or shared boundary governance), run and record all five smoke groups from `validation-snapshots.md` before merge:
  1. Phase30/31/32 + tool-loop/invoke-iterative/skill/context
  2. Messaging boundary + phase32
  3. LLM memory/performance + phase32
  4. Multimodal adapters/api + phase32
  5. Chat + phase32
- Preserve the currently validated aggregate baseline (**361 passed, 5 skipped**) unless new evidence supersedes it.

## Label Policy (CI-Enforced)
- Use exactly one sequencing label per PR: `sequence:1`, `sequence:2`, or `sequence:3`.
- PRs without a sequencing label are treated as unsequenced and pass the sequencing guard.
- For sequenced PRs, ordering is enforced on the same base branch:
  - `sequence:1`: no predecessor required.
  - `sequence:2`: requires an already merged `sequence:1` PR.
  - `sequence:3`: requires an already merged `sequence:2` PR.
