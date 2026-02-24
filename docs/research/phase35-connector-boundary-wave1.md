# Phase 35 Connector Boundary — Wave 1 Decisions (2026-02-24)

## Scope

This note records architecture and rollout decisions for the fresh-agent orchestration wave that prepared three implementation branches for connector-boundary adoption in Phase 35:

1. **LLM + embeddings boundary path**
2. **Multimodal boundary path**
3. **Chat proxy boundary path**

## Branches and Commits

- `feat/phase35-boundary-llm-embeddings` @ `ef1a509`
- `feat/phase35-boundary-multimodal` @ `c2a2024`
- `feat/phase35-boundary-chat-proxy` @ `ad850c1`

## Architecture Decisions

### 1) Keep boundary execution centralized by connector family

- All new outbound model-facing paths should flow through connector boundary governance instead of embedding policy/retry/timeout logic in route or adapter code.
- This preserves one reliability and policy model across LLM, embeddings, multimodal, and chat-adjacent execution surfaces.

### 2) Connector naming contract for Phase 35

- Naming stays explicit and surface-scoped so policy packs and telemetry can target each connector family independently.
- Wave 1 follows the split:
  - **LLM/embeddings connector boundary** (text + vector generation paths)
  - **Multimodal connector boundary** (image/file-aware inference paths)
  - **Chat proxy connector boundary** (chat route execution bridge)
- This naming avoids ambiguous “generic model connector” labels and keeps governance intents readable during reviews.

### 3) Why multimodal used the sync governance helper

- Multimodal adapters include call sites that remain synchronous in the current stack and cannot safely await async governance plumbing without broader refactors.
- Using the sync governance helper for this wave:
  - keeps policy enforcement consistent with boundary rules,
  - avoids event-loop bridging risks in adapter paths,
  - minimizes blast radius while preserving deterministic behavior.
- Async-first convergence can happen in a later cleanup wave once multimodal call sites are fully async-compatible.

### 4) Rollout order decision

Wave 1 sequencing is intentionally staged:

1. **LLM/embeddings first**  
   Highest traffic model path; validates baseline boundary behavior where coverage is strongest.
2. **Multimodal second**  
   Adds mixed sync/async adapter constraints after baseline behavior is stable.
3. **Chat proxy third**  
   Final chat-facing integration after core model paths are boundary-governed.

This order reduces integration risk and makes regressions easier to localize by connector family.

## Validation Snapshot (Targeted)

- **PR A / LLM-embeddings branch**
  - `test_connector_boundary_llm_memory.py`: **2 passed**
  - `test_performance_fixes.py`: **25 passed**
  - `test_phase32_connector_boundary.py`: **13 passed, 1 skipped**

- **PR B / multimodal branch**
  - `test_connector_boundary_multimodal_adapters.py`: **4 passed**
  - `test_multimodal_api.py`: **16 passed**
  - `test_phase32_connector_boundary.py`: **13 passed, 1 skipped**

- **PR C / chat proxy branch**
  - `test_chat.py`: **4 passed**
  - `test_phase32_connector_boundary.py`: **13 passed, 1 skipped**

## Follow-up

- Open review packets for each Phase 35 branch with explicit merge sequencing labels.
- Re-run targeted suites post-merge in the same A → B → C order.
- Track async convergence opportunities for multimodal governance helper usage in a subsequent wave.
