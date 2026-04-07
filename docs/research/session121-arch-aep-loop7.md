# ARCH-AEP Loop 7 — Architecture Review
**Session 121/123 — April 2026**
**Reviewed against**: `origin/main` at commit `729d68f` (PR #383 — P72 Impact Dashboard)

## Verdict: PASS-WITH-CONDITIONS

## Summary
All UX-D cluster deliverables (P70, P71, P-PACK v2, P72) and ARCH-AEP Loop 6 remediations (PR #381) are present on `origin/main` and correctly wired into the lifespan. The review found two timing oracle vulnerabilities in SHA-256 comparisons using `!=` instead of `hmac.compare_digest()`. These are fixed in PR #385 (POST-1.4). No critical architectural gaps were found.

## Confirmed Correct on origin/main

| Subsystem | Status |
|---|---|
| AgentRuntime `pack_registry` parameter | PRESENT — `_inject_pack_addenda()` wired at lines 636, 845, 1129 |
| SpawnerService (`spawner/`) | PRESENT — wired in lifespan at `app.state.spawner_service` |
| KnowledgeIngestionService (`knowledge/`) | PRESENT — wired in lifespan at `app.state.knowledge_service` |
| OutcomesService + SQLite persistence | PRESENT — `OutcomePersistence` wired, `outcomes_db_path` in config |
| ToolGovernance `load_approved_tools_file()` | PRESENT — method exists at governance.py:98 |
| SSE `_record_outcome_safe()` | PRESENT — called in both invoke routes and stream route |
| PackSharingService | PRESENT — wired at `app.state.pack_sharing_service` |
| backup/restore_planner.py | No timing oracle — clean |

## Findings

### Conditions (must fix in POST-1.4 — both in same PR)

| ID | File | Line | Issue |
|---|---|---|---|
| C-01 | `engine/src/agent33/packs/loader.py` | 225 | `actual_hash != expected_hash` — direct hex string comparison. Must use `hmac.compare_digest()` |
| C-02 | `engine/src/agent33/security/approval_tokens.py` | 160 | `data.get("arg_hash") != expected_hash` — direct string comparison. Must use `hmac.compare_digest()` |

Both are timing oracle vulnerabilities. While the practical exploitability is low (C-01 is an integrity check, not an authentication bypass), they violate the project's security posture documented in CLAUDE.md anti-corner-cutting rules and MEMORY.md lesson #23.

### Low (notes, no action required)

| ID | Subsystem | Finding |
|---|---|---|
| L-01 | `packs/remote_marketplace.py` | SSRF: no private IP range blocking on registry URLs. Risk is operator-controlled (config-driven). Backlog for POST-3 supply chain review. |
| L-02 | `packs/registry.py` | Silent pack name collision: two packs with same bare skill name — second pack's alias silently dropped. No warning/error. Low priority. |
| L-03 | Pack provenance | Currently uses HMAC-SHA256 (symmetric). POST-3.2 will migrate to Sigstore cosign (keyless) per approved architectural decision. |

## What Was NOT Found (Falsely Reported in Initial Draft)

An initial draft of this review read the stale root checkout (commit `f092529`, Session 110) instead of `origin/main`. That draft incorrectly reported all UX-D features as missing. These reports are INVALID — all features are present on `origin/main`. The initial draft has been superseded by this corrected review.

## Remediation Status

- C-01 and C-02: Fixed in PR #385 (POST-1.4 — this same PR)
- All other confirmed-correct items: no action required
- L-01, L-02, L-03: Logged in backlog for POST-3 cluster

## Unblocks

This review clears the Loop 7 gate for:
- POST-1.5 (SkillsBench baseline)
- POST-2 cluster (SkillsBench competitiveness)
- POST-3 cluster (pack ecosystem)
- POST-4 cluster (P69b / P-PACK v3)
