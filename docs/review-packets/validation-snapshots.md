# Validation Snapshots (Session Evidence)

Use this as the shared source of truth for PR-1/PR-2/PR-3 merge gating.

| Validation group | Command (session) | Result |
|---|---|---:|
| Baseline targeted tests | `cd engine && python -m pytest <targeted regression set> -q` | **187 passed** |
| Connector tests | `cd engine && python -m pytest tests/test_phase32_connector_boundary.py -q` | **11 passed** |
| Connector regression group | `cd engine && python -m pytest <connector regression group> -q` | **92 passed** |
| Persistence tests | `cd engine && python -m pytest tests/test_phase31_learning_signals.py -q` | **14 passed** |
| Observability tests (phase30 + integration) | `cd engine && python -m pytest tests/test_phase30_effort_routing.py tests/test_integration_wiring.py -q` | **38 passed** |
| Phase30 routing suite | `cd engine && python -m pytest tests/test_phase30_effort_routing.py -q` | **15 passed** |

## Notes
- Counts above are copied from in-session validation evidence and should be treated as merge gates.
- Do not replace these with inferred totals from unrelated full-suite runs.
