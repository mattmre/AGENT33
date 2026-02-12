# De-duplication Policy

## Priority Order
1) Most recent timestamp
2) Most complete (coverage of sections/templates)
3) Most widely referenced across repos

## Immutability Principle
- **`collected/` is immutable**: Raw ingests are never modified after initial capture.
- All refinements create new artifacts in `core/` with `supersedes` relationships.
- Provenance chain: collected → core → distributed repos.

## Conflict Handling
- Preserve both in `collected/`
- Create a merged canonical version in `core/`
- Record rationale in `core/CHANGELOG.md`
- Add `supersedes` relationship link when replacing artifacts

## Relationship Types
When canonicalizing, document relationships:
- `derived-from`: canonical artifact → source in collected/
- `supersedes`: new version → deprecated version
- See `core/orchestrator/RELATIONSHIP_TYPES.md` for full taxonomy

## Relationships

| Type | Target | Notes |
|------|--------|-------|
| depends-on | `core/orchestrator/RELATIONSHIP_TYPES.md` | Relationship taxonomy |
| explains | . | Immutability and provenance rules for the canonicalization workflow |
| contextualizes | `sync-plan.md` | Related sync policies |
