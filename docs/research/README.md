# AGENT 33 External Repo Intake Pack

**Snapshot date:** 2026-01-16

## Contents

- `agent33-repo-intake-feature-matrix-narrative.md` — repo-ready narrative/runbook for pulling repos, analyzing, and producing artifacts.
- `repo_dossiers/` — one dossier per repo, aligned to the narrative template.
- `master_feature_matrix.md` / `master_feature_matrix.csv` — condensed cross-repo comparison.
- `templates/` — dossier and matrix schema templates.
- `agentic-orchestration-trends-2025H2.md` — prior research memo (6-month trends).
- `agentic-github-repos-5kplus-2026-01-16.md` — repo shortlist used for intake.

## How to use in AGENT 33

1. Copy `agent33-repo-intake-feature-matrix-narrative.md` into `core/orchestrator/` (or link from `core/ORCHESTRATION_INDEX.md`).
2. Commit `repo_dossiers/` into `docs/research/intake/<DATE>/` or `collected/` (immutable raw intake) depending on your policy.
3. Promote reusable patterns into `core/` with decisions logged in `core/CHANGELOG.md`.

## Notes on evidence

The dossiers are based on publicly available documentation pages and READMEs referenced in each dossier’s evidence section. For full fidelity, your intake pipeline should clone each repo and extract additional evidence directly from code, configs, and tests.
