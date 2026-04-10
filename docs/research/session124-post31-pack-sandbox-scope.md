# Session 124 — POST-3.1 Pack Sandbox Scope

## Date

2026-04-10

## Goal

Implement POST-3.1 as a focused security-hardening slice for the pack ecosystem: reuse the existing CLIAdapter sandbox, close the remaining pack-manifest injection gaps, and add explicit regression coverage for the pack attack surface.

## Current Baseline

- `CLIAdapter` subprocess isolation already exists and remains the sandbox mechanism.
- `load_pack_skills()` already blocks skill-path traversal.
- `verify_checksums()` already blocks checksum path traversal and uses `hmac.compare_digest()`.
- `RemotePackMarketplace._safe_extract()` already blocks zip-slip and symlink entries.
- `PackManifest` already scans `prompt_addenda` for prompt injection patterns.
- The remaining gap is that `tool_config` values are not scanned, and encoded payload detection only covers Base64.

## Included Work

1. Extend `agent33.security.injection` to detect encoded prompt-injection payloads beyond Base64:
   - Unicode escape sequences such as `\\u0069\\u0067...`
   - hex-encoded payloads that decode to prompt-injection strings
2. Extend `PackManifest` validation so `tool_config` values go through the same recursive injection scanner as `prompt_addenda`.
3. Add regression coverage for the six POST-3.1 attack categories:
   - system prompt override
   - delimiter injection
   - instruction override
   - encoded/obfuscated payload
   - path traversal / filesystem escape
   - manifest supply-chain injection via `tool_config`

## Non-Goals

1. New sandbox runtime infrastructure
2. Sigstore signing or revocation support (POST-3.2)
3. CLI UX improvements (POST-3.3)
4. Seed-pack creation (POST-3.4)
5. Pack marketplace UI or operator audit UX

## Candidate Files

- `engine/src/agent33/security/injection.py`
- `engine/src/agent33/packs/manifest.py`
- `engine/tests/test_security_hardening.py`
- `engine/tests/test_ppack_v1.py`
- `engine/tests/test_pack_loader.py`
- `engine/tests/test_remote_marketplace.py`

## Validation Plan

- `pytest engine/tests/test_security_hardening.py engine/tests/test_ppack_v1.py engine/tests/test_pack_loader.py engine/tests/test_remote_marketplace.py -q --no-cov`
- `ruff check engine/src/agent33/security/injection.py engine/src/agent33/packs/manifest.py engine/tests/test_security_hardening.py engine/tests/test_ppack_v1.py engine/tests/test_pack_loader.py engine/tests/test_remote_marketplace.py`
- `ruff format --check engine/src/agent33/security/injection.py engine/src/agent33/packs/manifest.py engine/tests/test_security_hardening.py engine/tests/test_ppack_v1.py engine/tests/test_pack_loader.py engine/tests/test_remote_marketplace.py`
- `mypy engine/src/agent33/security/injection.py engine/src/agent33/packs/manifest.py --config-file engine/pyproject.toml`
