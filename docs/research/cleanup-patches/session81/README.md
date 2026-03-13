# Session 81 Cleanup Patch Archive

This repo-tracked subset preserves the four `.claude` prototype worktrees that
were intentionally kept as local history after the broader Session 81/82
cleanup resolved the remaining non-`.claude` holdouts.

## Contents

- `manifest.csv`: tabular index of each repo-tracked prototype holdout
- `manifest.json`: machine-readable index
- `export_holdout_patches.ps1`: repeatable export script used to build this archive
- `<slug>/status.txt`: branch, classification, subject, and git-status snapshot
- `<slug>/committed-vs-origin-main.patch`: committed branch delta relative to `origin/main`
- `<slug>/working-tree-tracked.patch`: tracked but uncommitted local changes
- `<slug>/working-tree-untracked.patch`: untracked files captured as patch additions

## Notes

- The broader cleanup analysis and resolution decisions are documented in:
  - `docs/research/session81-holdout-preservation-audit.md`
  - `docs/research/session82-remaining-holdout-resolution-audit.md`
- This archive is repo-local preservation only; it is meant to make the
  intentionally retained prototype history inspectable without reopening old
  implementation worktrees.
- The export script derives the current worktree root dynamically so reruns stay
  inside the active checkout instead of writing back to the shared root repo.
