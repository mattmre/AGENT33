# Validation Snapshots (Session Evidence)

Use this as the shared source of truth for PR-1/PR-2/PR-3 merge gating.

| Validation group | Command (session) | Result |
|---|---|---:|
| Phase30/31/32 + tool-loop/invoke-iterative/skill/context | `cd engine && python -m pytest tests/test_phase30_effort_routing.py tests/test_phase31_learning_signals.py tests/test_phase32_connector_boundary.py tests/test_tool_loop.py tests/test_invoke_iterative.py tests/test_skill_matching.py tests/test_context_manager.py -q` | **213 passed, 1 skipped** |
| Messaging boundary + phase32 | `cd engine && python -m pytest tests/test_connector_boundary_messaging_adapters.py tests/test_phase32_connector_boundary.py -q` | **29 passed, 1 skipped** |
| LLM memory/performance + phase32 | `cd engine && python -m pytest tests/test_connector_boundary_llm_memory.py tests/test_performance_fixes.py tests/test_phase32_connector_boundary.py -q` | **40 passed, 1 skipped** |
| Multimodal adapters/api + phase32 | `cd engine && python -m pytest tests/test_connector_boundary_multimodal_adapters.py tests/test_multimodal_api.py tests/test_phase32_connector_boundary.py -q` | **33 passed, 1 skipped** |
| Chat + phase32 | `cd engine && python -m pytest tests/test_chat.py tests/test_phase32_connector_boundary.py -q` | **17 passed, 1 skipped** |
| Aggregate smoke-gate evidence | Session aggregate across command groups above | **332 passed, 5 skipped** |

## Notes
- Counts above are copied from in-session validation evidence and should be treated as merge gates.
- Do not replace these with inferred totals from unrelated full-suite runs.
