# Sync Plan

## Ingest
- Source repos are scanned for `docs/`, agent folders, and agentic files (CLAUDE.md, AGENTS.md, etc.).
- Raw content is placed under `collected/<repo>/`.

## Normalize
- Identify duplicates and prefer the latest or most complete version.
- Promote canonical files into `core/` (planned).
- Record decisions in a future `core/CHANGELOG.md`.

## Distribute
- Update downstream repos from `core/` using a controlled copy process.
- Require PRs per repo with ARCH-AEP compliance.

## Governance
- All changes tracked in Git.
- Manifest updated per ingest.
