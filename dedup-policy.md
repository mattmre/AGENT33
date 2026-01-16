# De-duplication Policy

## Priority Order
1) Most recent timestamp
2) Most complete (coverage of sections/templates)
3) Most widely referenced across repos

## Conflict Handling
- Preserve both in `collected/`
- Create a merged canonical version in `core/`
- Record rationale in `core/CHANGELOG.md` (planned)
