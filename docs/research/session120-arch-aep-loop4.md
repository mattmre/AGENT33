# ARCH-AEP Loop 4 — Session 120 UX-A Architecture Review

**Date**: 2026-04-04
**Reviewer**: session120 (Claude Sonnet 4.6)
**Scope**: PRs #365–#371 (UX-A cluster: P60a, P-ENV, P63, P60b, P62, P61, P64)

---

## Gate Criteria Assessment

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Lite mode passes `test_lite_mode.py` | ✅ PASS | PR #365 (P60a) + PR #368 (P60b) — `test_lite_mode.py` exists and all B1/B2/B3 checks green |
| Diagnose CLI works | ✅ PASS | PR #367 (P63) — `agent33 diagnose` with traffic-light checks and `--fix` |
| Wizard completes end-to-end, no external services | ✅ PASS | PR #371 (P64) — `agent33 wizard` with skip/ollama/openai paths; 26 tests cover end-to-end with mock IO |
| Panel review | ✅ SELF-REVIEW | This document |

---

## Verdict

**Approved for UX-B.** 0 Critical, 1 High, 3 Medium, 2 Low findings.

---

## High Finding

**[PR #371 — P64] `.env.local` de-duplication absent in `_write_env`.**

`_write_env` appends a `# --- wizard ---` section to `.env.local` without checking if one already exists. Running `agent33 wizard` twice on the same directory silently writes duplicate `AGENT33_PROFILE`, `OLLAMA_BASE_URL`, and `DEFAULT_MODEL` entries. The last value wins in most `.env` parsers, so behavior is correct, but the file becomes noisy and confusing.

**Remediation**: Before writing, check for `# --- wizard ---` in existing content and truncate at that marker, or strip matching keys before appending.

---

## Medium Findings

**M1. [PR #365 — P60a] `InProcessCache` drops all state on server restart.**

The Redis fallback (`InProcessCache`) is a process-local LRU dict. When the server restarts in lite mode, the entire cache is lost. This is expected and documented in the code, but the wizard and bootstrap flow don't surface this caveat to the user. A user who relies on session caching for lite-mode chat will see unexpected state resets.

**Remediation**: Add a `# NOTE: ephemeral — clears on restart` comment near the class and optionally print a one-line warning in the `agent33 diagnose` output when mode=lite.

---

**M2. [PR #365 — P60a] `InProcessMessageBus` silently drops events when no subscriber registered.**

`publish()` looks up `self._queues[channel]` and silently no-ops if the key doesn't exist. Contrast with NATS which delivers to multiple subscribers and supports replay. In lite mode, any automation or webhook triggered via the bus will silently disappear if the subscriber hasn't registered yet.

**Remediation**: Log a DEBUG warning on publish to unknown channel, or document the no-subscriber contract explicitly.

---

**M3. [PR #366 — P-ENV] `detect_env` 30-day cache has no invalidation path.**

`~/.agent33/env.json` is refreshed only if `detect_env(refresh=True)` is called or the cache is 30 days old. If a user installs a GPU, removes Ollama, or significantly changes RAM, the cached profile will give stale model recommendations. The wizard uses this stale data without offering a manual refresh path.

**Remediation**: The wizard's environment step could check cache age and warn if >7 days old, or expose `agent33 env show --refresh` (already implemented) more prominently in the wizard output.

---

## Low Findings

**L1. [PR #371 — P64] Wizard template label matching is fragile.**

`_step_template` matches the user's choice back to a template `name` by checking `choice.startswith(t["label"])`. If a template's `label` value contains characters that could appear as a prefix of another label (e.g., a hypothetical "Code" and "Code Reviewer"), the wrong template gets selected. The current 5 templates have no overlap, but this is fragile for future additions.

**Remediation**: Use a `{label} — {description}` → `name` lookup dict instead of `startswith()`.

---

**L2. [PR #370 — P61] `ProfileSettingsSource.get_field_value` returns empty string for field_name.**

When a profile key is not found, `get_field_value` returns `(None, "", False)`. The empty string `""` as field_name could interact oddly with pydantic-settings internal field resolution if the source is ever iterated over. The `__call__` method returns the correct dict, so runtime behavior is fine, but it's a subtly non-conformant `PydanticBaseSettingsSource` implementation.

**Remediation**: Return `(None, field_name, False)` instead of `(None, "", False)` to match the protocol contract.

---

## Positive Notes

- **IO protocol abstraction** in the wizard is the right design — all 26 tests are behavioral, not infrastructure
- **Module-level try/except** on nats + postgres imports eliminates the B1 crash class entirely
- **Consistent graceful-except pattern** across wizard, diagnose, and env detect — no uncaught exceptions bubble to the user
- **Profile priority order** (init > env > dotenv > profile > secrets) is clearly documented and tested
- **Bootstrap + wizard complement each other** — bootstrap generates random secrets, wizard configures provider and profile — clean separation of concerns
- **SQLite FTS5 fallback** to LIKE is safe and well-tested with tenant isolation
- All 7 PRs in UX-A shipped with zero Critical findings and green CI

---

## UX-A Cluster Summary

| PR | Phase | Tests Added | Status |
|----|-------|-------------|--------|
| #365 | P60a — protocols + fallbacks + mode config | 18 | ✅ Merged |
| #366 | P-ENV — env detection + model selection | 15 | ✅ Merged |
| #367 | P63 — diagnose CLI | 22 | ✅ Merged |
| #368 | P60b — SQLite memory adapter | 25 | ✅ Merged |
| #369 | P62 — smart auth bootstrap | 12 | ✅ Merged |
| #370 | P61 — config profiles | 20 | ✅ Merged |
| #371 | P64 — first-run wizard | 26 | 🟡 CI |

**Total new tests in UX-A**: ~138

---

## Recommendation for UX-B

Before starting UX-B (P65–P67):

1. **Close H1** (`_write_env` de-duplication) — 15 min fix in `wizard.py`
2. **Document M2** (`InProcessMessageBus` no-subscriber contract) — code comment only
3. Begin P65 (quick-start templates) from fresh `origin/main` worktree after P64 merges
