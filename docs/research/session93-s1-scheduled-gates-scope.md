# Session 93 Slice 1: Scheduled-Gates Hardening

Date: 2026-03-18
Branch: `fix/session93-s1-scheduled-gates-hardening`

## Problem

The recent S45 scheduled-gates feature landed with two real gaps:

1. malformed cron expressions were accepted during `create_schedule()` and only dropped later during APScheduler registration
2. the scheduled-gates route suite used fake bearer tokens and skipped 12 assertions when AuthMiddleware rejected them

Together, those issues meant the service could report schedule creation success for jobs that would never run, while the API tests gave false confidence about the route layer.

## Scope

Included:

- reject malformed cron expressions synchronously during schedule creation
- reuse the same cron parsing path during job registration
- convert scheduled-gates route tests to real JWT-backed requests
- remove auth-based skips and assert exact route outcomes

Excluded:

- scheduled-gates persistence or durability work
- threshold/evaluation logic changes
- E2E harness speed or network isolation
- component-security scaling follow-up

## Validation

- `python -m pytest engine/tests/test_scheduled_gates.py -q -rs --no-cov`
- `python -m ruff check engine/src/agent33/evaluation/scheduled_gates.py engine/src/agent33/api/routes/scheduled_gates.py engine/tests/test_scheduled_gates.py`
- `python -m mypy engine/src/agent33/evaluation/scheduled_gates.py engine/src/agent33/api/routes/scheduled_gates.py --config-file engine/pyproject.toml`

## Outcome

- malformed cron expressions now fail fast with `ValueError`
- API create now returns `422` for malformed cron input
- scheduled-gates route tests run with `0 skipped`
