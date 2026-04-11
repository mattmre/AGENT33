# Session 126 — POST-3.4 Seed Packs Scope

## Date

2026-04-11

## Goal

Create 5 installable seed packs under `engine/packs/` to seed the AGENT-33 pack ecosystem.

## PACK.yaml Schema Fields

The `PackManifest` Pydantic model (`engine/src/agent33/packs/manifest.py`) enforces:

### Required Fields

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | Lowercase letters, digits, hyphens; 1-64 chars; must start/end with letter or digit |
| `version` | string | Semver: `MAJOR.MINOR.PATCH` |
| `description` | string | Non-empty; max 500 chars |
| `author` | string | Non-empty |
| `skills` | list[PackSkillEntry] | At least 1 entry required |

### PackSkillEntry Fields

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | Non-empty; max 64 chars |
| `path` | string | Relative path to skill directory/file; non-empty |
| `description` | string | Optional; default `""` |
| `required` | bool | Optional; default `true` |

### Optional Fields

| Field | Type | Notes |
|-------|------|-------|
| `schema_version` | string | Must be `"1"` if provided |
| `license` | string | e.g. `"Apache-2.0"` |
| `tags` | list[string] | Classification tags |
| `category` | string | Category slug |
| `prompt_addenda` | list[string] | Injection-scanned; appended to agent system prompt |
| `tool_config` | dict[str, dict] | Per-tool overrides; injection-scanned |

### Injection Scanning

Both `prompt_addenda` and `tool_config` are scanned by `agent33.security.injection.scan_inputs_recursive()` during PACK.yaml validation. The `validate_pack` CLI command runs this scan before accepting a pack.

## Skill Frontmatter Format

Skills are directories containing a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: skill-slug
version: 1.0.0
description: Short description of what this skill does.
allowed_tools:
  - tool_name
tags:
  - tag1
---

# Skill Title

Markdown body becomes the `instructions` field.
```

The loader (`engine/src/agent33/skills/loader.py`) parses frontmatter via `parse_frontmatter()` and maps it to `SkillDefinition`. The body becomes `instructions`. The `allowed_tools` frontmatter key maps to `allowed_tools` on `SkillDefinition`.

Note: The SKILL.md frontmatter uses `allowed_tools` (not `tools`). The existing `planning-with-files` skill uses `allowed-tools` with hyphens (Anthropic-format); the Pydantic model field is `allowed_tools` with underscore — both are accepted because Pydantic model aliases resolve during `model_validate`.

## Skill Path Convention

In `PACK.yaml`, `path` is the relative path from the pack directory root to the skill directory. Example:

```yaml
skills:
  - name: search-web
    path: skills/search-web
    description: Search the web for information
```

This means `engine/packs/web-research/skills/search-web/SKILL.md` must exist.

## 5 Packs to Create

1. `web-research` — `skills/search-web`, `skills/summarize-results`, `skills/extract-facts`
2. `code-review` — `skills/review-diff`, `skills/check-security`, `skills/suggest-improvements`
3. `meeting-notes` — `skills/extract-action-items`, `skills/summarize-transcript`, `skills/identify-decisions`
4. `document-summarizer` — `skills/chunk-and-summarize`, `skills/extract-key-points`, `skills/generate-abstract`
5. `developer-assistant` — `skills/run-tests`, `skills/lint-code`, `skills/git-workflow`, `skills/explain-error`

## Non-Goals

1. No server-side API changes
2. No registry upload or publishing
3. No pack signing / Sigstore integration (POST-3.5+)
4. No marketplace UI
5. No changes to the pack install/update business logic
6. No changes to `PackManifest` or `SkillDefinition` models
7. No changes to CLI commands (POST-3.3 already added `--json`/`--plain` output modes)

## Validation Plan

From `engine/` in the worktree:
```bash
PYTHONPATH=src python -m pytest tests/test_seed_packs.py -q --no-cov
python -m ruff check src/ tests/test_seed_packs.py
python -m ruff format --check tests/test_seed_packs.py
python -m mypy src --config-file pyproject.toml
```

All 5 packs must pass `agent33 packs validate <pack_path>` via the real CLI.
