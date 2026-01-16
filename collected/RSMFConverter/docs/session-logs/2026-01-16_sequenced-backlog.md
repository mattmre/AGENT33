# Sequenced Backlog: Phase 12-Ready Refinement Cycle

**Date**: 2026-01-16
**Source**: `docs/next session/next-session-narrative.md`, `docs/refinement-remediation/2026-01-15_tracker.md`
**Framework**: Agentic Orchestration (Planner, Repo Auditor, Test Engineer, Follow-up Engineer, QA/Reporter)

---

## Executive Summary

This document captures the final sequenced backlog extracted from all prior refinement cycles. It consolidates "Recommended Additional Tests" and "Priority Follow-ups" with acceptance criteria for implementation.

**Baseline State**:
- Tests at session start: 3,054 passing
- Branch: `feat/refinement-calendar-hardening-teams-tests`
- CRITICAL tier: 7/7 COMPLETE
- HIGH tier: 8/8 COMPLETE
- MEDIUM tier: 5/9 COMPLETE (4 deferred)
- LOW tier: 0/1 COMPLETE

**Final State**:
- Tests at session end: 3,105 passing (+51)
- LOW tier: 1/1 COMPLETE
- All actionable remediation items DONE

---

## Sequenced Backlog

### Tier 1: LOW Priority Items (COMPLETE)

| ID | Finding | Agent | Effort | Acceptance Criteria | Status |
|----|---------|-------|--------|---------------------|--------|
| L1 | Code duplication in ID generation | Architecture | S | 1. Create `parsers/id_utils.py` shared module<br>2. Migrate Teams, Slack, WhatsApp parsers<br>3. Add regression tests for ID consistency<br>4. All existing tests pass | **COMPLETE** |

### Tier 2: Deferred MEDIUM Items (Documented for Future)

| ID | Finding | Agent | Effort | Rationale for Deferral | Status |
|----|---------|-------|--------|------------------------|--------|
| M3 | Locale detection O(n*m) complexity | Performance | M | Low impact; optimization not urgent | DEFERRED |
| M4 | Teams HTML memory for large files | Performance | M | ZIP bomb protection addresses most risk | DEFERRED |
| M6 | Slack parser missing i18n integration | Architecture | M | Slack uses Unix epoch timestamps - no locale parsing needed | DEFERRED |
| M8 | WhatsApp user guide missing i18n docs | Documentation | M | Documentation, lower priority than code | DEFERRED |

### Tier 3: Recommended Additional Tests (From Prior Cycles)

| Source | Description | Status |
|--------|-------------|--------|
| T1-T4 | Teams edge cases (Unicode, long messages, malformed HTML, empty) | COMPLETE |
| T5-T8 | Teams i18n (Thai/Arabic-Indic/Buddhist/Persian) | COMPLETE |
| T9-T11 | Teams ZIP handling | COMPLETE |
| M7 | Bengali numeral + Hebrew calendar tests | COMPLETE |

---

## L1 Implementation Plan: ID Generation Refactoring

### Problem Statement

All three parsers duplicate identical MD5-based ID generation logic:
- `teams.py:1335-1392` (4 methods, ~57 lines)
- `slack.py:802-840` (3 methods, ~38 lines)
- `whatsapp.py:1330-1342, 1614-1625` (2 methods, ~24 lines)

**Total duplicated code**: ~119 lines across 9 methods

### Proposed Solution

Create `src/rsmfconverter/parsers/id_utils.py` with:

```python
IDType enum: PARTICIPANT, CONVERSATION, EVENT, ATTACHMENT
generate_id(*components, id_type, platform=None, hash_length=8)
generate_participant_id(identifier, platform=None)
generate_conversation_id(identifier, platform=None)
generate_event_id(*components, platform=None)
generate_attachment_id(identifier, platform=None)
```

### Migration Path

1. Create `id_utils.py` with shared functions
2. Add comprehensive tests in `test_id_utils.py`
3. Update parsers to import and use shared functions
4. Remove duplicated methods from parsers
5. Verify all existing tests pass

### Acceptance Criteria

- [ ] `id_utils.py` created with 5 functions + enum
- [ ] 20+ unit tests for ID generation
- [ ] Teams parser migrated (remove 4 methods)
- [ ] Slack parser migrated (remove 3 methods)
- [ ] WhatsApp parser migrated (remove 2 methods)
- [ ] All 3,054+ tests pass
- [ ] IDs generated are identical to previous implementation

---

## Deferred Items Analysis

### M6: Slack Parser i18n Integration

**Research Findings**:
- Slack timestamps are Unix epoch (e.g., `1705312200.123456`)
- No locale-dependent timestamp parsing required
- User content may have non-Western text, but doesn't affect parsing
- i18n integration would only benefit display name handling (very low priority)

**Recommendation**: Permanently DEFERRED. Not architecturally needed.

### M3: Locale Detection O(n*m) Complexity

**Current State**:
- `LocaleDetector.detect()` iterates over all patterns for all locales
- Theoretical worst case: O(n patterns × m locales)
- Practical impact: <10ms for typical inputs

**Recommendation**: DEFERRED. Optimize only if profiling shows bottleneck.

### M4: Teams HTML Memory for Large Files

**Current State**:
- Teams parser loads entire HTML into memory
- ZIP bomb protection (M2) mitigates most risk
- `max_per_file_size` default: 100 MB

**Recommendation**: DEFERRED. ZIP safety limits address practical concerns.

### M8: WhatsApp User Guide i18n Docs

**Current State**:
- CLI options `--source-locale`, `--source-timezone`, `--forensic` exist
- `docs/user-guide/I18N-CLI-OPTIONS.md` covers generic i18n
- WhatsApp-specific documentation would be incremental improvement

**Recommendation**: DEFERRED. Covered by generic i18n guide.

---

## Agent Orchestration Plan

### Phase 1: Planner (Complete)
- Extract and prioritize backlog items
- Define acceptance criteria
- Create sequenced backlog document

### Phase 2: Implementer - ID Utils Module
- Create `id_utils.py` with shared functions
- Ensure backward-compatible hash generation

### Phase 3: Test Engineer - ID Utils Tests
- Create `test_id_utils.py`
- Test all ID types and edge cases
- Test backward compatibility with existing IDs

### Phase 4: Refactorer - Parser Migration
- Update Teams parser to use `id_utils`
- Update Slack parser to use `id_utils`
- Update WhatsApp parser to use `id_utils`

### Phase 5: QA/Reporter
- Run full test suite
- Verify CI checks pass
- Update session log
- Update phase review deliverables

---

## Verification Checkpoints

- [x] L1 implemented with regression tests (51 tests)
- [x] All deferred items documented with rationale
- [x] Full test suite passes (3,105 tests)
- [x] No regressions introduced
- [x] Session log updated with results
- [x] Next-session-narrative updated

---

*Generated by agentic orchestration workflow*
*Session: 2026-01-16*
*Status: ALL ITEMS COMPLETE*
