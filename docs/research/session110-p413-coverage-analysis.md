# P4.13 Coverage Push Analysis (Session 110)

## Goal
Push test coverage from ~85.8% to 90% (~2,300-2,500 additional covered lines).

## Priority 1 Targets (0 tests, high testability)

| Rank | Module | Lines | Est. Tests |
|------|--------|-------|------------|
| 1 | tools/tldr_enforcer.py | 189 | 8-10 |
| 2 | services/graph_generator.py | 199 | 6-8 |
| 3 | config_apply.py | 221 | 10-12 |
| 4 | automation/dead_letter.py | 147 | 6-8 |
| 5 | workflows/actions/http_request.py | 177 | 8-10 |
| 6 | automation/filters.py | 157 | 5-7 |
| 7 | workflows/actions/handoff.py | 71 | 4-5 |
| 8 | workflows/migration.py | 171 | 5-7 |
| 9 | config_schema.py | 177 | 4-6 |
| 10 | cli/main.py | 259 | 6-8 |

## Priority 2 Targets (partial coverage, high-impact gaps)
- agents/effort.py (533 lines)
- memory/context_compressor.py (563 lines)

## Estimated: 62-81 new tests for Priority 1, 15-20 for Priority 2
