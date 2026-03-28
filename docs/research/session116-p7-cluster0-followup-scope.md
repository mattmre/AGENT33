# Session 116 P7 Scope Lock

## Slice

- `P7 / Cluster 0 follow-up remediation`
- Source cycle: `AEP-20260328-1`

## In Scope

- Fix operator verification token guidance so the read-only flow and bounded reset
  flow use the correct scopes and do not imply one token can do both.
- Make ingestion-artifact `planning_refs` unambiguously repository-root-relative.
- Clarify in the repo-ingestor skill that the ingestion template path is
  repository-root-relative.
- Add focused regression coverage for the updated guidance and path contract.

## Out of Scope

- Any new operator or backup routes
- Any process-registry behavioral changes
- Any generic artifact registry or ticketing workflow
- Any Cluster A work

## Expected Write Set

- `docs/operators/operator-verification-runbook.md`
- `engine/tests/test_operator_verification_runbooks_docs.py`
- `engine/src/agent33/improvement/ingestion_artifacts.py`
- `engine/tests/test_ingestion_artifacts.py`
- `docs/research/templates/INGESTION_TASK_TEMPLATE.md`
- `docs/research/codex-autorunner-ingestion-task-2026-03-28.md`
- `engine/packs/platform-builder/skills/research/repo-ingestor/SKILL.md`

## Verification Plan

- `pytest engine/tests/test_operator_verification_runbooks_docs.py engine/tests/test_ingestion_artifacts.py engine/tests/test_repo_ingestion.py -q --no-cov`
- `ruff check engine/src/agent33/improvement/ingestion_artifacts.py engine/tests/test_operator_verification_runbooks_docs.py engine/tests/test_ingestion_artifacts.py engine/tests/test_repo_ingestion.py`
- `ruff format --check engine/src/agent33/improvement/ingestion_artifacts.py engine/tests/test_operator_verification_runbooks_docs.py engine/tests/test_ingestion_artifacts.py engine/tests/test_repo_ingestion.py`
- `mypy engine/src/agent33/improvement/ingestion_artifacts.py --config-file engine/pyproject.toml`
- `git diff --check`
