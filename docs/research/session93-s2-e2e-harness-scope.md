# Session 93 Slice 2: E2E Harness Hardening

Date: 2026-03-18
Branch: `fix/session93-s2-e2e-harness-hardening`

## Problem

The E2E harness defined a deterministic embedding helper but never wired it into app lifespan initialization. The suite therefore built the real embedding stack on every test app startup, while tenant fixtures also opened nested `TestClient` instances on the same app. The result was an unnecessarily slow suite for a mocked E2E harness.

## Findings

1. `_deterministic_embed()` existed in `engine/tests/e2e/conftest.py` but the `e2e_app` fixture only patched long-term memory, NATS, and Redis.
2. App lifespan still initialized the real `EmbeddingProvider`, `EmbeddingCache`, `HybridSearcher`, `RAGPipeline`, and `ProgressiveRecall`.
3. Hook-chain E2E tests use the real runtime and therefore traverse progressive recall before the mocked LLM call.
4. `LongTermMemory` in the harness did not provide explicit `store()` and `search()` behavior, so recall/storage paths relied on incomplete mocks.
5. `tenant_a_client` and `tenant_b_client` each opened another `TestClient`, multiplying lifespan setup cost inside multi-tenant tests.

## Changes

1. Patched the E2E harness to replace `agent33.memory.embeddings.EmbeddingProvider` with a deterministic mock during app lifespan.
2. Completed the E2E `LongTermMemory` mock with explicit `store()` and `search()` async behavior.
3. Replaced nested authenticated `TestClient` fixtures with lightweight auth-header proxy wrappers over the shared base client.
4. Added a harness request-path test that asserts a real agent invoke request awaits the deterministic embedder through progressive recall.
5. Added an auth-proxy regression test proving lowercase `authorization` overrides replace fixture auth instead of appending a second bearer token.

## Validation

Baseline before the slice on clean branch:

- `python -m pytest engine/tests/e2e/ -q --no-cov` -> `25 passed` in `196.67s`

After the slice:

- `python -m pytest engine/tests/e2e/ -q --no-cov --durations=15` -> `26 passed` in `154.89s`
- `python -m pytest engine/tests/e2e/ -q --no-cov --durations=10` -> `26 passed` in `155.17s`
- review-follow-up validation: `python -m pytest engine/tests/e2e/ -q --no-cov --durations=10` -> `27 passed` in `161.58s`
- `python -m ruff check engine/tests/e2e/conftest.py engine/tests/e2e/test_agent_tool_memory_flow.py`
- `python -m ruff format --check engine/tests/e2e/conftest.py engine/tests/e2e/test_agent_tool_memory_flow.py`
- `python -m ruff check engine/tests/e2e/conftest.py engine/tests/e2e/test_agent_tool_memory_flow.py engine/tests/e2e/test_multi_tenant_isolation.py`
- `python -m ruff format --check engine/tests/e2e/conftest.py engine/tests/e2e/test_agent_tool_memory_flow.py engine/tests/e2e/test_multi_tenant_isolation.py`

Observed improvement:

- End-to-end runtime improved by about `41.5s` versus the reproduced clean-branch baseline.
- The worst multi-tenant setup spikes dropped from roughly `16-18s` to roughly `6-7s`.

## Scope Boundary

This slice hardens the E2E harness only. It does not change production embedding behavior, provider transport, or runtime semantics outside tests.
