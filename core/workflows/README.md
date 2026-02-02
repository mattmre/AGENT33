# Workflows Canon

- Canonical workflow assets live directly under `core/workflows/`.
- Archived variants from source repos live in `core/workflows/sources/`.

## Canonical Files
- `workflows/ci.yml` (baseline CI template)
- `workflows/dotnet-build.yml` (.NET CI template)
- `dependabot.yml` (baseline dependabot config)
- `PULL_REQUEST_TEMPLATE.md`
- `ISSUE_TEMPLATE/bug_report.md`
- `ISSUE_TEMPLATE/feature_request.md`
- `instructions/csharp.instructions.md`
- `instructions/python.instructions.md`

## Notes
- Source repo workflow packs may be highly project-specific; merge selectively into canonical as needed.
- Promotion criteria: see `core/workflows/PROMOTION_CRITERIA.md`.
- Source index: see `core/workflows/SOURCES_INDEX.md`.
