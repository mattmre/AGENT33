# Sync Plan

## Ingest
- Source repos are scanned for `docs/`, agent folders, and agentic files (CLAUDE.md, AGENTS.md, etc.).
- Raw content is placed under `collected/<repo>/`.
- **Immutability**: Once ingested, collected/ artifacts are never modified.

## Normalize
- Identify duplicates and prefer the latest or most complete version.
- Promote canonical files into `core/` with `derived-from` relationship links.
- Record decisions in `core/CHANGELOG.md`.
- When updating, create new version with `supersedes` relationship to old.

## Relationship Tracking
- All canonicalization creates relationship links (see `dedup-policy.md`).
- Provenance chain maintained: collected → core → distributed.
- Relationships documented in CHANGELOG entries.

## Distribute
- Update downstream repos from `core/` using a controlled copy process.
- Require PRs per repo with ARCH-AEP compliance.
- Track distribution with relationship links back to core artifacts.

## Governance
- All changes tracked in Git.
- Manifest updated per ingest.
- Relationship integrity verified during sync.
