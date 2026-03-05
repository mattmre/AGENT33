# Session 54 Delta: Modular Retrieval Diagnostics

## Goal
Refactor retrieval execution into explicit pipeline stages and expose retrieval diagnostics without breaking existing RAG query contracts.

## Implementation Summary
- Extended `engine/src/agent33/memory/rag.py` with modular diagnostics models:
  - `RetrievalStageDiagnostic`
  - `RetrievalDiagnostics`
  - `RAGQueryWithDiagnostics`
- Added `RAGPipeline.query_with_diagnostics(text)`:
  - returns the existing `RAGResult` plus per-stage timing/count diagnostics
  - records pipeline totals and retrieval method (`vector` or `hybrid`)
- Kept `RAGPipeline.query(text)` behavior stable:
  - still returns `RAGResult` and now delegates to `query_with_diagnostics`
- Staged vector pipeline diagnostics:
  - `vector-search`
  - `threshold-filter`
  - `source-map`
  - `prompt-assembly`
- Staged hybrid pipeline diagnostics:
  - `hybrid-search`
  - `source-map`
  - `prompt-assembly`
- Added regression tests in `engine/tests/test_hybrid_rag.py` for both vector/hybrid diagnostics paths.

## Validation
- `python -m ruff format src/agent33/memory/rag.py tests/test_hybrid_rag.py`
- `python -m ruff check src/agent33/memory/rag.py tests/test_hybrid_rag.py`
- `python -m mypy src/agent33/memory/rag.py --config-file pyproject.toml`
- `PYTHONPATH=src python -m pytest tests/test_hybrid_rag.py -q --no-cov`

## Next
- Surface diagnostics in operator-facing APIs/workflow telemetry where needed without changing default response payloads.
