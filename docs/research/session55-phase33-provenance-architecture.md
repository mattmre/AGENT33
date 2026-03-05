# Pack Signing, Provenance Verification & Conflict Resolution Architecture

**Date**: 2026-03-07
**Status**: Implemented
**Session**: 55
**Phase**: 33 (Skill Packs & Distribution — Hardening)
**Depends On**: Phase 33 core pack system (registry, loader, manifest, versioning, adapter, API)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Provenance Model](#3-provenance-model)
4. [Signing & Verification Flow](#4-signing--verification-flow)
5. [Trust Policy Engine](#5-trust-policy-engine)
6. [Version Conflict Detection](#6-version-conflict-detection)
7. [Conflict Resolution Strategies](#7-conflict-resolution-strategies)
8. [Registry Integration](#8-registry-integration)
9. [Security Considerations](#9-security-considerations)
10. [File Plan](#10-file-plan)
11. [Test Coverage](#11-test-coverage)
12. [Future Work](#12-future-work)

---

## 1. Executive Summary

Phase 33's core pack system (merged in sessions 50-54) provides pack manifests, semver dependency resolution, a registry, loader, adapter, and API routes. Two gaps remained:

1. **Trust & Provenance** — No mechanism to verify that a pack was produced by a trusted entity and hasn't been tampered with post-signing.
2. **Version Conflict Resolution** — The dependency resolver detects version conflicts for *dependencies*, but there was no facility to detect *pack-to-pack* conflicts (overlapping skill names, incompatible shared dependency ranges) or to apply resolution strategies.

This session closes both gaps with minimal new code, no external crypto dependencies, and full backward compatibility.

---

## 2. Problem Statement

### 2.1 Provenance

When packs can be installed from local directories (and eventually a marketplace), the engine needs to answer:

- **Authenticity**: Was this pack actually produced by the claimed author?
- **Integrity**: Has the manifest been modified since signing?
- **Trust Level**: Does this pack meet the deployment's minimum trust requirements?
- **Signer Authorization**: Is the signer on the approved list?

### 2.2 Version Conflicts

When multiple packs are installed simultaneously:

- **Skill Name Collisions**: Two packs may declare a skill with the same name, causing ambiguous resolution in the SkillRegistry.
- **Dependency Range Incompatibilities**: Two packs may depend on the same third pack but with non-overlapping version constraints, making it impossible to install both.

---

## 3. Provenance Model

### PackProvenance (Pydantic BaseModel)

| Field         | Type        | Default     | Description                              |
|---------------|-------------|-------------|------------------------------------------|
| `signer_id`   | `str`       | (required)  | Identity of the signing entity           |
| `signature`   | `str`       | (required)  | Hex-encoded HMAC-SHA256 digest           |
| `signed_at`   | `datetime`  | `now(UTC)`  | Timestamp of signing                     |
| `algorithm`   | `str`       | `"sha256"`  | Hash algorithm (extensible)              |
| `trust_level` | `TrustLevel`| `COMMUNITY` | Provenance trust classification          |

### TrustLevel (StrEnum)

Ordered from lowest to highest trust:

```
UNTRUSTED → COMMUNITY → VERIFIED → OFFICIAL
```

---

## 4. Signing & Verification Flow

### Signing (`sign_pack`)

1. Serialize the `PackManifest` to **canonical JSON** (sorted keys, no whitespace).
2. Compute `HMAC-SHA256(signing_key, canonical_json)`.
3. Return a `PackProvenance` with the hex digest, signer identity, timestamp, and trust level.

### Verification (`verify_pack`)

1. Re-serialize the manifest to canonical JSON (same deterministic process).
2. Compute `HMAC-SHA256(verification_key, canonical_json)`.
3. Compare against the stored signature using `hmac.compare_digest` (constant-time).
4. Return `True` / `False`.

### Design Decisions

- **HMAC-SHA256 over asymmetric signatures**: For the initial implementation, HMAC with shared secrets is sufficient. It's stdlib-only (`hmac` + `hashlib`), zero external dependencies. Asymmetric signing (Ed25519 via PyNaCl, already a dependency) can be added as an alternative algorithm later.
- **Canonical JSON serialization**: Using `json.dumps(data, sort_keys=True, separators=(",", ":"))` ensures the same manifest always produces the same byte sequence regardless of field ordering.
- **Constant-time comparison**: `hmac.compare_digest` prevents timing attacks.

---

## 5. Trust Policy Engine

### PackTrustPolicy (Pydantic BaseModel)

| Field              | Type          | Default      | Description                                        |
|--------------------|---------------|--------------|----------------------------------------------------|
| `require_signature`| `bool`        | `False`      | Reject unsigned packs when `True`                  |
| `min_trust_level`  | `TrustLevel`  | `UNTRUSTED`  | Minimum trust level for accepted packs             |
| `allowed_signers`  | `list[str]`   | `[]`         | If non-empty, only these signer IDs are accepted   |

### Evaluation Logic (`evaluate_trust`)

```
if provenance is None:
    if policy.require_signature → REJECT
    else → ALLOW (no restriction)

if policy.allowed_signers and signer not in list → REJECT
if provenance.trust_level < policy.min_trust_level → REJECT

→ ALLOW
```

---

## 6. Version Conflict Detection

### `detect_conflicts(pack_a, pack_b) -> list[VersionConflict]`

Two categories of conflicts are detected:

1. **Skill Name Overlap** (`ConflictKind.SKILL_NAME_OVERLAP`): Both packs declare a skill with the same `name`. This would cause ambiguous bare-name resolution in SkillRegistry.

2. **Version Range Incompatibility** (`ConflictKind.VERSION_RANGE_INCOMPATIBLE`): Both packs depend on the same third pack, but their version constraints have no overlapping satisfying versions.

### Overlap Detection Algorithm

For dependency range overlap, a brute-force probe tests versions `{0..20}.{0..20}.{0..5}` against both constraints. This pragmatic approach avoids implementing full interval intersection for the constraint syntax we support (^, ~, >=, <, etc.). The probe space covers 2,646 version points which is fast (<1ms) and sufficient for real-world semver constraints.

---

## 7. Conflict Resolution Strategies

### `resolve_conflicts(conflicts, strategy, versions) -> list[Resolution]`

| Strategy   | Behavior                                                       |
|------------|----------------------------------------------------------------|
| `"latest"` | Prefer the pack with the higher semver version                 |
| `"manual"` | Mark all conflicts as requiring human intervention             |
| `"reject"` | Reject all conflicts outright (strictest policy)               |

The `"latest"` strategy requires a `versions` dict mapping pack names to version strings. If a version is missing, it falls back to `"manual"`.

---

## 8. Registry Integration

The `PackRegistry.install()` method now accepts optional provenance parameters:

```python
def install(
    self,
    source: PackSource,
    *,
    provenance: PackProvenance | None = None,
    verification_key: str = "",
) -> InstallResult:
```

The install flow is:

1. Validate directory structure
2. **Evaluate trust policy** — check provenance against `self._trust_policy`
3. **Verify signature** — if provenance and key are provided, verify HMAC
4. Load and validate manifest
5. Load skills into SkillRegistry
6. Register as installed

The `PackRegistry.__init__` now accepts an optional `trust_policy` parameter:

```python
PackRegistry(packs_dir, skill_registry, trust_policy=PackTrustPolicy(...))
```

Default policy (`PackTrustPolicy()`) allows everything, preserving backward compatibility.

---

## 9. Security Considerations

| Concern                | Mitigation                                                    |
|------------------------|---------------------------------------------------------------|
| Timing attacks         | `hmac.compare_digest` for constant-time comparison            |
| Key management         | Keys are passed as parameters, not stored in code             |
| Algorithm agility      | `algorithm` field enables future migration to Ed25519         |
| Downgrade attacks      | `require_signature` policy prevents bypassing provenance      |
| Canonical form attacks | Deterministic JSON serialization prevents re-ordering exploits|

### Limitations (Acknowledged)

- HMAC requires shared secrets — not suitable for public marketplace trust without infrastructure for key distribution. Future work will add Ed25519 asymmetric signatures.
- No certificate chain / delegation model yet.
- Provenance metadata is not yet persisted alongside the installed pack on disk.

---

## 10. File Plan

| File                                          | Action   | Description                                 |
|-----------------------------------------------|----------|---------------------------------------------|
| `engine/src/agent33/packs/provenance.py`      | Created  | Signing, verification, trust policy engine   |
| `engine/src/agent33/packs/conflicts.py`       | Created  | Conflict detection and resolution            |
| `engine/src/agent33/packs/registry.py`        | Modified | Wire provenance into install flow            |
| `engine/src/agent33/packs/__init__.py`         | Modified | Export new public API symbols                |
| `engine/tests/test_pack_provenance.py`        | Created  | 30+ tests for provenance and conflicts       |
| `docs/research/session55-phase33-provenance-architecture.md` | Created | This document |

---

## 11. Test Coverage

### Provenance Tests (TestPackSigning)
- Sign returns valid provenance with correct fields
- Custom trust level propagation
- Sign + verify round-trip succeeds
- Wrong key fails verification
- Tampered manifest version fails verification
- Tampered description fails verification
- Unsupported algorithm rejects
- Deterministic signing (same input → same output)

### Trust Policy Tests (TestTrustPolicy)
- No provenance + no requirement → allowed
- No provenance + signature required → rejected
- Provenance meets policy → allowed
- Trust level too low → rejected
- Signer not in allowlist → rejected
- Signer in allowlist → allowed
- Empty allowlist → any signer accepted
- Trust level ordering verified across all 4 levels

### Conflict Detection Tests (TestConflictDetection)
- No overlaps → no conflicts
- Single skill name overlap detected
- Multiple skill overlaps detected
- Compatible shared dependency (overlapping ranges)
- Incompatible shared dependency (non-overlapping ranges)
- Disjoint dependency sets → no conflicts

### Conflict Resolution Tests (TestConflictResolution)
- Reject strategy marks all as rejected
- Manual strategy marks all as manual
- Latest strategy picks higher version
- Equal versions → prefer pack A (stable)
- Missing version → fall back to manual
- Unknown strategy raises ValueError
- Empty conflict list → empty resolution list

---

## 12. Future Work

1. **Asymmetric Signing (Ed25519)**: Use PyNaCl (already a project dependency) for public-key signatures suitable for marketplace distribution.
2. **Provenance Persistence**: Store provenance metadata alongside installed pack on disk (e.g., `PROVENANCE.json` file).
3. **Conflict Resolution UI**: Surface detected conflicts in the frontend pack management UI.
4. **Automatic Conflict Detection on Install**: Run `detect_conflicts` against all currently installed packs when a new pack is installed.
5. **Certificate Chain / Delegation**: Support signing delegation (org signs a CI key, CI key signs packs).
6. **Revocation Lists**: Allow revoking compromised signer IDs.
