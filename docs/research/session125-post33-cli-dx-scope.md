# Session 125 — POST-3.3 CLI DX Scope

## Date

2026-04-11

## Goal

Implement POST-3.3 as a focused CLI usability slice for the pack ecosystem:

1. add explicit `--json` and `--plain` output modes to the pack-management commands that currently mix human text with ad hoc JSON dumps
2. make `agent33 diagnose` pack-aware so operators can detect obvious pack-configuration and signing-readiness issues before attempting registry workflows

## Current Baseline

- `agent33 packs` already supports:
  - `validate`
  - `apply`
  - `list`
  - `search`
  - `install`
  - `update`
  - `publish`
  - `revocation-status`
- Output is inconsistent:
  - some commands print friendly prose (`list`, `search`, `install`)
  - some commands dump raw JSON only in one branch (`apply --dry-run`)
  - there is no shared output-mode contract for scripts
- `agent33 diagnose` currently checks Python/env/disk/port/Ollama/LLM/database/Redis only.
- The runtime already has enough pack configuration to support pack-aware diagnostics:
  - `Settings.pack_definitions_dir`
  - `Settings.pack_marketplace_dir`
  - `Settings.pack_marketplace_remote_sources`
  - `PackHubConfig.local_cache_path`
  - optional Sigstore verification in `agent33.packs.provenance`

## Included Work

1. Add output-mode handling for pack CLI commands:
   - `--json` for structured machine-readable output
   - `--plain` for stable minimal text output without extra prose
   - reject conflicting `--json` + `--plain`
2. Apply the output-mode contract to the existing pack commands without changing their underlying API behavior.
3. Extend `agent33 diagnose` with local pack checks that do not require a running server:
   - pack definitions directory presence / manifest count
   - marketplace remote-source JSON validity
   - pack hub cache presence/readiness signal
   - Sigstore package availability/readiness signal for pack signing flows
4. Add regression coverage for the new CLI output modes and diagnose pack checks.

## Non-Goals

1. New pack registry or marketplace APIs
2. Changes to pack install/update business logic
3. Seed-pack creation (POST-3.4)
4. Pack marketplace UI
5. Server-side operator diagnostics redesign
6. Full CLI-wide global output formatting across unrelated commands

## Candidate Files

- `engine/src/agent33/cli/packs.py`
- `engine/src/agent33/cli/diagnose.py`
- `engine/src/agent33/cli/main.py`
- `engine/tests/test_ppack_v1.py`
- `engine/tests/test_ppack_v2.py`
- `engine/tests/test_diagnose.py`

## Validation Plan

- `pytest engine/tests/test_ppack_v1.py engine/tests/test_ppack_v2.py engine/tests/test_diagnose.py -q --no-cov`
- `ruff check engine/src/agent33/cli/packs.py engine/src/agent33/cli/diagnose.py engine/src/agent33/cli/main.py engine/tests/test_ppack_v1.py engine/tests/test_ppack_v2.py engine/tests/test_diagnose.py`
- `ruff format --check engine/src/agent33/cli/packs.py engine/src/agent33/cli/diagnose.py engine/src/agent33/cli/main.py engine/tests/test_ppack_v1.py engine/tests/test_ppack_v2.py engine/tests/test_diagnose.py`
- `mypy engine/src/agent33/cli/packs.py engine/src/agent33/cli/diagnose.py engine/src/agent33/cli/main.py --config-file engine/pyproject.toml`

## Notes

- Keep the default human-readable output behavior intact unless a command already emits JSON in a narrow branch.
- Prefer small shared helpers over duplicating output-mode branching in every command.
- Diagnose should remain local and side-effect free except for the existing `--fix` flow.
